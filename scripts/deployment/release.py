#!/usr/bin/env python3
"""Trusted main releases. Never reads provider secret payloads or copies dotenv files."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = 'Vittorix99/mcp-website'
REPOSITORY_ID = 899139661
WORKFLOW = '.github/workflows/release.yml'
REGION = 'us-central1'
SHA = r'[0-9a-f]{40}'
DIGEST = r'[0-9a-f]{64}'
NAME = r'[a-z][a-z0-9-]{0,62}'
SECRET_KEYS = ('PAYPAL_CLIENT_SECRET', 'PAYPAL_LIVE_CLIENT_SECRET', 'MAILERSEND_API_KEY',
    'PASS2U_API_KEY', 'SOUNDCLOUD_CLIENT_SECRET', 'GENDER_API_KEY', 'SENDER_API_KEY',
    'SENDER_WEBHOOK_SECRET', 'FIREBASE_TOKEN', 'FIREBASE_SERVICE_ACCOUNT_JSON',
    'FIREBASE_SERVICE_ACCOUNT', 'GMAIL_SERVICE_ACCOUNT_JSON', 'MCP_ENV_FILE')
TOPOLOGY_PATHS = ['firebase.json', 'mcp-backend/functions/triggers',
    'mcp-backend/functions/api/decorators', 'mcp-backend/functions/config/function_secrets.py']


def require(condition, field):
    if not condition:
        raise ValueError(f'Release validation failed: {field}')


def public_value(env, key):
    value = env.get(key, '')
    require(isinstance(value, str) and 0 < len(value) <= 2048 and
        not any(ord(c) < 32 or c in '\"\\' for c in value), key)
    return value


def prepare(environment, env):
    require(environment in {'staging', 'production'}, 'environment')
    require(env.get('GITHUB_REPOSITORY') == REPOSITORY and
        str(env.get('GITHUB_REPOSITORY_ID')) == str(REPOSITORY_ID), 'repository identity')
    require(env.get('GITHUB_REF') == 'refs/heads/main', 'main ref')
    require(env.get('GITHUB_WORKFLOW_REF') == f'{REPOSITORY}/{WORKFLOW}@refs/heads/main', 'workflow identity')
    require(env.get('GITHUB_EVENT_NAME') in {'push', 'workflow_dispatch'}, 'trusted event')
    sha = env.get('GITHUB_SHA', '')
    return public_configuration(environment, env, sha)


def public_configuration(environment, env, sha):
    """Public release inputs only; callers must independently authenticate their source."""
    catalog = json.loads((ROOT / 'mcp-backend/functions/config/environment_catalog.json').read_text())
    require(environment in {'staging', 'production'}, 'environment')
    resource = catalog['environments'][environment]
    project = resource['project_id']
    require(re.fullmatch(SHA, sha), 'release SHA')
    for key in SECRET_KEYS:
        require(not env.get(key), 'provider credentials must stay in Secret Manager')
    require(not any(key.startswith('NEXT_PUBLIC_') for key in env), 'unexpected frontend inputs')
    identities = {}
    for key in ['DEPLOY_SERVICE_ACCOUNT', 'BUILD_SERVICE_ACCOUNT', 'RUNTIME_SERVICE_ACCOUNT', 'WEB_RUNTIME_SERVICE_ACCOUNT']:
        value = public_value(env, key)
        require(re.fullmatch(r'[a-z][a-z0-9-]{4,28}[a-z0-9]@' + re.escape(project) + r'\.iam\.gserviceaccount\.com', value), key)
        identities[key] = value
    require(len(set(identities.values())) == 4, 'separate deploy/build/backend/web identities')
    provider = public_value(env, 'WIF_PROVIDER')
    require(re.fullmatch(r'projects/[0-9]+/locations/global/workloadIdentityPools/[a-z0-9-]+/providers/[a-z0-9-]+', provider), 'WIF provider')
    backend = dict(MCP_ENV=environment, STORAGE_BUCKET=resource['storage_bucket'],
        BACKEND_URL=resource['backend_url'], ALLOWED_ORIGINS=','.join(resource['allowed_origins']),
        MCP_RUNTIME_SERVICE_ACCOUNT=identities['RUNTIME_SERVICE_ACCOUNT'],
        PAYPAL_CLIENT_ID=public_value(env, 'PAYPAL_CLIENT_ID'))
    backend.update({f'{provider.upper()}_MODE':mode for provider, mode in resource['providers'].items()})
    # The release profile enables explicit E2E integrations; bare runtime defaults stay offline-safe.
    if environment == 'staging':
        backend.update(MAIL_MODE='staging', PASS2U_MODE='fake', GENDER_MODE='fake',
            SOUNDCLOUD_MODE='staging')
        recipients = public_value(env, 'MAIL_ALLOWED_RECIPIENTS')
        require(all(re.fullmatch(r'[^\s@,;<>*]+@[^\s@,;<>*]+\.[^\s@,;<>*]+', address)
            for address in recipients.split(',')), 'MAIL_ALLOWED_RECIPIENTS exact addresses')
        backend['MAIL_ALLOWED_RECIPIENTS'] = recipients
    for key in ['MAILERSEND_FROM_EMAIL', 'MAILERSEND_FROM_NAME', 'SOUNDCLOUD_CLIENT_ID']:
        backend[key] = public_value(env, key)
    frontend = dict(NEXT_PUBLIC_ENV=environment, NEXT_PUBLIC_BASE_URL=resource['backend_url'],
        NEXT_PUBLIC_FIREBASE_PROJECT_ID=project, NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=resource['storage_bucket'],
        NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=f'{project}.firebaseapp.com',
        NEXT_PUBLIC_FIREBASE_API_KEY=public_value(env, 'FIREBASE_API_KEY'),
        NEXT_PUBLIC_FIREBASE_APP_ID=public_value(env, 'FIREBASE_APP_ID'),
        NEXT_PUBLIC_PAYPAL_ENV='sandbox' if environment == 'staging' else 'production',
        **{('NEXT_PUBLIC_PAYPAL_CLIENT_ID' if environment == 'staging' else 'NEXT_PUBLIC_PAYPAL_LIVE_CLIENT_ID'):backend['PAYPAL_CLIENT_ID']})
    digest = hashlib.sha256(json.dumps(dict(backend=backend,frontend=frontend,
        web_runtime=identities['WEB_RUNTIME_SERVICE_ACCOUNT'],
        build_account=identities['BUILD_SERVICE_ACCOUNT']), sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    backend.update(MCP_RELEASE_SHA=sha, MCP_CONFIG_DIGEST=digest)
    frontend.update(NEXT_PUBLIC_RELEASE_SHA=sha, NEXT_PUBLIC_CONFIGURATION_DIGEST=digest)
    return dict(schema=1, environment=environment, project=project, sha=sha, digest=digest,
        backend=backend, frontend=frontend, identities=identities, wif_provider=provider)


def validate_environment(environment, metadata, branches):
    policy = metadata.get('deployment_branch_policy') or {}
    require(policy.get('custom_branch_policies') is True and
        policy.get('protected_branches') is False, 'explicit environment branch policy')
    require(branches == [{'name':'main', 'type':'branch'}], 'only main may deploy')
    if environment == 'production':
        require(metadata.get('can_admins_bypass') is False, 'production approval cannot be bypassed')
        require(any(rule.get('type') == 'required_reviewers' and rule.get('reviewers')
            for rule in metadata.get('protection_rules', [])), 'production required reviewers')


def validate_snapshot_run(run):
    repository = run.get('repository', {})
    require(repository.get('full_name') == REPOSITORY and repository.get('id') == REPOSITORY_ID,
        'snapshot repository')
    require(run.get('path') == WORKFLOW and run.get('head_branch') == 'main' and
        re.fullmatch(SHA, run.get('head_sha', '')) and
        run.get('event') in {'push', 'workflow_dispatch'} and run.get('status') == 'completed' and
        run.get('conclusion') in {'success', 'failure', 'cancelled'} and run.get('run_attempt') == 1,
        'snapshot run provenance')


def validate_health(health, manifest):
    require(health == dict(status='ok', environment=manifest['environment'],
        project_id=manifest['project'], release_sha=manifest['sha'], configuration_digest=manifest['digest']),
        'deployed release identity')


def validate_snapshot(snapshot, manifest):
    require(snapshot.get('schema') == 1 and snapshot.get('project') == manifest['project'] and
        snapshot.get('environment') == manifest['environment'], 'snapshot environment')
    require(re.fullmatch(SHA, snapshot.get('sha', '')) and
        re.fullmatch(DIGEST, snapshot.get('digest', '')), 'snapshot version stamps')
    require(re.fullmatch('sites/' + re.escape(manifest['project']) + r'/versions/[a-zA-Z0-9-]+',
        snapshot.get('hosting_version', '')), 'snapshot hosting version')
    require(isinstance(snapshot.get('functions'), list) and snapshot['functions'] and
        all(re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_]*', name) for name in snapshot['functions']), 'snapshot function names')
    require(isinstance(snapshot.get('services'), dict) and snapshot['services'], 'snapshot services')
    require(isinstance(snapshot.get('secrets'), list), 'snapshot secret version references')
    for reference in snapshot['secrets']:
        require(re.fullmatch(r'[A-Z][A-Z0-9_]*', reference.get('secret', '')) and
            re.fullmatch(r'[1-9][0-9]*', reference.get('version', '')), 'snapshot numeric secret reference')
    for service, state in snapshot['services'].items():
        require(re.fullmatch(NAME, service), 'snapshot service name')
        traffic = state.get('traffic', {})
        require(traffic and all(re.fullmatch(re.escape(service) + r'-[a-z0-9-]+', revision) and
            type(percent) is int and 0 < percent <= 100 for revision, percent in traffic.items()) and
            sum(traffic.values()) == 100, 'immutable revision traffic')


def command(args, *, env=None, cwd=ROOT):
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True)
    # Do not echo CLI stdout/stderr: SDK diagnostics can include environment or credentials.
    require(result.returncode == 0, f'{Path(args[0]).name} command (diagnostics withheld)')
    return result.stdout


def github(path):
    return json.loads(command(['gh', 'api', f'repos/{REPOSITORY}/{path}']))


def gcloud(manifest, *args):
    return command(['gcloud', *args, '--project', manifest['project'], '--quiet'])


def hosting(manifest, path, *, version=None, cloud=None):
    token = (cloud or gcloud)(manifest, 'auth', 'print-access-token').strip()
    url = 'https://firebasehosting.googleapis.com/v1beta1/sites/' + manifest['project'] + path
    if version is not None:
        url += '?' + urlencode({'versionName':version})
    req = Request(url, data=b'{}' if version else None,
        # Personal OAuth needs an explicit quota project for Hosting requests.
        headers={'Authorization':'Bearer ' + token, 'Content-Type':'application/json',
            'x-goog-user-project':manifest['project']})
    with urlopen(req, timeout=30) as response:
        return json.load(response)


def cloud_functions(manifest, *, cloud=None):
    # Select public metadata only; never request environment values or secret payloads.
    records = json.loads((cloud or gcloud)(manifest, 'functions', 'list', '--v2', '--regions', REGION,
        '--format=json(name,labels,serviceConfig.service,serviceConfig.revision)'))
    codebases = {'python_codebase', 'firebase-frameworks-' + manifest['project']}
    return [item for item in records if item.get('labels', {}).get('firebase-functions-codebase') in codebases]


def service_state(manifest, service, *, cloud=None):
    data = json.loads((cloud or gcloud)(manifest, 'run', 'services', 'describe', service, '--region', REGION,
        '--format=json(status.traffic)'))
    traffic = {}
    for row in data.get('status', {}).get('traffic', []):
        if row.get('percent', 0):
            revision = row.get('revisionName', '')
            traffic[revision] = traffic.get(revision, 0) + row['percent']
    return {'traffic':traffic}


# Mirrors mcp-website/config/build-reads.cjs: these endpoints answer 404 on an empty environment.
EMPTY_STATE_ENDPOINTS = frozenset({'get_latest_radio_episode'})


def fetch_json(url):
    with urlopen(Request(url, headers={'Cache-Control':'no-cache'}), timeout=30) as response:
        require(response.status == 200, 'HTTP smoke status')
        return json.load(response)


def smoke(manifest):
    project = manifest['project']
    for url in [f'https://us-central1-{project}.cloudfunctions.net/deployment_health',
                f'https://{project}.web.app/api/deployment-health']:
        # Bounded retry handles propagation; mismatch is never reported as success.
        for attempt in range(6):
            try:
                validate_health(fetch_json(url), manifest)
                break
            except Exception:
                if attempt == 5:
                    raise ValueError('Release health check failed') from None
                time.sleep(5)
    for endpoint in ['get_all_events', 'get_next_event', 'get_membership_price_public',
                     'get_published_radio_episodes', 'get_latest_radio_episode', 'get_radio_seasons']:
        try:
            fetch_json(f'https://us-central1-{project}.cloudfunctions.net/{endpoint}')
        except HTTPError as error:
            # An environment without radio episodes is valid; any other failure is not.
            if not (endpoint in EMPTY_STATE_ENDPOINTS and error.code == 404):
                raise


def expected_functions(manifest, env):
    result = command([str(ROOT / '.venv/bin/python'), '-c',
        'import json; from firebase_functions.private.serving import get_functions; '
        'print(json.dumps(sorted(get_functions())))'], cwd=ROOT / 'mcp-backend/functions',
        env={**env, **manifest['backend'], 'ADMIN_PORT':'8087'})
    return json.loads(result)


def snapshot_release(manifest, env):
    previous = fetch_json(f'https://{manifest["project"]}.web.app/api/deployment-health')
    old = {**manifest, 'sha':previous.get('release_sha'), 'digest':previous.get('configuration_digest')}
    validate_health(previous, old)
    verify_topology(old['sha'])
    verify_function_releases(old)
    smoke(old)
    records = cloud_functions(manifest)
    functions = sorted(item['name'].rsplit('/', 1)[-1] for item in records
        if item.get('labels', {}).get('firebase-functions-codebase') == 'python_codebase')
    require(functions == expected_functions(manifest, env),
        'function inventory changed: controlled baseline required before automatic release')
    require(any(item.get('labels', {}).get('firebase-functions-codebase') ==
        'firebase-frameworks-' + manifest['project'] for item in records), 'SSR rollback target')
    services = {}
    references = set()
    for item in records:
        service = item.get('serviceConfig', {}).get('service', '').rsplit('/', 1)[-1]
        require(re.fullmatch(NAME, service), 'managed Cloud Run service')
        services[service] = service_state(manifest, service)
        for revision in services[service]['traffic']:
            references.update(verify_revision_secrets(manifest, revision))
    releases = hosting(manifest, '/releases?pageSize=1').get('releases', [])
    require(len(releases) == 1 and releases[0].get('type') == 'DEPLOY', 'previous Hosting release')
    snapshot = dict(schema=1, environment=manifest['environment'], project=manifest['project'],
        sha=old['sha'], digest=old['digest'], functions=functions, services=services,
        secrets=[dict(secret=name,version=version) for name,version in sorted(references)],
        hosting_version=releases[0]['version']['name'])
    validate_snapshot(snapshot, manifest)
    verify_secret_versions(snapshot, manifest)
    return snapshot


def rollback(snapshot, manifest):
    validate_snapshot(snapshot, manifest)
    verify_topology(snapshot['sha'])
    verify_secret_versions(snapshot, manifest)
    # Validate ALL targets before the first mutation; no guessed service names or latest pointers.
    records = cloud_functions(manifest)
    current = {item.get('serviceConfig', {}).get('service', '').rsplit('/', 1)[-1] for item in records}
    require(current == set(snapshot['services']), 'rollback service inventory')
    functions = sorted(item['name'].rsplit('/', 1)[-1] for item in records
        if item.get('labels', {}).get('firebase-functions-codebase') == 'python_codebase')
    require(functions == snapshot['functions'], 'rollback function inventory')
    references = set()
    for service, state in snapshot['services'].items():
        for revision in state['traffic']:
            references.update(verify_revision_secrets(manifest, revision))
    require(references == {(item['secret'],item['version']) for item in snapshot['secrets']},
        'snapshot must describe secrets of every saved active revision')
    for service, state in snapshot['services'].items():
        target = ','.join(f'{revision}={percent}' for revision, percent in sorted(state['traffic'].items()))
        gcloud(manifest, 'run', 'services', 'update-traffic', service, '--region', REGION, '--to-revisions', target)
    hosting(manifest, '/releases', version=snapshot['hosting_version'])
    for service, state in snapshot['services'].items():
        require(service_state(manifest, service) == state, 'restored revision traffic')
    smoke({**manifest, 'sha':snapshot['sha'], 'digest':snapshot['digest']})


def verify_topology(previous_sha):
    require(bool(re.fullmatch(SHA, previous_sha or '')), 'baseline SHA')
    command(['git', 'merge-base', '--is-ancestor', previous_sha, 'HEAD'])
    # Traffic rollback does not restore Eventarc filters, Scheduler definitions,
    # rules or indexes. Refuse those changes before deploy, rather than promise
    # a rollback that restores only part of the control plane.
    changed = command(['git', 'diff', '--name-only', previous_sha, 'HEAD', '--', *TOPOLOGY_PATHS])
    require(not changed.strip(), 'trigger/deployment topology changed: controlled baseline required')


def verify_secret_versions(snapshot, manifest):
    for reference in snapshot['secrets']:
        require(gcloud(manifest, 'secrets', 'versions', 'describe', reference['version'],
            '--secret', reference['secret'], '--format=value(state)').strip() == 'ENABLED',
            'previous secret version must remain enabled for rollback')


def verify_revision_secrets(manifest, revision):
    # Revisions are immutable, but a reference to "latest" is not. Preserve only
    # revisions whose secret environment references use explicit numeric versions.
    data = json.loads(gcloud(manifest, 'run', 'revisions', 'describe', revision, '--region', REGION,
        '--format=json'))
    require(data.get('metadata', {}).get('name') == revision, 'existing immutable revision')
    # Field projections into repeated env/volumes can silently return nothing
    # (gcloud 573); an empty result must never read as "no secrets".
    require(bool(data.get('spec', {}).get('containers')), 'revision container configuration')
    aliases = {}
    for entry in data.get('metadata', {}).get('annotations', {}).get('run.googleapis.com/secrets', '').split(','):
        if entry:
            key, separator, resource = entry.partition(':')
            require(bool(separator), 'secret reference annotation')
            aliases[key] = resource
    references = set()
    def add(name, version):
        require(bool(re.fullmatch(r'[1-9][0-9]*', str(version))), 'rollback requires numeric secret versions')
        resource = aliases.get(name, name)
        if resource.startswith('projects/'):
            match = re.fullmatch(r'projects/([^/]+)/secrets/([A-Z][A-Z0-9_]*)', resource)
            require(bool(match), 'secret resource reference')
            project, name = match.groups()
            if project != manifest['project']:
                actual = gcloud(manifest, 'projects', 'describe', manifest['project'], '--format=value(projectNumber)').strip()
                require(project == actual and actual.isdecimal(), 'same-project secret reference')
        else:
            name = resource
        require(bool(re.fullmatch(r'[A-Z][A-Z0-9_]*', name)), 'canonical provider secret name')
        references.add((name,str(version)))
    for container in data.get('spec', {}).get('containers', []):
        for item in container.get('env', []):
            reference = item.get('valueFrom', {}).get('secretKeyRef')
            if reference:
                add(reference.get('name', ''), reference.get('key', ''))
    for volume in data.get('spec', {}).get('volumes', []):
        secret = volume.get('secret', {})
        if secret:
            require(secret.get('items'), 'explicit mounted secret versions')
            for item in secret['items']:
                add(secret.get('secretName', ''), item.get('key', ''))
    require(bool(references) or not aliases, 'secret references missing from revision description')
    return references


def cloud_preflight(manifest, *, cloud=None):
    cloud = cloud or gcloud
    require(cloud(manifest, 'projects', 'describe', manifest['project'], '--format=value(projectId)').strip()
        == manifest['project'], 'actual project')
    bucket = manifest['backend']['STORAGE_BUCKET']
    require(cloud(manifest, 'storage', 'buckets', 'describe', 'gs://' + bucket, '--format=value(name)').strip()
        .removeprefix('gs://').rstrip('/') == bucket, 'actual storage bucket')
    enabled = set(cloud(manifest, 'services', 'list', '--enabled', '--format=value(config.name)').split())
    require({'cloudfunctions.googleapis.com', 'cloudbuild.googleapis.com', 'run.googleapis.com',
        'artifactregistry.googleapis.com', 'secretmanager.googleapis.com', 'firebasehosting.googleapis.com',
        'eventarc.googleapis.com', 'pubsub.googleapis.com', 'firestore.googleapis.com',
        'storage.googleapis.com', 'identitytoolkit.googleapis.com', 'cloudscheduler.googleapis.com'} <= enabled, 'pre-enabled deployment APIs')
    for account in manifest['identities'].values():
        require(cloud(manifest, 'iam', 'service-accounts', 'describe', account, '--format=value(email)').strip()
            == account, 'existing service identity')
    secrets = [secret for provider, secret in [
        ('PAYPAL', 'PAYPAL_CLIENT_SECRET'), ('MAIL', 'MAILERSEND_API_KEY'),
        ('PASS2U', 'PASS2U_API_KEY'), ('SOUNDCLOUD', 'SOUNDCLOUD_CLIENT_SECRET'),
        ('GENDER', 'GENDER_API_KEY')]
        if manifest['backend'].get(provider + '_MODE') in {'sandbox', 'staging', 'live'}]
    for secret in secrets:
        require(cloud(manifest, 'secrets', 'versions', 'describe', 'latest', '--secret', secret,
            '--format=value(state)').strip() == 'ENABLED', 'enabled provider secret version')
        policy = json.loads(cloud(manifest, 'secrets', 'get-iam-policy', secret, '--format=json(bindings)'))
        member = 'serviceAccount:' + manifest['identities']['RUNTIME_SERVICE_ACCOUNT']
        require(any(binding.get('role') == 'roles/secretmanager.secretAccessor' and
            member in binding.get('members', []) and not binding.get('condition')
            for binding in policy.get('bindings', [])), 'preconfigured per-secret runtime access')


def release_environment(manifest):
    # CLI, discovery and framework code receive an explicit environment, never the runner's dotenv.
    allowed = ['PATH', 'HOME', 'TMPDIR', 'CI', 'GOOGLE_APPLICATION_CREDENTIALS']
    env = {key:os.environ[key] for key in allowed if key in os.environ}
    env.update(GCLOUD_PROJECT=manifest['project'], GOOGLE_CLOUD_PROJECT=manifest['project'],
        CLOUDSDK_CORE_PROJECT=manifest['project'], CLOUDSDK_CORE_DISABLE_PROMPTS='1',
        FIREBASE_CLI_EXPERIMENTS='webframeworks', MCP_RELEASE_CONFIG=str(ROOT / '.local/release/config.json'),
        NEXT_TELEMETRY_DISABLED='1')
    return env


def write_configuration(manifest):
    # Fresh checkout only. Refuse inherited local configuration without reading its contents.
    for directory in [ROOT, ROOT / 'mcp-backend/functions', ROOT / 'mcp-website']:
        require(not [path for path in directory.glob('.env*') if path.name != '.env.example'],
            'existing dotenv files')
    scratch = ROOT / '.local/release'
    scratch.mkdir(parents=True, exist_ok=True, mode=0o700)
    (scratch / 'config.json').write_text(json.dumps(manifest, sort_keys=True) + '\n')
    env_file = ROOT / 'mcp-backend/functions' / ('.env.' + manifest['project'])
    env_file.write_text(''.join(f'{key}="{value}"\n' for key, value in sorted(manifest['backend'].items())))
    # The SSR function validates its public runtime settings when next.config.js loads
    # at server start. firebase-tools copies mcp-website/.env.* into the SSR function and
    # applies it as environment; without this file the function crashes on boot (HTTP 500).
    # Public NEXT_PUBLIC_* values only; secrets stay in Secret Manager.
    web_env = ROOT / 'mcp-website' / ('.env.' + manifest['project'])
    require(all(re.fullmatch(r'NEXT_PUBLIC_[A-Z0-9_]+', key) for key in manifest['frontend']), 'public frontend keys')
    web_env.write_text(''.join(f'{key}="{value}"\n' for key, value in sorted(manifest['frontend'].items())))
    config = json.loads((ROOT / 'firebase.json').read_text())
    config['hosting']['site'] = manifest['project']
    config['hosting']['frameworksBackend']['serviceAccount'] = manifest['identities']['WEB_RUNTIME_SERVICE_ACCOUNT']
    (ROOT / 'firebase.release.generated.json').write_text(json.dumps(config) + '\n')
    target = ROOT / 'mcp-backend/functions/venv'
    if target.exists() or target.is_symlink():
        require(target.is_symlink() and target.resolve() == (ROOT / '.venv').resolve(), 'Python virtualenv')
    else:
        target.symlink_to('../../.venv', target_is_directory=True)


def verify_function_releases(manifest, *, cloud=None):
    cloud = cloud or gcloud
    records = cloud_functions(manifest, cloud=cloud)
    managed = [item for item in records if item.get('labels', {}).get('firebase-functions-codebase') == 'python_codebase']
    require(managed, 'deployed backend inventory')
    for item in managed:
        service = item.get('serviceConfig', {}).get('service', '').rsplit('/', 1)[-1]
        require(re.fullmatch(NAME, service), 'managed backend service')
        state = service_state(manifest, service, cloud=cloud)
        require(state['traffic'], 'active backend revision')
        for revision in state['traffic']:
            data = json.loads(cloud(manifest, 'run', 'revisions', 'describe', revision, '--region', REGION,
                '--format=json'))
            require(data.get('metadata', {}).get('name') == revision, 'active immutable revision')
            # These are literal runtime configuration values, not Secret Manager
            # payloads (bound secrets use valueFrom). Keep only public stamps;
            # never persist or print the environment returned by the API.
            stamps = {row.get('name'):row.get('value') for container in data.get('spec', {}).get('containers', [])
                for row in container.get('env', []) if row.get('name') in {'MCP_RELEASE_SHA','MCP_CONFIG_DIGEST'}}
            require(stamps.get('MCP_RELEASE_SHA') == manifest['sha'] and
                stamps.get('MCP_CONFIG_DIGEST') == manifest['digest'], 'all active backend revisions must match release')


def preflight(manifest):
    metadata = github('environments/' + manifest['environment'])
    policies = github('environments/' + manifest['environment'] + '/deployment-branch-policies?per_page=100')
    require(policies.get('total_count') == 1, 'one main-only deployment branch rule')
    branches = sorted([{'name':item['name'], 'type':item['type']} for item in policies.get('branch_policies', [])], key=lambda x:x['name'])
    validate_environment(manifest['environment'], metadata, branches)
    require(command(['git', 'rev-parse', 'HEAD']).strip() == manifest['sha'], 'checkout SHA')
    require(os.environ.get('PAYMENT_ROLLOUT_APPROVED') == 'true', 'payment worker compatibility approval')
    require(os.environ.get('ROLLBACK_BASELINE_VERIFIED') == 'true', 'staging rollback proof and baseline approval')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['prepare', 'snapshot', 'deploy', 'rollback'])
    parser.add_argument('--environment', required=True, choices=['staging', 'production'])
    parser.add_argument('--snapshot-run-id')
    args = parser.parse_args()
    manifest = prepare(args.environment, os.environ)
    preflight(manifest)
    if args.operation == 'prepare':
        write_configuration(manifest)
        print('Public release configuration prepared; no cloud authentication or mutation.')
        return
    env = release_environment(manifest)
    # Auth action generated an ephemeral WIF config; the bridge validates it before CLI discovery.
    require(bool(env.get('GOOGLE_APPLICATION_CREDENTIALS')), 'ephemeral WIF credentials')
    command(['node', str(ROOT / 'scripts/deployment/firebase.cjs'), 'validate'], env=env)
    cloud_preflight(manifest)
    if args.operation == 'rollback':
        require(bool(re.fullmatch(r'[1-9][0-9]*', args.snapshot_run_id or '')), 'snapshot run ID')
        run = github('actions/runs/' + args.snapshot_run_id)
        validate_snapshot_run(run)
        destination = ROOT / '.local/release/download'
        require(not destination.exists(), 'fresh snapshot download directory')
        command(['gh', 'run', 'download', args.snapshot_run_id, '--repo', REPOSITORY,
            '--name', 'rollback-' + args.environment, '--dir', str(destination)])
        previous = json.loads((destination / 'snapshot.json').read_text())
        rollback(previous, manifest)
        print('Rollback traffic, Hosting version and health verified; application data unchanged.')
        return
    if args.operation == 'snapshot':
        previous = snapshot_release(manifest, env)
        (ROOT / '.local/release/snapshot.json').write_text(json.dumps(previous, sort_keys=True) + '\n')
        # Snapshot upload is a separate workflow step BEFORE any deploy command.
        print('Rollback baseline captured; no deployment started.')
        return
    previous = json.loads((ROOT / '.local/release/snapshot.json').read_text())
    validate_snapshot(previous, manifest)
    saved = json.loads((ROOT / '.local/release/config.json').read_text())
    require(saved == manifest, 'configuration changed since preparation')
    try:
        for target in ['backend', 'hosting']:
            print(f'Deploying scoped {target} release.', flush=True)
            command(['node', str(ROOT / 'scripts/deployment/firebase.cjs'), target], env=env)
        verify_function_releases(manifest)
        smoke(manifest)
    except Exception:
        print('Release failed; restoring the captured revisions and Hosting version.', flush=True)
        try:
            rollback(previous, manifest)
        except Exception:
            raise ValueError('Release failed and rollback is incomplete: owner intervention required.') from None
        raise ValueError('Release failed; previous release restored and verified.') from None
    print('Release identity, all backend stamps and read-only smoke verified.')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # No arbitrary SDK/API errors, URLs with auth parameters or credential values in logs.
        print(str(error) if isinstance(error, ValueError) else 'Release operation failed; diagnostics withheld.', file=sys.stderr)
        sys.exit(1)
