"""Release boundaries: public configuration, trusted provenance, immutable rollback."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('deployment_release', ROOT / 'scripts/deployment/release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


def inputs(environment='staging'):
    project = 'mcp-website-dev-39539' if environment == 'staging' else 'mcp-website-2a1ad'
    return dict(GITHUB_REPOSITORY='Vittorix99/mcp-website', GITHUB_REPOSITORY_ID='899139661',
        GITHUB_REF='refs/heads/main', GITHUB_EVENT_NAME='push', GITHUB_SHA='a' * 40,
        GITHUB_WORKFLOW_REF='Vittorix99/mcp-website/.github/workflows/release.yml@refs/heads/main',
        WIF_PROVIDER='projects/123456789/locations/global/workloadIdentityPools/github/providers/release',
        DEPLOY_SERVICE_ACCOUNT=f'github-deploy@{project}.iam.gserviceaccount.com',
        BUILD_SERVICE_ACCOUNT=f'functions-build@{project}.iam.gserviceaccount.com',
        RUNTIME_SERVICE_ACCOUNT=f'app-runtime@{project}.iam.gserviceaccount.com',
        WEB_RUNTIME_SERVICE_ACCOUNT=f'web-runtime@{project}.iam.gserviceaccount.com',
        FIREBASE_API_KEY='public-web-api-key', FIREBASE_APP_ID='1:123456789:web:abc',
        PAYPAL_CLIENT_ID='public-client-id', MAILERSEND_FROM_EMAIL='hello@example.com',
        MAILERSEND_FROM_NAME='MCP', MAIL_ALLOWED_RECIPIENTS='test@example.com,admin@example.com',
        SOUNDCLOUD_CLIENT_ID='public-soundcloud-id')


@pytest.mark.parametrize('environment', ['staging', 'production'])
def test_public_configuration_is_explicit_and_stamped(environment):
    manifest = release.prepare(environment, inputs(environment))
    assert manifest['sha'] == 'a' * 40
    assert manifest['backend']['MCP_CONFIG_DIGEST'] == manifest['digest']
    assert manifest['frontend']['NEXT_PUBLIC_CONFIGURATION_DIGEST'] == manifest['digest']
    assert manifest['backend']['MCP_RUNTIME_SERVICE_ACCOUNT'].startswith('app-runtime@')
    assert all('SECRET' not in key and not key.endswith('API_KEY') for key in manifest['backend'])
    assert manifest['backend']['MAIL_MODE'] == ('staging' if environment == 'staging' else 'live')
    assert release.prepare(environment, dict(reversed(list(inputs(environment).items())))) == manifest


@pytest.mark.parametrize(('key', 'value'), [
    ('GITHUB_EVENT_NAME', 'pull_request'), ('GITHUB_EVENT_NAME', 'workflow_run'),
    ('GITHUB_REF', 'refs/heads/other'), ('GITHUB_REPOSITORY', 'attacker/mcp-website'),
    ('GITHUB_REPOSITORY_ID', '1'), ('GITHUB_SHA', 'latest'),
    ('GITHUB_WORKFLOW_REF', 'Vittorix99/mcp-website/.github/workflows/pr.yml@refs/heads/main'),
    ('DEPLOY_SERVICE_ACCOUNT', 'deploy@wrong.iam.gserviceaccount.com'),
    ('RUNTIME_SERVICE_ACCOUNT', 'app-runtime@wrong.iam.gserviceaccount.com'),
    ('WIF_PROVIDER', 'arbitrary'), ('FIREBASE_APP_ID', ''),
    ('PAYPAL_CLIENT_SECRET', 'DO-NOT-PRINT'), ('FIREBASE_TOKEN', 'DO-NOT-PRINT'),
    ('NEXT_PUBLIC_CUSTOM_SECRET', 'DO-NOT-PRINT'),
    ('PAYPAL_CLIENT_ID', 'MCP\nSECRET=DO-NOT-PRINT'),
])
def test_rejects_unsafe_release_inputs_without_echoing_values(key, value):
    with pytest.raises(ValueError) as error:
        release.prepare('staging', {**inputs(), key: value})
    if value:
        assert value not in str(error.value)


def test_production_cannot_reuse_staging_identities():
    with pytest.raises(ValueError):
        release.prepare('production', inputs())


def test_build_identity_is_explicit_separate_and_bound_into_the_digest():
    manifest = release.prepare('staging', inputs())
    assert manifest['identities']['BUILD_SERVICE_ACCOUNT'] == inputs()['BUILD_SERVICE_ACCOUNT']
    changed = release.prepare('staging', {**inputs(),
        'BUILD_SERVICE_ACCOUNT':'another-build@mcp-website-dev-39539.iam.gserviceaccount.com'})
    assert changed['digest'] != manifest['digest']
    for value in ['', inputs()['RUNTIME_SERVICE_ACCOUNT'],
                  'build@mcp-website-2a1ad.iam.gserviceaccount.com',
                  '1005755179074-compute@developer.gserviceaccount.com']:
        with pytest.raises(ValueError):
            release.prepare('staging', {**inputs(), 'BUILD_SERVICE_ACCOUNT':value})


def test_public_configuration_can_be_shared_without_forging_github_identity():
    public = {key:value for key,value in inputs().items() if not key.startswith('GITHUB_')}
    manifest = release.public_configuration('staging', public, 'a' * 40)
    assert manifest == release.prepare('staging', inputs())
    with pytest.raises(ValueError, match='repository identity'):
        release.prepare('staging', public)
    with pytest.raises(ValueError):
        release.public_configuration('staging', public, 'main')


def test_reusable_job_receives_the_environment_build_identity():
    import yaml
    workflow = yaml.safe_load((ROOT / '.github/workflows/deploy-environment.yml').read_text())
    assert workflow['jobs']['release']['env']['BUILD_SERVICE_ACCOUNT'] == '${{ vars.BUILD_SERVICE_ACCOUNT }}'


def test_rollback_artifact_requires_this_repository_main_release_workflow():
    run = dict(repository={'full_name':'Vittorix99/mcp-website', 'id':899139661},
        path='.github/workflows/release.yml', head_branch='main', head_sha='b' * 40,
        event='push', status='completed', conclusion='failure', run_attempt=1)
    release.validate_snapshot_run(run)
    for update in [dict(path='.github/workflows/pr.yml'), dict(head_branch='feature'),
                   dict(event='pull_request'), dict(status='in_progress'), dict(run_attempt=2)]:
        with pytest.raises(ValueError):
            release.validate_snapshot_run({**run, **update})


def test_smoke_rejects_wrong_release_even_with_http_success():
    manifest = release.prepare('staging', inputs())
    health = dict(status='ok', environment='staging', project_id=manifest['project'],
        release_sha=manifest['sha'], configuration_digest=manifest['digest'])
    release.validate_health(health, manifest)
    for key in ['environment', 'project_id', 'release_sha', 'configuration_digest', 'status']:
        with pytest.raises(ValueError):
            release.validate_health({**health, key:'wrong'}, manifest)


def test_production_environment_requires_real_reviewer_and_main_only_policy():
    protected = dict(can_admins_bypass=False, protection_rules=[dict(type='required_reviewers',prevent_self_review=False,
        reviewers=[dict(type='User',reviewer={'id':123})])],
        deployment_branch_policy=dict(protected_branches=False,custom_branch_policies=True))
    release.validate_environment('production', protected, [{'name':'main','type':'branch'}])
    for invalid in [{}, {**protected, 'protection_rules':[]},
                    {**protected, 'can_admins_bypass':True}]:
        with pytest.raises(ValueError):
            release.validate_environment('production', invalid, [{'name':'main','type':'branch'}])
    with pytest.raises(ValueError):
        release.validate_environment('production', protected, [{'name':'*','type':'branch'}])


def snapshot(manifest):
    return dict(schema=1, environment=manifest['environment'], project=manifest['project'],
        sha=manifest['sha'], digest=manifest['digest'],
        hosting_version=f"sites/{manifest['project']}/versions/previous-version",
        services={'public-api':{'traffic':{'public-api-00001-abc':100}}},
        functions=['deployment_health'], secrets=[])


def test_rollback_rejects_cross_environment_or_unresolved_latest_revision():
    manifest = release.prepare('staging', inputs())
    previous = snapshot(manifest)
    release.validate_snapshot(previous, manifest)
    for update in [dict(project='mcp-website-2a1ad'), dict(environment='production'),
        dict(hosting_version='sites/other/versions/v1'), dict(services={}),
        dict(services={'public-api':{'traffic':{'LATEST':100}}}),
        dict(services={'public-api':{'traffic':{'public-api-00001-abc':50}}})]:
        with pytest.raises(ValueError):
            release.validate_snapshot({**previous, **update}, manifest)


@pytest.mark.parametrize('version', ['latest', '', '0', 'disabled'])
def test_rollback_refuses_secret_aliases_before_restoring_traffic(monkeypatch, version):
    manifest = release.prepare('staging', inputs())
    revision = 'public-api-00001-abc'
    monkeypatch.setattr(release, 'gcloud', lambda *args: json.dumps(dict(metadata={'name':revision},
        spec={'containers':[{'env':[{'valueFrom':{'secretKeyRef':{'name':'mail-key', 'key':version}}}]}]})))
    with pytest.raises(ValueError, match='numeric secret versions'):
        release.verify_revision_secrets(manifest, revision)


def test_rollback_validates_every_revision_before_first_mutation(monkeypatch):
    monkeypatch.setattr(release, 'verify_topology', lambda _: None)
    manifest = release.prepare('staging', inputs())
    previous = snapshot(manifest)
    previous['services']['ssr-site'] = {'traffic':{'ssr-site-00001-abc':100}}
    records = [dict(name='projects/p/locations/us-central1/functions/deployment_health',
        labels={'firebase-functions-codebase':'python_codebase'},
        serviceConfig={'service':'projects/p/locations/us-central1/services/public-api'}),
        dict(name='projects/p/locations/us-central1/functions/ssrsite',
        labels={'firebase-functions-codebase':'firebase-frameworks-' + manifest['project']},
        serviceConfig={'service':'projects/p/locations/us-central1/services/ssr-site'})]
    monkeypatch.setattr(release, 'cloud_functions', lambda _: records)
    checked = []
    def validate_revision(_, revision):
        checked.append(revision)
        if revision.startswith('ssr'):
            raise ValueError('Unavailable revision')
        return set()
    monkeypatch.setattr(release, 'verify_revision_secrets', validate_revision)
    monkeypatch.setattr(release, 'gcloud', lambda *args: pytest.fail('Mutation before validating all targets'))
    monkeypatch.setattr(release, 'hosting', lambda *args, **kwargs: pytest.fail('Premature Hosting release'))
    with pytest.raises(ValueError, match='Unavailable revision'):
        release.rollback(previous, manifest)
    assert len(checked) == 2


def test_rollback_restores_backend_ssr_hosting_then_checks_identity(monkeypatch):
    monkeypatch.setattr(release, 'verify_topology', lambda _: None)
    manifest = release.prepare('staging', inputs())
    previous = snapshot(manifest)
    previous['services']['ssr-site'] = {'traffic':{'ssr-site-00001-abc':100}}
    records = [dict(name='deployment_health', labels={'firebase-functions-codebase':'python_codebase'},
        serviceConfig={'service':'public-api'}),
        dict(name='ssrsite', labels={'firebase-functions-codebase':'firebase-frameworks-' + manifest['project']},
        serviceConfig={'service':'ssr-site'})]
    monkeypatch.setattr(release, 'cloud_functions', lambda _: records)
    monkeypatch.setattr(release, 'verify_revision_secrets', lambda *args: set())
    calls = []
    monkeypatch.setattr(release, 'gcloud', lambda _, *args: calls.append(args))
    monkeypatch.setattr(release, 'hosting', lambda _, *args, **kwargs: calls.append(('hosting', kwargs['version'])))
    monkeypatch.setattr(release, 'service_state', lambda _, service: previous['services'][service])
    monkeypatch.setattr(release, 'smoke', lambda old: calls.append(('health', old['sha'])))
    release.rollback(previous, manifest)
    assert calls[0][:3] == ('run', 'services', 'update-traffic')
    assert calls[1][:3] == ('run', 'services', 'update-traffic')
    assert calls[2] == ('hosting', previous['hosting_version'])
    assert calls[3] == ('health', previous['sha'])


def test_read_only_preflight_checks_metadata_and_per_secret_runtime_access(monkeypatch):
    manifest = release.prepare('staging', inputs())
    calls = []
    def cloud(_, *args):
        calls.append(args)
        if args[:2] == ('projects','describe'):
            return manifest['project']
        if args[:3] == ('storage','buckets','describe'):
            return manifest['backend']['STORAGE_BUCKET']
        if args[:2] == ('services','list'):
            return '\n'.join(name + '.googleapis.com' for name in ['cloudfunctions', 'cloudbuild', 'run',
                'artifactregistry', 'secretmanager', 'firebasehosting', 'eventarc', 'pubsub',
                'firestore', 'storage', 'identitytoolkit', 'cloudscheduler'])
        if args[:3] == ('iam','service-accounts','describe'):
            return args[3]
        if args[:3] == ('secrets','versions','describe'):
            return 'ENABLED'
        if args[:2] == ('secrets','get-iam-policy'):
            return json.dumps({'bindings':[{'role':'roles/secretmanager.secretAccessor',
                'members':['serviceAccount:' + manifest['identities']['RUNTIME_SERVICE_ACCOUNT']]}]})
        pytest.fail('Unexpected cloud operation')
    monkeypatch.setattr(release, 'gcloud', cloud)
    release.cloud_preflight(manifest)
    assert all('access' not in call and 'set-iam-policy' not in call and 'enable' not in call for call in calls)


def test_pipeline_does_not_grant_cloud_identity_to_verification_or_prs():
    import yaml
    # PyYAML YAML 1.1 parses the GitHub key "on" as True; account for this in assertions.
    pipeline = yaml.safe_load((ROOT / '.github/workflows/release.yml').read_text())
    jobs = pipeline['jobs']
    assert jobs['verify']['permissions'] == {'contents':'read'}
    assert jobs['production']['needs'] == 'staging'
    assert "needs.staging.result == 'success'" in jobs['production']['if']
    assert pipeline['concurrency']['cancel-in-progress'] is False
    pr = yaml.safe_load((ROOT / '.github/workflows/pr.yml').read_text())
    assert 'workflow_call' in pr.get('on', pr.get(True))
    assert 'id-token' not in pr['permissions']
    assert not any('secrets' in job for job in jobs.values())


def test_preparation_writes_only_explicit_public_configuration(tmp_path, monkeypatch):
    manifest = release.prepare('staging', inputs())
    (tmp_path / 'mcp-backend/functions').mkdir(parents=True)
    (tmp_path / 'mcp-website').mkdir()
    for directory in [tmp_path / 'mcp-backend/functions', tmp_path / 'mcp-website']:
        (directory / '.env.example').write_text('# Tracked inert template, never loaded\n')
    (tmp_path / 'firebase.json').write_text((ROOT / 'firebase.json').read_text())
    monkeypatch.setattr(release, 'ROOT', tmp_path)
    release.write_configuration(manifest)
    config = json.loads((tmp_path / 'firebase.release.generated.json').read_text())
    assert config['hosting']['frameworksBackend']['serviceAccount'] == manifest['identities']['WEB_RUNTIME_SERVICE_ACCOUNT']
    data = (tmp_path / 'mcp-backend/functions' / ('.env.' + manifest['project'])).read_text()
    assert 'MCP_RELEASE_SHA=' in data
    assert 'PAYPAL_CLIENT_SECRET=' not in data
    assert 'GOOGLE_APPLICATION_CREDENTIALS=' not in data
    assert json.loads((tmp_path / '.local/release/config.json').read_text()) == manifest


def test_preparation_refuses_developer_dotenv_without_opening_it(tmp_path, monkeypatch):
    manifest = release.prepare('staging', inputs())
    (tmp_path / '.env.local').write_text('PRIVATE_SENTINEL_DO_NOT_COPY')
    monkeypatch.setattr(release, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='existing dotenv files'):
        release.write_configuration(manifest)
    assert not (tmp_path / '.local/release/config.json').exists()


def test_topology_change_requires_controlled_baseline(monkeypatch):
    calls = []
    def execute(args):
        calls.append(args)
        return 'mcp-backend/functions/triggers/jobs_trigger.py\n' if args[1] == 'diff' else ''
    monkeypatch.setattr(release, 'command', execute)
    with pytest.raises(ValueError, match='topology changed'):
        release.verify_topology('a' * 40)
    assert calls[0][:3] == ['git','merge-base','--is-ancestor']


def test_disabled_previous_secret_version_blocks_rollback_before_traffic(monkeypatch):
    manifest = release.prepare('staging', inputs())
    previous = snapshot(manifest)
    previous['secrets'] = [{'secret':'PAYPAL_CLIENT_SECRET', 'version':'7'}]
    monkeypatch.setattr(release, 'verify_topology', lambda _: None)
    calls = []
    monkeypatch.setattr(release, 'gcloud', lambda _, *args: calls.append(args) or 'DISABLED')
    with pytest.raises(ValueError, match='previous secret version'):
        release.rollback(previous, manifest)
    assert len(calls) == 1
    assert calls[0][:3] == ('secrets','versions','describe')


def test_release_verifies_active_revisions_after_a_rollback_not_latest_function_metadata(monkeypatch):
    manifest = release.prepare('staging', inputs())
    revision = 'public-api-00001-abc'
    monkeypatch.setattr(release, 'cloud_functions', lambda _, **kwargs:[dict(
        name='deployment_health', labels={'firebase-functions-codebase':'python_codebase'},
        serviceConfig={'service':'public-api', 'environmentVariables':{'MCP_RELEASE_SHA':'b' * 40}})])
    monkeypatch.setattr(release, 'service_state', lambda *args, **kwargs:{'traffic':{revision:100}})
    response = dict(metadata={'name':revision}, spec={'containers':[{'env':[
        {'name':'MCP_RELEASE_SHA','value':manifest['sha']},
        {'name':'MCP_CONFIG_DIGEST','value':manifest['digest']},
        {'name':'PAYPAL_CLIENT_SECRET','valueFrom':{'secretKeyRef':{'key':'7'}}}]}]})
    monkeypatch.setattr(release, 'gcloud', lambda *args:json.dumps(response))
    release.verify_function_releases(manifest)
    response['spec']['containers'][0]['env'][0]['value'] = 'b' * 40
    with pytest.raises(ValueError, match='active backend revisions'):
        release.verify_function_releases(manifest)


def test_snapshot_collects_secret_versions_of_saved_revisions_after_rollback(monkeypatch):
    manifest = release.prepare('staging', inputs())
    healthy = dict(status='ok',environment=manifest['environment'],project_id=manifest['project'],
        release_sha=manifest['sha'],configuration_digest=manifest['digest'])
    monkeypatch.setattr(release, 'fetch_json', lambda _: healthy)
    monkeypatch.setattr(release, 'smoke', lambda _: None)
    monkeypatch.setattr(release, 'verify_topology', lambda _: None)
    monkeypatch.setattr(release, 'verify_function_releases', lambda _: None)
    records = [dict(name='deployment_health',labels={'firebase-functions-codebase':'python_codebase'},
        serviceConfig={'service':'public-api', 'secretEnvironmentVariables':[{'secret':'PAYPAL_CLIENT_SECRET','version':'8'}]}),
        dict(name='ssrsite',labels={'firebase-functions-codebase':'firebase-frameworks-' + manifest['project']},
        serviceConfig={'service':'ssr-site'})]
    monkeypatch.setattr(release, 'cloud_functions', lambda _:records)
    monkeypatch.setattr(release, 'expected_functions', lambda *args:['deployment_health'])
    monkeypatch.setattr(release, 'service_state', lambda _, service:{'traffic':{service+'-00001-abc':100}})
    monkeypatch.setattr(release, 'verify_revision_secrets', lambda _, revision:
        {('PAYPAL_CLIENT_SECRET','7')} if revision.startswith('public-api') else set())
    monkeypatch.setattr(release, 'hosting', lambda *args:{'releases':[{'type':'DEPLOY',
        'version':{'name':f"sites/{manifest['project']}/versions/previous-version"}}]})
    checked = []
    monkeypatch.setattr(release, 'verify_secret_versions', lambda snapshot, _:checked.extend(snapshot['secrets']))
    result = release.snapshot_release(manifest, {})
    assert result['secrets'] == checked == [{'secret':'PAYPAL_CLIENT_SECRET','version':'7'}]


def test_active_revision_alias_is_resolved_to_same_project_numeric_secret(monkeypatch):
    manifest = release.prepare('staging', inputs())
    revision = 'public-api-00001-abc'
    data = dict(metadata={'name':revision, 'annotations':{'run.googleapis.com/secrets':
        'provider-key:projects/123456789/secrets/PAYPAL_CLIENT_SECRET'}},spec={'containers':[{'env':[
        {'valueFrom':{'secretKeyRef':{'name':'provider-key','key':'7'}}}]}]})
    monkeypatch.setattr(release, 'gcloud', lambda _, *args:'123456789' if args[0]=='projects' else json.dumps(data))
    assert release.verify_revision_secrets(manifest, revision) == {('PAYPAL_CLIENT_SECRET','7')}
    data['metadata']['annotations']['run.googleapis.com/secrets'] = 'provider-key:projects/foreign/secrets/PAYPAL_CLIENT_SECRET'
    with pytest.raises(ValueError, match='same-project'):
        release.verify_revision_secrets(manifest, revision)


def test_staging_release_uses_real_providers_and_fake_wallet_without_changing_production():
    manifest = release.prepare('staging', inputs())
    backend = manifest['backend']
    assert {key: backend[key] for key in ['PAYPAL_MODE', 'MAIL_MODE', 'PASS2U_MODE',
        'GENDER_MODE', 'SOUNDCLOUD_MODE']} == dict(PAYPAL_MODE='sandbox', MAIL_MODE='staging',
        PASS2U_MODE='fake', GENDER_MODE='staging', SOUNDCLOUD_MODE='staging')
    assert backend['MAILERSEND_FROM_EMAIL'] == 'hello@example.com'
    assert backend['MAIL_ALLOWED_RECIPIENTS'] == 'test@example.com,admin@example.com'
    assert backend['SOUNDCLOUD_CLIENT_ID'] == 'public-soundcloud-id'
    changed = release.prepare('staging', {**inputs(), 'MAIL_ALLOWED_RECIPIENTS':'other@example.com'})
    assert changed['digest'] != manifest['digest']
    production = release.prepare('production', inputs('production'))
    assert production['backend']['PASS2U_MODE'] == 'live'
    assert 'MAIL_ALLOWED_RECIPIENTS' not in production['backend']


@pytest.mark.parametrize('recipients', ['', '@example.com', '*', 'a@example.com,',
    'valid@example.com,not-an-address', 'a@example.com;other@example.com'])
def test_release_rejects_missing_or_broad_staging_recipients(recipients):
    with pytest.raises(ValueError, match='MAIL_ALLOWED_RECIPIENTS'):
        release.prepare('staging', {**inputs(), 'MAIL_ALLOWED_RECIPIENTS':recipients})


def test_release_preflight_requires_every_active_provider_secret_and_never_wallet(monkeypatch):
    manifest = release.prepare('staging', inputs())
    requested = []
    def cloud(_, *args):
        if args[:2] == ('projects', 'describe'): return manifest['project']
        if args[:3] == ('storage', 'buckets', 'describe'): return manifest['backend']['STORAGE_BUCKET']
        if args[:2] == ('services', 'list'):
            return '\n'.join(name + '.googleapis.com' for name in ['cloudfunctions', 'cloudbuild', 'run',
                'artifactregistry', 'secretmanager', 'firebasehosting', 'eventarc', 'pubsub',
                'firestore', 'storage', 'identitytoolkit', 'cloudscheduler'])
        if args[:3] == ('iam', 'service-accounts', 'describe'): return args[3]
        if args[:3] == ('secrets', 'versions', 'describe'):
            requested.append(args[args.index('--secret') + 1])
            return 'ENABLED'
        if args[:2] == ('secrets', 'get-iam-policy'):
            return json.dumps({'bindings':[{'role':'roles/secretmanager.secretAccessor',
                'members':['serviceAccount:' + manifest['identities']['RUNTIME_SERVICE_ACCOUNT']]}]})
        pytest.fail('Unexpected cloud operation')
    release.cloud_preflight(manifest, cloud=cloud)
    assert set(requested) == {'PAYPAL_CLIENT_SECRET', 'MAILERSEND_API_KEY',
        'SOUNDCLOUD_CLIENT_SECRET', 'GENDER_API_KEY'}
    def missing_mail(_, *args):
        if args[:3] == ('secrets', 'versions', 'describe') and 'MAILERSEND_API_KEY' in args:
            return 'DISABLED'
        return cloud(_, *args)
    with pytest.raises(ValueError, match='enabled provider secret version'):
        release.cloud_preflight(manifest, cloud=missing_mail)


def test_release_profile_loads_runtime_and_binds_only_needed_provider_secrets():
    import os
    import subprocess
    import sys
    manifest = release.prepare('staging', inputs())
    env = {key:os.environ[key] for key in ['PATH', 'HOME', 'TMPDIR'] if key in os.environ}
    env.update(manifest['backend'])
    env.update(PAYPAL_CLIENT_SECRET='synthetic-paypal', MAILERSEND_API_KEY='synthetic-mail',
        SOUNDCLOUD_CLIENT_SECRET='synthetic-radio', GENDER_API_KEY='synthetic-gender')
    code = """import json
from config.runtime_settings import get_runtime_settings
from config.function_secrets import secrets_for_function
s=get_runtime_settings()
assert s.providers.pass2u.value=='fake'
assert s.providers.mail_allowed_recipients==('test@example.com','admin@example.com')
print(json.dumps({name:[secret.name for secret in secrets_for_function(name)]
for name in ['capture_order_event','create_wallet_pass','on_membership_created',
'admin_create_radio_episode','deployment_health']}))
"""
    result = subprocess.run([sys.executable, '-c', code], env=env,
        cwd=ROOT/'mcp-backend/functions', capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        'capture_order_event':['PAYPAL_CLIENT_SECRET', 'MAILERSEND_API_KEY'],
        'create_wallet_pass':[], 'on_membership_created':['GENDER_API_KEY', 'MAILERSEND_API_KEY'],
        'admin_create_radio_episode':['SOUNDCLOUD_CLIENT_SECRET'], 'deployment_health':[]}
