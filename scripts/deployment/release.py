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


class ValidationFailure(ValueError):
    """Only validation labels owned by this module may be shown in diagnostics."""
    def __init__(self, field):
        self.field = field
        super().__init__(f'Release validation failed: {field}')


class CommandFailure(ValueError):
    def __init__(self, metadata):
        self.metadata = metadata
        super().__init__('Release child command failed: ' + json.dumps(metadata, sort_keys=True))


def failure_metadata(error):
    if isinstance(error, CommandFailure):
        return error.metadata
    if isinstance(error, ValidationFailure):
        return {'category': 'validation', 'validation': error.field}
    if isinstance(error, HTTPError):
        return {'category': 'http', 'http_status': error.code}
    public_failures = {
        'Release failed and rollback is incomplete: owner intervention required.': 'rollback-incomplete',
        'Release failed; previous release restored and verified.': 'deployment-failed-restored',
    }
    if type(error) is ValueError and str(error) in public_failures:
        return {'category': public_failures[str(error)]}
    kind = type(error).__name__
    return {'category': 'unexpected', 'error_type': kind if kind in {
        'ValueError', 'RuntimeError', 'TypeError', 'KeyError', 'JSONDecodeError',
        'OSError', 'FileNotFoundError', 'TimeoutError'} else 'unknown'}


def report_failure(stage, error):
    print(json.dumps({'event': 'release_failure', 'stage': stage, **failure_metadata(error)},
        sort_keys=True), file=sys.stderr, flush=True)


def progress(stage, **counts):
    print(json.dumps({'event': 'release_progress', 'stage': stage, **counts}, sort_keys=True), flush=True)


def require(condition, field):
    if not condition:
        raise ValidationFailure(field)


def public_value(env, key):
    value = env.get(key, '')
    require(isinstance(value, str) and 0 < len(value) <= 2048 and
        not any(ord(c) < 32 or c in '\"\\' for c in value), key)
    return value


def git_object(sha, path):
    value = command(['git', 'rev-parse', f'{sha}:{path}']).strip()
    require(re.fullmatch(SHA, value), 'component source identity')
    return value


def component_trees(sha):
    """Source identity per component: stable while that component's files are unchanged."""
    backend = git_object(sha, 'mcp-backend/functions')
    site = hashlib.sha256(f"{git_object(sha, 'mcp-website')}:{git_object(sha, 'firebase.json')}".encode()).hexdigest()
    return backend, site


def prepare(environment, env):
    require(environment in {'staging', 'production'}, 'environment')
    require(env.get('GITHUB_REPOSITORY') == REPOSITORY and
        str(env.get('GITHUB_REPOSITORY_ID')) == str(REPOSITORY_ID), 'repository identity')
    require(env.get('GITHUB_REF') == 'refs/heads/main', 'main ref')
    require(env.get('GITHUB_WORKFLOW_REF') == f'{REPOSITORY}/{WORKFLOW}@refs/heads/main', 'workflow identity')
    require(env.get('GITHUB_EVENT_NAME') in {'push', 'workflow_dispatch'}, 'trusted event')
    sha = env.get('GITHUB_SHA', '')
    return public_configuration(environment, env, sha)


def public_configuration(environment, env, sha, trees=None):
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
    backend_tree, site_tree = trees or component_trees(sha)

    def digest(**values):
        return hashlib.sha256(json.dumps(values, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    # Each digest covers only that component's public configuration, never the commit:
    # an unrelated commit must not change a component's identity.
    backend_digest = digest(backend=backend, build_account=identities['BUILD_SERVICE_ACCOUNT'])
    site_digest = digest(frontend=frontend, web_runtime=identities['WEB_RUNTIME_SERVICE_ACCOUNT'],
        build_account=identities['BUILD_SERVICE_ACCOUNT'])
    backend.update(MCP_BACKEND_TREE=backend_tree, MCP_CONFIG_DIGEST=backend_digest)
    # The commit stays in the site stamps as provenance only; identity is tree + digest.
    frontend.update(NEXT_PUBLIC_RELEASE_SHA=sha, NEXT_PUBLIC_SITE_TREE=site_tree,
        NEXT_PUBLIC_CONFIGURATION_DIGEST=site_digest)
    return dict(schema=2, environment=environment, project=project, sha=sha,
        components=dict(backend=dict(tree=backend_tree, digest=backend_digest),
                        site=dict(tree=site_tree, digest=site_digest)),
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


def validate_health(health, manifest, component, *, sha=None):
    """Exact identity of one component; the site commit is checked only when the caller expects it."""
    identity = manifest['components'][component]
    expected = dict(status='ok', environment=manifest['environment'], project_id=manifest['project'],
        configuration_digest=identity['digest'])
    health = dict(health) if isinstance(health, dict) else {}
    if component == 'backend':
        expected['backend_tree'] = identity['tree']
    else:
        expected['site_tree'] = identity['tree']
        commit = health.pop('release_sha', '')
        require(bool(re.fullmatch(SHA, commit or '')) and (sha is None or commit == sha), 'site release commit')
    require(health == expected, 'deployed release identity')


HEALTH_URLS = {'backend': 'https://us-central1-{project}.cloudfunctions.net/deployment_health',
               'site': 'https://{project}.web.app/api/deployment-health'}


def read_live(manifest):
    return {component: fetch_json(url.format(project=manifest['project'])) for component, url in HEALTH_URLS.items()}


def plan_release(manifest, live):
    """Which components differ from what is live. Unreadable live state never means "deploy"."""
    changed = {}
    for component, tree_key in (('backend', 'backend_tree'), ('site', 'site_tree')):
        health = live.get(component)
        require(isinstance(health, dict) and health.get('status') == 'ok' and
            health.get('environment') == manifest['environment'] and
            health.get('project_id') == manifest['project'], f'live {component} identity readable')
        want = manifest['components'][component]
        changed[component] = not (health.get(tree_key) == want['tree'] and
            health.get('configuration_digest') == want['digest'])
    return changed


def validate_snapshot(snapshot, manifest):
    require(snapshot.get('schema') == 2 and snapshot.get('project') == manifest['project'] and
        snapshot.get('environment') == manifest['environment'], 'snapshot environment')
    components = snapshot.get('components', {})
    require(re.fullmatch(SHA, snapshot.get('sha', '')) and
        re.fullmatch(SHA, components.get('backend', {}).get('tree', '')) and
        re.fullmatch(DIGEST, components.get('backend', {}).get('digest', '')) and
        re.fullmatch(DIGEST, components.get('site', {}).get('tree', '')) and
        re.fullmatch(DIGEST, components.get('site', {}).get('digest', '')), 'snapshot version stamps')
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
    started = time.monotonic()
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True)
    # Do not echo CLI stdout/stderr: SDK diagnostics can include environment or credentials.
    if result.returncode != 0:
        name = Path(args[0]).name
        tool = name if name in {'gcloud', 'gh', 'node', 'git'} else 'child'
        if re.fullmatch(r'python(?:[0-9.]+)?', name):
            tool = 'python'
        operation = tool
        prefixes = {
            'gcloud': [('run', 'services', 'update-traffic'), ('run', 'services', 'describe'),
                ('run', 'revisions', 'describe'), ('functions', 'list'), ('secrets', 'versions', 'describe'),
                ('secrets', 'get-iam-policy'), ('projects', 'describe'), ('auth', 'print-access-token')],
            'gh': [('api',), ('run', 'download')],
            'git': [('rev-parse',), ('merge-base',), ('diff',)],
        }
        for prefix in prefixes.get(tool, []):
            if tuple(args[1:1 + len(prefix)]) == prefix:
                operation += '.' + '.'.join(prefix)
                break
        if tool == 'node' and len(args) == 3 and args[1] == str(ROOT / 'scripts/deployment/firebase.cjs') and args[2] in {'hosting', 'backend', 'probe', 'validate'}:
            operation = 'firebase.' + args[2]
        output = (result.stdout + '\n' + result.stderr).lower()
        category = next((category for category, markers in [
            ('permission-denied', ('permission_denied', 'permission denied', 'missing permissions')),
            ('authentication', ('unauthenticated', 'failed to authenticate', 'invalid_grant', 'expired token')),
            ('build', ('release build failed', 'build failed')),
            ('network', ('enotfound', 'econnreset', 'etimedout', 'timed out')),
        ] if any(marker in output for marker in markers)), 'unclassified')
        metadata = {'operation': operation, 'exit_code': result.returncode, 'category': category,
            'elapsed_seconds': round(time.monotonic() - started, 3)}
        status = re.findall(r'RELEASE_SDK_STATUS=(4[0-9]{2}|5[0-9]{2})', result.stderr)
        if status:
            metadata['sdk_status'] = int(status[-1])
        targets = re.findall(r'RELEASE_API_TARGET=([a-z0-9-]+\.googleapis\.com/[A-Za-z0-9/*:._-]{0,160})(?:\s|$)', result.stderr)
        if targets:
            metadata['api_target'] = targets[-1]
        kinds = re.findall(r'RELEASE_ERROR_TYPE=(Error|FirebaseError|TypeError|SyntaxError|RangeError|unknown)\b', result.stderr)
        if kinds:
            metadata['error_type'] = kinds[-1]
        phases = re.findall(r'RELEASE_PROBE_PHASE=(firebase-auth|hosting-read|web-config|admin-config|project-permissions|account-actas)', result.stderr)
        if phases:
            metadata['probe_phase'] = phases[-1]
        roles = re.findall(r'RELEASE_ACCOUNT_ROLE=(BUILD_SERVICE_ACCOUNT|RUNTIME_SERVICE_ACCOUNT|WEB_RUNTIME_SERVICE_ACCOUNT)\b', result.stderr)
        if roles:
            metadata['account_role'] = roles[-1]
        missing = re.findall(r'RELEASE_MISSING_PERMISSION=(run\.services\.(?:get|update)|firebasehosting\.sites\.(?:get|update)|cloudfunctions\.functions\.(?:get|update)|iam\.serviceAccounts\.actAs|apikeys\.keys\.getKeyString)\b', result.stderr)
        if missing:
            metadata['missing_permissions'] = sorted(set(missing))
        raise CommandFailure(metadata)
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


# Hosting pins each version to a Cloud Run revision tag and a new release can take minutes to reach every edge.
HEALTH_ATTEMPTS = 24
HEALTH_DELAY_SECONDS = 10


def smoke(manifest, *, site_sha=None):
    project = manifest['project']
    for component, url in HEALTH_URLS.items():
        url = url.format(project=project)
        # Bounded retry handles propagation; mismatch is never reported as success.
        observed = None
        for attempt in range(HEALTH_ATTEMPTS):
            try:
                health = fetch_json(url)
                commit = health.get('release_sha') if isinstance(health, dict) else None
                observed = commit if isinstance(commit, str) and re.fullmatch(SHA, commit) else None
                validate_health(health, manifest, component, sha=site_sha if component == 'site' else None)
                break
            except Exception as error:
                if attempt == HEALTH_ATTEMPTS - 1:
                    # Only labels owned by this module plus the public commit the site reports are surfaced.
                    if isinstance(error, ValidationFailure):
                        detail = f' (observed {observed[:12]})' if observed and component == 'site' else ''
                        raise ValidationFailure(f'{component} health: {error.field}{detail}') from None
                    raise ValueError('Release health check failed') from None
                time.sleep(HEALTH_DELAY_SECONDS)
    for endpoint in ['get_all_events', 'get_next_event', 'get_membership_price_public',
                     'get_published_radio_episodes', 'get_latest_radio_episode', 'get_radio_seasons']:
        try:
            fetch_json(f'https://us-central1-{project}.cloudfunctions.net/{endpoint}')
        except HTTPError as error:
            # An environment without radio episodes is valid; any other failure is not.
            if not (endpoint in EMPTY_STATE_ENDPOINTS and error.code == 404):
                raise


def expected_functions(manifest, env):
    if manifest['environment'] == 'production':
        result = command([str(ROOT / '.venv/bin/python'), '-c',
            'import json; from firebase_functions.private.serving import get_functions; '
            'print(json.dumps(sorted(get_functions())))'], cwd=ROOT / 'mcp-backend/functions',
            env={**env, **manifest['backend'], 'ADMIN_PORT':'8087'})
        return json.loads(result)
    # Bootstrap and migration intentionally provision only HTTP endpoints on staging.
    # Use the same socket-blocked SDK inventory for snapshot and CLI selection.
    result = command([str(ROOT / '.venv/bin/python'), '-c',
        'import json; from bootstrap_staging import discover_endpoints; print(json.dumps(discover_endpoints()))'],
        cwd=ROOT / 'scripts/deployment')
    endpoints = json.loads(result)
    return sorted(row['id'] for row in endpoints if row['kind'] == 'http')


def snapshot_release(manifest, env):
    progress('snapshot.inventory')
    live = read_live(manifest)
    backend, site = live['backend'], live['site']
    # The previous site commit is the topology baseline: every release leaves both components
    # matching its commit, and topology changes never go through the automatic path.
    old = {**manifest, 'sha':site.get('release_sha'), 'components':dict(
        backend=dict(tree=backend.get('backend_tree'), digest=backend.get('configuration_digest')),
        site=dict(tree=site.get('site_tree'), digest=site.get('configuration_digest')))}
    require(bool(re.fullmatch(SHA, old['sha'] or '')), 'previous site commit')
    validate_health(backend, old, 'backend')
    validate_health(site, old, 'site', sha=old['sha'])
    verify_topology(old['sha'])
    records = cloud_functions(manifest)
    functions = sorted(item['name'].rsplit('/', 1)[-1] for item in records
        if item.get('labels', {}).get('firebase-functions-codebase') == 'python_codebase')
    require(functions == expected_functions(manifest, env),
        'function inventory changed: controlled baseline required before automatic release')
    require(any(item.get('labels', {}).get('firebase-functions-codebase') ==
        'firebase-frameworks-' + manifest['project'] for item in records), 'SSR rollback target')
    progress('snapshot.revisions')
    verify_function_releases(old)
    smoke(old, site_sha=old['sha'])
    services = {}
    references = set()
    progress('snapshot.capture', total=len(records))
    for item in records:
        service = item.get('serviceConfig', {}).get('service', '').rsplit('/', 1)[-1]
        require(re.fullmatch(NAME, service), 'managed Cloud Run service')
        services[service] = service_state(manifest, service)
        for revision in services[service]['traffic']:
            references.update(verify_revision_secrets(manifest, revision))
    releases = hosting(manifest, '/releases?pageSize=1').get('releases', [])
    # A restored release is published as type ROLLBACK; it is as live and finalized as a DEPLOY, so a release
    # that follows a successful automatic restore can still be snapshotted. SITE_DISABLE and others are refused.
    require(len(releases) == 1 and releases[0].get('type') in {'DEPLOY', 'ROLLBACK'}, 'previous Hosting release')
    snapshot = dict(schema=2, environment=manifest['environment'], project=manifest['project'],
        sha=old['sha'], components=old['components'], functions=functions, services=services,
        secrets=[dict(secret=name,version=version) for name,version in sorted(references)],
        hosting_version=releases[0]['version']['name'])
    validate_snapshot(snapshot, manifest)
    verify_secret_versions(snapshot, manifest)
    return snapshot


def rollback(snapshot, manifest):
    progress('rollback.validate')
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
    progress('rollback.traffic', total=len(snapshot['services']))
    for index, (service, state) in enumerate(snapshot['services'].items(), 1):
        target = ','.join(f'{revision}={percent}' for revision, percent in sorted(state['traffic'].items()))
        gcloud(manifest, 'run', 'services', 'update-traffic', service, '--region', REGION, '--to-revisions', target)
        if index % 25 == 0 or index == len(snapshot['services']):
            progress('rollback.traffic', completed=index, total=len(snapshot['services']))
    progress('rollback.hosting')
    # Hosting rejects republishing the version that is already active. This is
    # normal for backend-only rollback or a deploy that failed before publication.
    if active_hosting_version(manifest) != snapshot['hosting_version']:
        hosting(manifest, '/releases', version=snapshot['hosting_version'])
    else:
        progress('rollback.hosting-already-active')
    progress('rollback.readback')
    for service, state in snapshot['services'].items():
        require(service_state(manifest, service) == state, 'restored revision traffic')
    require(active_hosting_version(manifest) == snapshot['hosting_version'], 'restored Hosting version')
    smoke({**manifest, 'sha':snapshot['sha'], 'components':snapshot['components']}, site_sha=snapshot['sha'])
    progress('rollback.verified')


def active_hosting_version(manifest):
    releases = hosting(manifest, '/releases?pageSize=1').get('releases', [])
    require(len(releases) == 1, 'active Hosting release readable')
    release = releases[0]
    if release.get('type') == 'SITE_DISABLE':
        return None
    version = release.get('version', {}).get('name')
    require(bool(re.fullmatch('sites/' + re.escape(manifest['project']) + r'/versions/[a-zA-Z0-9-]+', version or '')),
        'active Hosting version readable')
    return version


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


def provider_secrets(manifest):
    return [secret for provider, secret in [
        ('PAYPAL', 'PAYPAL_CLIENT_SECRET'), ('MAIL', 'MAILERSEND_API_KEY'),
        ('PASS2U', 'PASS2U_API_KEY'), ('SOUNDCLOUD', 'SOUNDCLOUD_CLIENT_SECRET'),
        ('GENDER', 'GENDER_API_KEY')]
        if manifest['backend'].get(provider + '_MODE') in {'sandbox', 'staging', 'live'}]


def stale_secret_versions(manifest):
    """Secrets whose newest version is not what an active backend revision is pinned to.

    Functions bind a numeric secret version at deploy time, and the backend identity ignores
    secret versions, so a rotation alone would never reach an unchanged backend.
    """
    latest = {}
    for secret in provider_secrets(manifest):
        name = gcloud(manifest, 'secrets', 'versions', 'describe', 'latest', '--secret', secret,
            '--format=value(name)').strip()
        latest[secret] = name.rsplit('/', 1)[-1]
    services = {item.get('serviceConfig', {}).get('service', '').rsplit('/', 1)[-1]
        for item in cloud_functions(manifest)
        if item.get('labels', {}).get('firebase-functions-codebase') == 'python_codebase'}
    stale = set()
    for service in sorted(services):
        for revision in service_state(manifest, service)['traffic']:
            stale.update(secret for secret, version in verify_revision_secrets(manifest, revision)
                if secret in latest and version != latest[secret])
    return sorted(stale)


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
    for secret in provider_secrets(manifest):
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
                for row in container.get('env', []) if row.get('name') in {'MCP_BACKEND_TREE','MCP_CONFIG_DIGEST'}}
            backend = manifest['components']['backend']
            require(stamps.get('MCP_BACKEND_TREE') == backend['tree'] and
                stamps.get('MCP_CONFIG_DIGEST') == backend['digest'], 'all active backend revisions must match release')


def serve_latest_revisions(manifest, targets, *, cloud=None):
    """Point the deployed components' services at their newest revision.

    A deploy creates a revision, but a service whose traffic was pinned to a named revision (every restore does
    that) keeps serving it, so the new release would never go live. Already-latest services are left untouched."""
    cloud = cloud or gcloud
    codebases = {{'backend': 'python_codebase', 'hosting': 'firebase-frameworks-' + manifest['project']}[target]
        for target in targets}
    services = sorted({item.get('serviceConfig', {}).get('service', '').rsplit('/', 1)[-1]
        for item in cloud_functions(manifest, cloud=cloud)
        if item.get('labels', {}).get('firebase-functions-codebase') in codebases})
    progress('deploy.traffic', total=len(services))
    for index, service in enumerate(services, 1):
        require(re.fullmatch(NAME, service), 'deployed Cloud Run service')
        data = json.loads(cloud(manifest, 'run', 'services', 'describe', service, '--region', REGION,
            '--format=json(spec.traffic)'))
        if not any(row.get('latestRevision') is True and row.get('percent') == 100
                   for row in data.get('spec', {}).get('traffic', [])):
            cloud(manifest, 'run', 'services', 'update-traffic', service, '--region', REGION, '--to-latest')
        if index % 25 == 0 or index == len(services):
            progress('deploy.traffic', completed=index, total=len(services))


def execute_release(manifest, env, changed):
    """Deploy only the components whose live identity differs, then verify every component."""
    targets = [target for target, component in (('backend', 'backend'), ('hosting', 'site')) if changed[component]]
    print('Release plan: ' + (', '.join(targets) if targets else 'nothing changed, no deployment') + '.', flush=True)
    for target in targets:
        # Hosting pins the new version to the service's latest revision when it releases, and a service pinned to a
        # named revision by an earlier restore does not advance: route to latest before the deploy, not only after.
        serve_latest_revisions(manifest, [target])
        print(f'Deploying scoped {target} release.', flush=True)
        command(['node', str(ROOT / 'scripts/deployment/firebase.cjs'), target], env=env)
    if targets:
        serve_latest_revisions(manifest, targets)
    verify_function_releases(manifest)
    smoke(manifest, site_sha=manifest['sha'] if changed['site'] else None)
    return targets


def write_release_manifest(manifest, changed, deployed):
    """What went live and what was skipped; public identities only."""
    record = dict(schema=1, environment=manifest['environment'], project=manifest['project'], commit=manifest['sha'],
        components=manifest['components'], deployed=deployed,
        skipped=[name for name in ('backend', 'hosting') if name not in deployed])
    (ROOT / '.local/release').mkdir(parents=True, exist_ok=True, mode=0o700)
    (ROOT / '.local/release' / f"release-{manifest['environment']}.json").write_text(
        json.dumps(record, sort_keys=True, indent=2) + '\n')


def preflight(manifest, *, read_only=False):
    metadata = github('environments/' + manifest['environment'])
    policies = github('environments/' + manifest['environment'] + '/deployment-branch-policies?per_page=100')
    require(policies.get('total_count') == 1, 'one main-only deployment branch rule')
    branches = sorted([{'name':item['name'], 'type':item['type']} for item in policies.get('branch_policies', [])], key=lambda x:x['name'])
    validate_environment(manifest['environment'], metadata, branches)
    require(command(['git', 'rev-parse', 'HEAD']).strip() == manifest['sha'], 'checkout SHA')
    if read_only:
        # Approvals gate mutations only; a read-only access proof must work before they are granted.
        return
    require(os.environ.get('PAYMENT_ROLLOUT_APPROVED') == 'true', 'payment worker compatibility approval')
    # The first real rollback cannot already have a verified baseline. Permit only
    # owner-approved manual staging proofs; production always needs the baseline.
    staging_proof = (manifest['environment'] == 'staging' and
        os.environ.get('GITHUB_EVENT_NAME') == 'workflow_dispatch' and
        os.environ.get('STAGING_RELEASE_PROOF_APPROVED') == 'true')
    require(os.environ.get('ROLLBACK_BASELINE_VERIFIED') == 'true' or staging_proof,
        'staging rollback proof and baseline approval')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['prepare', 'plan', 'verify', 'snapshot', 'deploy', 'rollback'])
    parser.add_argument('--environment', required=True, choices=['staging', 'production'])
    parser.add_argument('--snapshot-run-id')
    parser.add_argument('--read-only', action='store_true')
    args = parser.parse_args()
    # verify only reads; --read-only exists solely so the shared prepare step can skip mutation approvals.
    require(args.operation in {'verify', 'plan'} or not args.read_only or args.operation == 'prepare', 'read-only scope')
    read_only = args.operation in {'verify', 'plan'} or args.read_only
    manifest = prepare(args.environment, os.environ)
    preflight(manifest, read_only=read_only)
    if args.operation == 'prepare':
        write_configuration(manifest)
        print('Public release configuration prepared; no cloud authentication or mutation.')
        return
    if args.operation == 'plan':
        # Public health endpoints only: no credentials, no cloud mutation.
        print(json.dumps(plan_release(manifest, read_live(manifest)), sort_keys=True))
        return
    env = release_environment(manifest)
    # Auth action generated an ephemeral WIF config; the bridge validates it before CLI discovery.
    require(bool(env.get('GOOGLE_APPLICATION_CREDENTIALS')), 'ephemeral WIF credentials')
    command(['node', str(ROOT / 'scripts/deployment/firebase.cjs'), 'validate'], env=env)
    cloud_preflight(manifest)
    if args.operation == 'verify':
        # Identity and read access only: no snapshot, deployment, traffic or data change.
        result = command(['node', str(ROOT / 'scripts/deployment/firebase.cjs'), 'probe'], env=env)
        probe = json.loads(result.strip().splitlines()[-1])
        require(probe == dict(mode='read-only', firebase_auth=True, hosting_read=True,
            web_config_read=True, admin_config_read=True, project_permissions=True, account_actas=True), 'read-only probe result')
        print(json.dumps(probe, sort_keys=True), flush=True)
        print('Federated access verified: project, bucket, APIs, service identities and provider secret versions readable; '
              f'{len(cloud_functions(manifest))} functions listed; nothing deployed or changed.')
        return
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
    # Fail closed: without a readable live identity there is no basis to skip or deploy anything.
    changed = plan_release(manifest, read_live(manifest))
    if not changed['backend']:
        progress('deploy.secret-version-check')
        stale = stale_secret_versions(manifest)
        if stale:
            # Names only; never the values or versions.
            print('Backend secret versions are stale (' + ', '.join(stale) + '); the backend will be updated.', flush=True)
            changed['backend'] = True
    try:
        targets = execute_release(manifest, env, changed)
    except Exception as deployment_error:
        report_failure('deploy', deployment_error)
        print('Release failed; restoring the captured revisions and Hosting version.', flush=True)
        try:
            rollback(previous, manifest)
        except Exception as rollback_error:
            report_failure('rollback', rollback_error)
            raise ValueError('Release failed and rollback is incomplete: owner intervention required.') from None
        raise ValueError('Release failed; previous release restored and verified.') from None
    write_release_manifest(manifest, changed, targets)
    print('Release identity, all backend stamps and read-only smoke verified.')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # No arbitrary SDK/API errors, URLs with auth parameters or credential values in logs.
        report_failure('operation', error)
        print('Release operation failed; arbitrary diagnostics withheld.', file=sys.stderr)
        sys.exit(1)
