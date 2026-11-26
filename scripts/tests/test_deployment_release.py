"""Release boundaries: public configuration, trusted provenance, immutable rollback."""
import importlib.util
import json
from pathlib import Path

import io
import re
from urllib.error import HTTPError

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
    backend, site = manifest['components']['backend'], manifest['components']['site']
    assert manifest['backend']['MCP_CONFIG_DIGEST'] == backend['digest']
    assert manifest['backend']['MCP_BACKEND_TREE'] == backend['tree']
    assert 'MCP_RELEASE_SHA' not in manifest['backend'], 'the commit must not be stamped into backend functions'
    assert manifest['frontend']['NEXT_PUBLIC_CONFIGURATION_DIGEST'] == site['digest']
    assert manifest['frontend']['NEXT_PUBLIC_SITE_TREE'] == site['tree']
    assert manifest['frontend']['NEXT_PUBLIC_RELEASE_SHA'] == manifest['sha']
    assert manifest['backend']['MCP_RUNTIME_SERVICE_ACCOUNT'].startswith('app-runtime@')
    assert all('SECRET' not in key and not key.endswith('API_KEY') for key in manifest['backend'])
    assert manifest['backend']['MAIL_MODE'] == ('staging' if environment == 'staging' else 'live')
    assert release.prepare(environment, dict(reversed(list(inputs(environment).items())))) == manifest


def test_real_sdk_inventory_matches_staging_http_release_profile():
    manifest = release.prepare('staging', inputs())
    names = release.expected_functions(manifest, {})
    assert len(names) == 130
    assert 'deployment_health' in names
    assert 'on_membership_created' not in names
    assert 'rebuild_analytics_nightly' not in names


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
    assert changed['components']['backend']['digest'] != manifest['components']['backend']['digest']
    assert changed['components']['site']['digest'] != manifest['components']['site']['digest']
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


def healths(manifest):
    backend, site = manifest['components']['backend'], manifest['components']['site']
    return dict(
        backend=dict(status='ok', environment=manifest['environment'], project_id=manifest['project'],
            backend_tree=backend['tree'], configuration_digest=backend['digest']),
        site=dict(status='ok', environment=manifest['environment'], project_id=manifest['project'],
            release_sha=manifest['sha'], site_tree=site['tree'], configuration_digest=site['digest']))


def test_smoke_rejects_wrong_release_even_with_http_success():
    manifest = release.prepare('staging', inputs())
    live = healths(manifest)
    for component, health in live.items():
        release.validate_health(health, manifest, component)
        for key in health:
            with pytest.raises(ValueError):
                release.validate_health({**health, key:'wrong'}, manifest, component)
    # The site commit is provenance: any valid commit passes unless the caller pins it.
    older = {**live['site'], 'release_sha':'c' * 40}
    release.validate_health(older, manifest, 'site')
    with pytest.raises(ValueError):
        release.validate_health(older, manifest, 'site', sha=manifest['sha'])
    with pytest.raises(ValueError):
        release.validate_health({**live['backend'], 'release_sha':manifest['sha']}, manifest, 'backend')


def _smoke_with(monkeypatch, failing, code):
    manifest = release.prepare('staging', inputs())
    seen = []

    def fetch(url):
        seen.append(url.rsplit('/', 1)[-1])
        if url.endswith('/' + failing):
            raise HTTPError(url, code, 'x', {}, io.BytesIO())
        return {}
    monkeypatch.setattr(release, 'fetch_json', fetch)
    monkeypatch.setattr(release, 'validate_health', lambda *_, **__: None)
    release.smoke(manifest)
    return seen


def test_smoke_accepts_an_empty_radio_but_still_checks_every_endpoint(monkeypatch):
    seen = _smoke_with(monkeypatch, 'get_latest_radio_episode', 404)
    assert seen[-1] == 'get_radio_seasons' and 'get_latest_radio_episode' in seen


@pytest.mark.parametrize('endpoint,code', [('get_latest_radio_episode', 500), ('get_latest_radio_episode', 403),
                                           ('get_all_events', 404), ('get_radio_seasons', 404)])
def test_smoke_rejects_other_failures(monkeypatch, endpoint, code):
    with pytest.raises(HTTPError):
        _smoke_with(monkeypatch, endpoint, code)


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
    return dict(schema=2, environment=manifest['environment'], project=manifest['project'],
        sha=manifest['sha'], components=manifest['components'],
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
    monkeypatch.setattr(release, 'smoke', lambda old, **kwargs: calls.append(('health', old['sha'])))
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
    assert 'MCP_BACKEND_TREE=' in data and 'MCP_RELEASE_SHA' not in data
    assert 'PAYPAL_CLIENT_SECRET=' not in data
    assert 'GOOGLE_APPLICATION_CREDENTIALS=' not in data
    web = (tmp_path / 'mcp-website' / ('.env.' + manifest['project'])).read_text()
    assert 'NEXT_PUBLIC_ENV="staging"' in web and 'NEXT_PUBLIC_RELEASE_SHA="' + manifest['sha'] + '"' in web
    assert all(line.startswith('NEXT_PUBLIC_') for line in web.splitlines())
    assert 'PAYPAL_CLIENT_SECRET' not in web and 'GOOGLE_APPLICATION_CREDENTIALS' not in web
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
        {'name':'MCP_BACKEND_TREE','value':manifest['components']['backend']['tree']},
        {'name':'MCP_CONFIG_DIGEST','value':manifest['components']['backend']['digest']},
        {'name':'PAYPAL_CLIENT_SECRET','valueFrom':{'secretKeyRef':{'key':'7'}}}]}]})
    monkeypatch.setattr(release, 'gcloud', lambda *args:json.dumps(response))
    release.verify_function_releases(manifest)
    response['spec']['containers'][0]['env'][0]['value'] = 'b' * 40
    with pytest.raises(ValueError, match='active backend revisions'):
        release.verify_function_releases(manifest)


def test_snapshot_collects_secret_versions_of_saved_revisions_after_rollback(monkeypatch):
    manifest = release.prepare('staging', inputs())
    live = healths(manifest)
    monkeypatch.setattr(release, 'fetch_json', lambda url: live['backend'] if 'cloudfunctions' in url else live['site'])
    monkeypatch.setattr(release, 'smoke', lambda _, **kwargs: None)
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


@pytest.mark.parametrize('names', [[], ['deployment_health', 'unapproved_event']])
def test_staging_snapshot_rejects_inventory_drift_before_revision_checks(monkeypatch, names):
    manifest = release.prepare('staging', inputs())
    monkeypatch.setattr(release, 'read_live', lambda _: healths(manifest))
    monkeypatch.setattr(release, 'verify_topology', lambda _: None)
    monkeypatch.setattr(release, 'cloud_functions', lambda _: [
        dict(name=name, labels={'firebase-functions-codebase':'python_codebase'}) for name in names])
    monkeypatch.setattr(release, 'expected_functions', lambda *a: ['deployment_health'])
    revision_checks = []
    monkeypatch.setattr(release, 'verify_function_releases', lambda _: revision_checks.append('checked'))
    monkeypatch.setattr(release, 'smoke', lambda *a, **kw: None)
    with pytest.raises(ValueError, match='function inventory changed'):
        release.snapshot_release(manifest, {})
    assert revision_checks == []


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
        PASS2U_MODE='fake', GENDER_MODE='fake', SOUNDCLOUD_MODE='staging')
    assert backend['MAILERSEND_FROM_EMAIL'] == 'hello@example.com'
    assert backend['MAIL_ALLOWED_RECIPIENTS'] == 'test@example.com,admin@example.com'
    assert backend['SOUNDCLOUD_CLIENT_ID'] == 'public-soundcloud-id'
    changed = release.prepare('staging', {**inputs(), 'MAIL_ALLOWED_RECIPIENTS':'other@example.com'})
    assert changed['components']['backend']['digest'] != manifest['components']['backend']['digest']
    assert changed['components']['site']['digest'] == manifest['components']['site']['digest']
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
        'SOUNDCLOUD_CLIENT_SECRET'}
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
        SOUNDCLOUD_CLIENT_SECRET='synthetic-radio')
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
        'create_wallet_pass':[], 'on_membership_created':['MAILERSEND_API_KEY'],
        'admin_create_radio_episode':['SOUNDCLOUD_CLIENT_SECRET'], 'deployment_health':[]}


@pytest.mark.parametrize('environment', ['staging', 'production'])
@pytest.mark.parametrize('publish', [False, True])
def test_hosting_request_uses_target_project_for_quota(monkeypatch, environment, publish):
    from contextlib import contextmanager
    from io import BytesIO
    from urllib.parse import parse_qs, urlparse

    manifest = release.prepare(environment, inputs(environment))
    calls = []

    def cloud(actual, *args):
        assert actual is manifest
        assert args == ('auth', 'print-access-token')
        return 'example-token'

    @contextmanager
    def open_request(request, timeout):
        calls.append(request)
        assert timeout == 30
        yield BytesIO(b'{"releases": []}')

    monkeypatch.setattr(release, 'urlopen', open_request)
    version = f"sites/{manifest['project']}/versions/example" if publish else None
    path = '/releases' if publish else '/releases?pageSize=1'
    assert release.hosting(manifest, path, version=version, cloud=cloud) == {'releases': []}
    assert len(calls) == 1
    request = calls[0]
    headers = {key.lower():value for key,value in request.header_items()}
    assert headers['x-goog-user-project'] == manifest['project']
    assert headers['authorization'] == 'Bearer example-token'
    parsed = urlparse(request.full_url)
    assert parsed.netloc == 'firebasehosting.googleapis.com'
    assert parsed.path == f"/v1beta1/sites/{manifest['project']}/releases"
    assert request.get_method() == ('POST' if publish else 'GET')
    if publish:
        assert parse_qs(parsed.query) == {'versionName':[version]}
        assert request.data == b'{}'


def test_revision_stamps_are_read_with_full_json_not_a_projection(monkeypatch):
    # gcloud 573 returns no env for `--format=json(spec.containers.env.name,...)`,
    # which made every correct release look mismatched.
    manifest = release.prepare('staging', inputs())
    revision = 'public-api-00001-abc'
    monkeypatch.setattr(release, 'cloud_functions', lambda _, **kwargs:[dict(
        name='deployment_health', labels={'firebase-functions-codebase':'python_codebase'},
        serviceConfig={'service':'public-api'})])
    monkeypatch.setattr(release, 'service_state', lambda *args, **kwargs:{'traffic':{revision:100}})
    response = dict(metadata={'name':revision}, spec={'containers':[{'env':[
        {'name':'MCP_BACKEND_TREE','value':manifest['components']['backend']['tree']},
        {'name':'MCP_CONFIG_DIGEST','value':manifest['components']['backend']['digest']}]}]})
    seen = []
    monkeypatch.setattr(release, 'gcloud', lambda *args: seen.append(args) or json.dumps(response))
    release.verify_function_releases(manifest)
    assert seen and all('--format=json' in call and not any('spec.containers' in str(part) for part in call) for call in seen)


def test_revision_secrets_fail_closed_when_description_has_no_containers_or_references(monkeypatch):
    manifest = release.prepare('staging', inputs())
    revision = 'public-api-00001-abc'
    seen = []
    data = dict(metadata={'name':revision})
    monkeypatch.setattr(release, 'gcloud', lambda _, *args: seen.append(args) or json.dumps(data))
    with pytest.raises(ValueError, match='container configuration'):
        release.verify_revision_secrets(manifest, revision)
    assert '--format=json' in seen[0]
    data = dict(metadata={'name':revision, 'annotations':{'run.googleapis.com/secrets':
        'provider-key:projects/p/secrets/PAYPAL_CLIENT_SECRET'}}, spec={'containers':[{'env':[]}]})
    with pytest.raises(ValueError, match='secret references missing'):
        release.verify_revision_secrets(manifest, revision)


def test_stamp_mismatch_error_never_contains_environment_values(monkeypatch):
    manifest = release.prepare('staging', inputs())
    revision = 'public-api-00001-abc'
    monkeypatch.setattr(release, 'cloud_functions', lambda _, **kwargs:[dict(
        name='x', labels={'firebase-functions-codebase':'python_codebase'}, serviceConfig={'service':'public-api'})])
    monkeypatch.setattr(release, 'service_state', lambda *args, **kwargs:{'traffic':{revision:100}})
    response = dict(metadata={'name':revision}, spec={'containers':[{'env':[
        {'name':'MCP_BACKEND_TREE','value':'b' * 40}, {'name':'API_TOKEN','value':'literal-secret-value'}]}]})
    monkeypatch.setattr(release, 'gcloud', lambda *args:json.dumps(response))
    with pytest.raises(ValueError) as error:
        release.verify_function_releases(manifest)
    assert 'literal-secret-value' not in str(error.value)


def test_release_environment_uses_experiments_not_previews():
    source = (release.ROOT / 'scripts/deployment/release.py').read_text() + \
        (release.ROOT / 'scripts/deployment/bootstrap_staging.py').read_text()
    assert "FIREBASE_CLI_EXPERIMENTS='webframeworks'" in source
    assert 'FIREBASE_CLI_PREVIEWS' not in source


def _preflight_fakes(monkeypatch, manifest):
    monkeypatch.setattr(release, 'github', lambda path: {'total_count': 1, 'branch_policies': [{'name': 'main', 'type': 'branch'}]})
    monkeypatch.setattr(release, 'validate_environment', lambda *args: None)
    monkeypatch.setattr(release, 'command', lambda *args, **kwargs: manifest['sha'] + '\n')


def test_read_only_preflight_skips_only_the_mutation_approvals(monkeypatch):
    manifest = release.prepare('staging', inputs())
    _preflight_fakes(monkeypatch, manifest)
    monkeypatch.delenv('PAYMENT_ROLLOUT_APPROVED', raising=False)
    monkeypatch.delenv('ROLLBACK_BASELINE_VERIFIED', raising=False)
    release.preflight(manifest, read_only=True)
    with pytest.raises(ValueError, match='payment worker compatibility approval'):
        release.preflight(manifest)
    monkeypatch.setenv('PAYMENT_ROLLOUT_APPROVED', 'true')
    with pytest.raises(ValueError, match='rollback proof'):
        release.preflight(manifest)
    # Source and environment protections still apply in read-only mode.
    monkeypatch.setattr(release, 'command', lambda *args, **kwargs: 'b' * 40 + '\n')
    with pytest.raises(ValueError, match='checkout SHA'):
        release.preflight(manifest, read_only=True)


@pytest.mark.parametrize(('environment', 'event', 'proof', 'payment', 'allowed'), [
    ('staging', 'workflow_dispatch', 'true', 'true', True),
    ('staging', 'workflow_dispatch', '', 'true', False),
    ('staging', 'workflow_dispatch', 'false', 'true', False),
    ('staging', 'workflow_dispatch', 'TRUE', 'true', False),
    ('staging', 'push', 'true', 'true', False),
    ('production', 'workflow_dispatch', 'true', 'true', False),
    ('staging', 'workflow_dispatch', 'true', 'false', False),
])
def test_unproven_baseline_allows_only_explicit_manual_staging_proof(
        monkeypatch, environment, event, proof, payment, allowed):
    manifest = release.prepare(environment, inputs(environment))
    _preflight_fakes(monkeypatch, manifest)
    monkeypatch.setenv('ROLLBACK_BASELINE_VERIFIED', 'false')
    monkeypatch.setenv('STAGING_RELEASE_PROOF_APPROVED', proof)
    monkeypatch.setenv('GITHUB_EVENT_NAME', event)
    monkeypatch.setenv('PAYMENT_ROLLOUT_APPROVED', payment)
    if allowed:
        release.preflight(manifest)
        # Proof consent must not disable the trusted checkout check.
        monkeypatch.setattr(release, 'command', lambda *a, **kw: 'b' * 40 + '\n')
        with pytest.raises(ValueError, match='checkout SHA'):
            release.preflight(manifest)
    else:
        with pytest.raises(ValueError):
            release.preflight(manifest)


@pytest.mark.parametrize('environment', ['staging', 'production'])
def test_verified_baseline_retains_ordinary_release_path(monkeypatch, environment):
    manifest = release.prepare(environment, inputs(environment))
    _preflight_fakes(monkeypatch, manifest)
    monkeypatch.setenv('ROLLBACK_BASELINE_VERIFIED', 'true')
    monkeypatch.setenv('PAYMENT_ROLLOUT_APPROVED', 'true')
    monkeypatch.delenv('STAGING_RELEASE_PROOF_APPROVED', raising=False)
    monkeypatch.setenv('GITHUB_EVENT_NAME', 'push')
    release.preflight(manifest)


@pytest.mark.parametrize('operation', ['deploy', 'snapshot', 'rollback'])
def test_read_only_flag_is_rejected_for_mutating_operations(monkeypatch, operation):
    monkeypatch.setattr('sys.argv', ['release.py', operation, '--environment', 'staging', '--read-only'])
    with pytest.raises(ValueError, match='read-only scope'):
        release.main()


def test_verify_access_job_is_manual_read_only_and_needs_no_deploy_flag():
    import yaml
    jobs = yaml.safe_load((ROOT / '.github/workflows/release.yml').read_text())['jobs']
    job = jobs['verify-access']
    assert job['needs'] == 'verify'
    assert job['if'] == "github.event_name == 'workflow_dispatch' && inputs.operation == 'verify'"
    assert job['with'] == {'environment': 'staging', 'operation': 'verify'}
    assert 'ENABLE_' not in job['if']
    # No mutating job can start for a verify dispatch.
    for name in ['staging', 'production', 'rollback']:
        assert 'verify' not in jobs[name]['if'].replace('needs.verify', '')
    steps = yaml.safe_load((ROOT / '.github/workflows/deploy-environment.yml').read_text())['jobs']['release']['steps']
    conditions = {step.get('name'): step.get('if') for step in steps}
    assert conditions['Capture verified previous release before mutations'] == "inputs.operation == 'deploy'"
    assert conditions['Preserve rollback snapshot before deployment'] == "inputs.operation == 'deploy'"


def test_component_identity_changes_only_with_its_own_component(synthetic_component_trees):
    base = release.prepare('staging', inputs())
    # An unrelated commit (docs, tooling, tests) changes neither tree.
    other_commit = release.prepare('staging', {**inputs(), 'GITHUB_SHA':'b' * 40})
    assert other_commit['components'] == base['components']
    synthetic_component_trees['mcp-backend/functions'] = 'changed'
    backend_edit = release.prepare('staging', inputs())
    assert backend_edit['components']['backend']['tree'] != base['components']['backend']['tree']
    assert backend_edit['components']['site'] == base['components']['site']
    synthetic_component_trees.clear()
    synthetic_component_trees['mcp-website'] = 'changed'
    site_edit = release.prepare('staging', inputs())
    assert site_edit['components']['site']['tree'] != base['components']['site']['tree']
    assert site_edit['components']['backend'] == base['components']['backend']
    synthetic_component_trees.clear()
    synthetic_component_trees['firebase.json'] = 'changed'
    hosting_config_edit = release.prepare('staging', inputs())
    assert hosting_config_edit['components']['site']['tree'] != base['components']['site']['tree']


def test_plan_names_only_components_that_differ_from_live():
    manifest = release.prepare('staging', inputs())
    live = healths(manifest)
    assert release.plan_release(manifest, live) == {'backend': False, 'site': False}
    older_site_commit = {**live, 'site': {**live['site'], 'release_sha': 'c' * 40}}
    assert release.plan_release(manifest, older_site_commit) == {'backend': False, 'site': False}
    assert release.plan_release(manifest, {**live, 'site': {**live['site'], 'site_tree': 'd' * 64}}) == \
        {'backend': False, 'site': True}
    assert release.plan_release(manifest, {**live, 'backend': {**live['backend'], 'backend_tree': 'd' * 40}}) == \
        {'backend': True, 'site': False}
    assert release.plan_release(manifest, {**live, 'backend': {**live['backend'], 'configuration_digest': 'e' * 64}}) == \
        {'backend': True, 'site': False}


@pytest.mark.parametrize('broken', [None, {}, {'status': 'unversioned'}, {'status': 'ok', 'environment': 'production'}])
@pytest.mark.parametrize('component', ['backend', 'site'])
def test_plan_fails_closed_when_live_identity_is_unreadable_or_foreign(component, broken):
    manifest = release.prepare('staging', inputs())
    live = {**healths(manifest), component: broken}
    with pytest.raises(ValueError, match='identity readable'):
        release.plan_release(manifest, live)


def test_legacy_live_backend_without_a_tree_is_planned_for_update_not_skipped():
    manifest = release.prepare('staging', inputs())
    live = healths(manifest)
    live['backend'] = {'status': 'ok', 'environment': 'staging', 'project_id': manifest['project'],
        'release_sha': 'b' * 40, 'configuration_digest': 'f' * 64}
    assert release.plan_release(manifest, live) == {'backend': True, 'site': False}


@pytest.mark.parametrize('changed,deployed', [
    ({'backend': False, 'site': False}, []), ({'backend': False, 'site': True}, ['hosting']),
    ({'backend': True, 'site': False}, ['backend']), ({'backend': True, 'site': True}, ['backend', 'hosting'])])
def test_release_deploys_only_changed_components_and_always_verifies_all(monkeypatch, changed, deployed):
    manifest = release.prepare('staging', inputs())
    calls = []
    monkeypatch.setattr(release, 'command', lambda args, **kwargs: calls.append(args[-1]))
    monkeypatch.setattr(release, 'verify_function_releases', lambda m: calls.append('verify-functions'))
    monkeypatch.setattr(release, 'smoke', lambda m, **kwargs: calls.append(('smoke', kwargs.get('site_sha'))))
    assert release.execute_release(manifest, {}, changed) == deployed
    assert calls[:len(deployed)] == deployed
    assert calls[len(deployed):] == ['verify-functions', ('smoke', manifest['sha'] if changed['site'] else None)]


def test_release_manifest_records_deployed_and_skipped(tmp_path, monkeypatch):
    manifest = release.prepare('staging', inputs())
    monkeypatch.setattr(release, 'ROOT', tmp_path)
    release.write_release_manifest(manifest, {'backend': False, 'site': True}, ['hosting'])
    record = json.loads((tmp_path / '.local/release/release-staging.json').read_text())
    assert record['deployed'] == ['hosting'] and record['skipped'] == ['backend']
    assert record['commit'] == manifest['sha'] and record['components'] == manifest['components']


def test_workflow_plans_before_any_snapshot_and_publishes_the_manifest_only_on_success():
    import yaml
    steps = yaml.safe_load((ROOT / '.github/workflows/deploy-environment.yml').read_text())['jobs']['release']['steps']
    names = [step.get('name', '') for step in steps]
    plan = next(i for i, name in enumerate(names) if name.startswith('Show release plan'))
    snapshot_step = names.index('Capture verified previous release before mutations')
    assert plan < snapshot_step
    assert steps[plan]['if'] == "inputs.operation == 'deploy'"
    assert 'release.py plan' in steps[plan]['run']
    publish = next(step for step in steps if step.get('name', '').startswith('Publish release manifest'))
    assert publish['if'] == "success() && inputs.operation == 'deploy'"
    assert publish['with']['path'] == '.local/release/release-${{ inputs.environment }}.json'
    assert steps.index(publish) > names.index('Deploy or restore immutable revisions and verify release')


def test_component_trees_resolve_against_real_git():
    # "HEAD" is a symbolic revision, so the synthetic fixture lets it through to real git.
    backend, site = release.component_trees('HEAD')
    assert re.fullmatch('[0-9a-f]{40}', backend) and re.fullmatch('[0-9a-f]{64}', site)
    assert backend != site[:40]


def _stale_fakes(monkeypatch, manifest, pinned_version):
    def gcloud(_, *args):
        assert args[:4] == ('secrets', 'versions', 'describe', 'latest')
        return f'projects/1/secrets/{args[5]}/versions/8\n'
    monkeypatch.setattr(release, 'gcloud', gcloud)
    monkeypatch.setattr(release, 'cloud_functions', lambda _: [dict(name='f',
        labels={'firebase-functions-codebase':'python_codebase'}, serviceConfig={'service':'public-api'})])
    monkeypatch.setattr(release, 'service_state', lambda *a, **k: {'traffic':{'public-api-00001-abc':100}})
    monkeypatch.setattr(release, 'verify_revision_secrets',
        lambda *_: {('PAYPAL_CLIENT_SECRET', pinned_version), ('UNRELATED_SECRET', '1')})


def test_rotated_secret_marks_an_unchanged_backend_for_update(monkeypatch):
    manifest = release.prepare('staging', inputs())
    _stale_fakes(monkeypatch, manifest, '7')
    assert release.stale_secret_versions(manifest) == ['PAYPAL_CLIENT_SECRET']


def test_current_secret_versions_leave_the_backend_alone(monkeypatch):
    manifest = release.prepare('staging', inputs())
    _stale_fakes(monkeypatch, manifest, '8')
    assert release.stale_secret_versions(manifest) == []
