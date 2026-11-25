#!/usr/bin/env python3
"""First staging HTTP+SSR release, explicitly operated by the owner; never a baseline bypass."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import subprocess
import tempfile

import release

ROOT = release.ROOT
require = release.require


def prepare(env, endpoints, *, environment='staging'):
    require(environment == 'staging', 'bootstrap staging only')
    require(not any(env.get(key) for key in ['CI','GITHUB_ACTIONS','FIREBASE_TOKEN',
        'GOOGLE_APPLICATION_CREDENTIALS']), 'local explicit operator authentication')
    operator = env.get('BOOTSTRAP_OPERATOR_EMAIL','')
    require(re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',operator), 'named bootstrap operator')
    manifest = release.public_configuration('staging',env,env.get('BOOTSTRAP_APPROVED_SHA',''))
    require(manifest['wif_provider'].split('/')[1] == '1005755179074', 'staging project number')
    require(endpoints and all(set(row) == {'id','kind'} and
        re.fullmatch(r'[a-z][a-z0-9_-]{0,62}',row['id']) and row['kind'] in {'http','event','schedule'}
        for row in endpoints) and len({row['id'] for row in endpoints}) == len(endpoints), 'SDK endpoint inventory')
    manifest['bootstrap'] = dict(operator=operator,endpoints=endpoints)
    return manifest


def validate_source(env, *, sha, clean, on_main, origin):
    require(re.fullmatch(release.SHA,env.get('BOOTSTRAP_APPROVED_SHA','')) and
        sha == env['BOOTSTRAP_APPROVED_SHA'] and clean and on_main, 'approved clean main checkout')
    require(origin in {'git@github.com:Vittorix99/mcp-website.git',
        'https://github.com/Vittorix99/mcp-website.git','https://github.com/Vittorix99/mcp-website'}, 'repository origin')


def source_check(env):
    command = release.command
    sha = command(['git','rev-parse','HEAD']).strip()
    # Fails closed if origin/main does not exist or the SHA is not integrated.
    command(['git','merge-base','--is-ancestor',sha,'origin/main'])
    validate_source(env,sha=sha,clean=not command(['git','status','--porcelain','--untracked-files=normal']).strip(),
        on_main=True,origin=command(['git','remote','get-url','origin']).strip())


def discover_endpoints():
    """Inspect SDK decorators in a demo environment; block every socket connection."""
    sys.path.insert(0,str(ROOT / 'scripts'))
    from lib.runtime_guard import command_environment
    _, env = command_environment('test-unit',{})
    code = '''import json,socket
socket.socket.connect=lambda *a,**k: (_ for _ in ()).throw(RuntimeError("Offline SDK discovery"))
from firebase_functions.private.serving import get_functions
rows=[]
for name,fn in get_functions().items():
 e=fn.__firebase_endpoint__
 kinds=[kind for field,kind in [("httpsTrigger","http"),("eventTrigger","event"),("scheduleTrigger","schedule")] if getattr(e,field,None) is not None]
 if len(kinds)!=1: raise ValueError("Unsupported bootstrap endpoint")
 rows.append(dict(id=name,kind=kinds[0]))
print("MCP_ENDPOINTS="+json.dumps(sorted(rows,key=lambda r:r["id"])))
'''
    output = release.command([str(ROOT / '.venv/bin/python'),'-c',code],
        cwd=ROOT / 'mcp-backend/functions',env=env)
    rows = [line.removeprefix('MCP_ENDPOINTS=') for line in output.splitlines() if line.startswith('MCP_ENDPOINTS=')]
    require(len(rows) == 1, 'offline SDK discovery result')
    return json.loads(rows[0])


def operator_environment(env):
    return {**{key:env[key] for key in ['HOME','PATH','TMPDIR','LANG'] if env.get(key)},
        'CLOUDSDK_CORE_DISABLE_PROMPTS':'1'}


def metadata_command(args, *, env):
    # gcloud can return exit zero with unreachable-region warnings. Never call
    # such an inventory complete. Keep diagnostics private, including on error.
    result = subprocess.run(args,cwd=ROOT,env=env,capture_output=True,text=True)
    require(result.returncode == 0 and not result.stderr.strip(), 'complete operator metadata command (diagnostics withheld)')
    return result.stdout


def validate_artifact_retention(repository, name):
    require(repository.get('name') == name and
        repository.get('labels',{}).get('firebase-functions-cleanup-opted-out') == 'true' and
        all(policy.get('action') != 'DELETE' for policy in repository.get('cleanupPolicies',{}).values()),
        'preconfigured artifact retention opt-out; no automatic image deletion during bootstrap')


def operator_cloud(env):
    safe = operator_environment(env)
    operator = env['BOOTSTRAP_OPERATOR_EMAIL']
    config = json.loads(release.command(['gcloud','config','list','--format=json'],env=safe))
    require(config.get('core',{}).get('account') == operator, 'active gcloud operator')
    require(not any(config.get('auth',{}).get(key) for key in
        ['impersonate_service_account','access_token_file','credential_file_override']) and
        not any(config.get('api_endpoint_overrides',{}).values()), 'unmodified operator authentication and API endpoints')
    def cloud(manifest,*args):
        inventory = args[:2] == ('functions','list') or args[:3] == ('run','services','list')
        runner = metadata_command if inventory else release.command
        return runner(['gcloud',*args,'--project',manifest['project'],
            '--account',operator,'--quiet'],env=safe)
    return cloud


def validate_empty_inventory(functions, services, hosting):
    require(isinstance(functions,list) and not functions and isinstance(services,list) and not services and
        isinstance(hosting,dict) and not hosting.get('releases') and not hosting.get('nextPageToken'),
        'empty initial cloud inventory; partial bootstrap requires owner investigation')


def initial_inventory(manifest, cloud):
    # Explicit all-region Functions; managed Run global list ignores configured region.
    functions = json.loads(cloud(manifest,'functions','list','--regions=-','--format=json(name)'))
    services = json.loads(cloud(manifest,'run','services','list','--platform=managed','--format=json(metadata.name)'))
    hosting = release.hosting(manifest,'/releases?pageSize=1',cloud=cloud)
    validate_empty_inventory(functions,services,hosting)


def verify_deployed(manifest, cloud, *, hosting=False, web=None):
    rows = json.loads(cloud(manifest,'functions','list','--regions=-',
        '--format=json(name,labels,buildConfig.serviceAccount,serviceConfig.serviceAccountEmail)'))
    python = [row for row in rows if row.get('labels',{}).get('firebase-functions-codebase') == 'python_codebase']
    expected = {row['id'] for row in manifest['bootstrap']['endpoints'] if row['kind'] == 'http'}
    require({row['name'].rsplit('/',1)[-1] for row in python} == expected, 'exact initial HTTP inventory')
    site = [row for row in rows if row.get('labels',{}).get('firebase-functions-codebase') == 'firebase-frameworks-' + manifest['project']]
    require(len(site) == (int(hosting) if web is None else web) and len(rows) == len(python)+len(site), 'initial SSR inventory')
    for row in rows:
        require(row['name'].startswith('projects/'+manifest['project']+'/locations/us-central1/functions/'), 'deployed project and region')
        require(row.get('buildConfig',{}).get('serviceAccount') == 'projects/'+manifest['project']+'/serviceAccounts/'+manifest['identities']['BUILD_SERVICE_ACCOUNT'], 'deployed build identity')
        runtime = 'RUNTIME_SERVICE_ACCOUNT' if row in python else 'WEB_RUNTIME_SERVICE_ACCOUNT'
        require(row.get('serviceConfig',{}).get('serviceAccountEmail') == manifest['identities'][runtime], 'deployed runtime identity')
    release.verify_function_releases(manifest,cloud=cloud)
    if hosting:
        release.smoke(manifest, site_sha=manifest['sha'])


def apply(manifest, env):
    require(env.get('BOOTSTRAP_CLOUD_APPROVED') == 'true' and env.get('BOOTSTRAP_DATA_REVIEWED') == 'true',
        'separate cloud and existing-data approvals')
    # Rebuild public configuration instead of trusting editable local plan artifacts.
    clean_env = {key:value for key,value in env.items() if key != 'GOOGLE_APPLICATION_CREDENTIALS'}
    require(manifest == prepare(clean_env,discover_endpoints()), 'unchanged bootstrap plan')
    source_check(env)
    credential = env.get('BOOTSTRAP_OPERATOR_ADC','')
    require(Path(credential).is_absolute(), 'explicit private operator ADC path')
    cloud = operator_cloud(env)
    release.cloud_preflight(manifest,cloud=cloud)
    repository = json.loads(cloud(manifest,'artifacts','repositories','describe','gcf-artifacts',
        '--location',release.REGION,'--format=json(name,labels,cleanupPolicies)'))
    validate_artifact_retention(repository,'projects/'+manifest['project']+'/locations/'+release.REGION+'/repositories/gcf-artifacts')
    initial_inventory(manifest,cloud)
    release.write_configuration(manifest)
    scratch = ROOT / '.local/release'
    base = operator_environment(env)
    base.update({key:env[key] for key in ['BOOTSTRAP_OPERATOR_EMAIL','BOOTSTRAP_APPROVED_SHA',
        'BOOTSTRAP_CLOUD_APPROVED','BOOTSTRAP_DATA_REVIEWED']})
    base.update(BOOTSTRAP_OPERATOR_ADC=credential,GOOGLE_APPLICATION_CREDENTIALS=credential,
        MCP_RELEASE_CONFIG=str(scratch / 'config.json'),GCLOUD_PROJECT=manifest['project'],
        GOOGLE_CLOUD_PROJECT=manifest['project'],FIREBASE_CLI_EXPERIMENTS='webframeworks',
        NEXT_TELEMETRY_DISABLED='1',FIREBASE_CLI_DISABLE_UPDATE_CHECK='1')
    def firebase(target):
        # A different empty configstore per process prevents cached Firebase login overriding ADC.
        with tempfile.TemporaryDirectory(prefix='operator-',dir=scratch) as profile:
            release.command(['node',str(ROOT / 'scripts/deployment/firebase-bootstrap.cjs'),target],
                env={**base,'XDG_CONFIG_HOME':profile})
    firebase('validate')
    result = dict(schema=1,project=manifest['project'],sha=manifest['sha'],components=manifest['components'],status='started')
    record = scratch / 'bootstrap-result.json'
    record.write_text(json.dumps(result)+'\n')
    try:
        firebase('backend')
        verify_deployed(manifest,cloud)
        firebase('hosting')
        verify_deployed(manifest,cloud,hosting=True)
    except Exception:
        result['status'] = 'incomplete-owner-investigation-required'
        record.write_text(json.dumps(result)+'\n')
        raise ValueError('Bootstrap stopped; inspect public result and cloud inventory; no automatic rollback or retry') from None
    result['status'] = 'http-ssr-verified-not-full-rollback-baseline'
    record.write_text(json.dumps(result)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['prepare','apply'])
    parser.add_argument('--environment',choices=['staging','production'],default='staging')
    args = parser.parse_args()
    manifest = prepare(os.environ,discover_endpoints(),environment=args.environment)
    source_check(os.environ)
    # Validate against the real pinned CLI selector, without authenticating or deploying.
    result = subprocess.run(['node',str(ROOT / 'scripts/deployment/firebase-bootstrap.cjs'),'selectors'],
        cwd=ROOT,env=operator_environment(os.environ),input=json.dumps(manifest['bootstrap']['endpoints']),
        text=True,capture_output=True)
    require(result.returncode == 0, 'exact pinned CLI HTTP selector')
    plan = ROOT / '.local/release/bootstrap-plan.json'
    if args.operation == 'prepare':
        plan.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        plan.write_text(json.dumps(manifest,sort_keys=True)+'\n')
        print('Public staging bootstrap plan prepared offline; no cloud authentication or deployment.')
    else:
        require(json.loads(plan.read_text()) == manifest, 'approved prepared bootstrap plan')
        apply(manifest,os.environ)
        print('Initial HTTP and SSR verified; triggers, scheduled jobs, data update and full rollback baseline remain separate.')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('Guarded staging bootstrap failed; diagnostics withheld.',file=sys.stderr)
        sys.exit(1)
