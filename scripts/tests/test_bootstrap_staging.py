"""Offline bootstrap boundaries; no owner credentials or provider calls."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest
from test_deployment_release import inputs

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/deployment'))
spec = importlib.util.spec_from_file_location('bootstrap_staging', ROOT / 'scripts/deployment/bootstrap_staging.py')
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


def environment():
    return {**inputs(), 'WIF_PROVIDER':'projects/1005755179074/locations/global/workloadIdentityPools/github-actions/providers/main-release', 'BOOTSTRAP_APPROVED_SHA':'a' * 40,
        'BOOTSTRAP_OPERATOR_EMAIL':'owner@example.com'}


def test_prepare_is_public_only_without_forged_workflow_or_rollback_approval():
    env = {key:value for key,value in environment().items() if not key.startswith('GITHUB_')}
    endpoints = [dict(id='get_event',kind='http'),dict(id='on_member',kind='event'),dict(id='cleanup',kind='schedule')]
    manifest = bootstrap.prepare(env, endpoints)
    assert manifest['bootstrap'] == dict(operator='owner@example.com',endpoints=endpoints)
    assert manifest['sha'] == 'a' * 40
    assert 'ROLLBACK_BASELINE_VERIFIED' not in json.dumps(manifest)
    assert 'PAYMENT_ROLLOUT_APPROVED' not in json.dumps(manifest)
    for update in [dict(BOOTSTRAP_OPERATOR_EMAIL=''),dict(BOOTSTRAP_APPROVED_SHA='main'),
                   dict(CI='true'),dict(GOOGLE_APPLICATION_CREDENTIALS='/synthetic/key.json'),
                   dict(PAYPAL_CLIENT_SECRET='SENTINEL')]:
        with pytest.raises(ValueError) as error:
            bootstrap.prepare({**env,**update},endpoints)
        assert 'SENTINEL' not in str(error.value)
    with pytest.raises(ValueError):
        bootstrap.prepare(env,endpoints,environment='production')


def test_source_is_clean_exact_approved_sha_in_main_and_this_repository():
    env = environment()
    valid = dict(sha='a'*40,clean=True,on_main=True,origin='git@github.com:Vittorix99/mcp-website.git')
    bootstrap.validate_source(env,**valid)
    for update in [dict(sha='b'*40),dict(clean=False),dict(on_main=False),dict(origin='https://github.com/other/repo.git')]:
        with pytest.raises(ValueError): bootstrap.validate_source(env,**{**valid,**update})


def test_initial_inventory_refuses_partial_creations_or_unreachable_locations():
    bootstrap.validate_empty_inventory([],[],{'releases':[]})
    for functions, services, hosting in [([{'name':'old'}],[],{}),([],[{'name':'partial'}],{}),
        ([],[],{'releases':[{'name':'old'}]}),([],[],{'nextPageToken':'more'})]:
        with pytest.raises(ValueError): bootstrap.validate_empty_inventory(functions,services,hosting)


def test_operator_environment_drops_cached_auth_and_cloud_sdk_overrides():
    env = {**environment(), 'HOME':'/synthetic/home','PATH':'/synthetic/bin','FIREBASE_TOKEN':'SENTINEL',
        'CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT':'SENTINEL','NODE_OPTIONS':'SENTINEL',
        'GOOGLE_APPLICATION_CREDENTIALS':'SENTINEL','PAYPAL_CLIENT_SECRET':'SENTINEL'}
    safe = bootstrap.operator_environment(env)
    assert safe == {'HOME':'/synthetic/home','PATH':'/synthetic/bin','CLOUDSDK_CORE_DISABLE_PROMPTS':'1'}
    assert 'SENTINEL' not in json.dumps(safe)


def test_operator_gcloud_refuses_configured_impersonation_and_uses_explicit_account(monkeypatch):
    calls = []
    def command(args,**kwargs):
        calls.append((args,kwargs))
        if args[1:3] == ['config','list']:
            return json.dumps({'core':{'account':'owner@example.com'}})
        return 'metadata'
    monkeypatch.setattr(bootstrap.release,'command',command)
    cloud = bootstrap.operator_cloud(environment())
    assert cloud({'project':'mcp-website-dev-39539'},'projects','describe') == 'metadata'
    assert calls[-1][0][-5:] == ['--project','mcp-website-dev-39539','--account','owner@example.com','--quiet']
    monkeypatch.setattr(bootstrap.release,'command',lambda *args,**kwargs: json.dumps(
        {'core':{'account':'owner@example.com'},'auth':{'impersonate_service_account':'SENTINEL'}}))
    with pytest.raises(ValueError): bootstrap.operator_cloud(environment())


def test_apply_needs_separate_cloud_and_data_approval_before_any_auth(monkeypatch):
    monkeypatch.setattr(bootstrap,'operator_cloud',lambda *args: pytest.fail('Must not authenticate'))
    with pytest.raises(ValueError): bootstrap.apply({},environment())


def test_cloud_preflight_can_use_operator_runner_without_secret_payload_access(monkeypatch):
    calls = []
    manifest = bootstrap.prepare(environment(),[dict(id='get_event',kind='http')])
    def cloud(_, *args):
        calls.append(args)
        if args[:2] == ('projects','describe'): return manifest['project']
        if args[:3] == ('storage','buckets','describe'): return manifest['backend']['STORAGE_BUCKET']
        if args[:2] == ('services','list'): return '\n'.join(name+'.googleapis.com' for name in
            ['cloudfunctions','cloudbuild','run','artifactregistry','secretmanager','firebasehosting',
             'eventarc','pubsub','firestore','storage','identitytoolkit','cloudscheduler'])
        if args[:3] == ('iam','service-accounts','describe'): return args[3]
        if args[:3] == ('secrets','versions','describe'): return 'ENABLED'
        if args[:2] == ('secrets','get-iam-policy'): return json.dumps({'bindings':[
            {'role':'roles/secretmanager.secretAccessor','members':['serviceAccount:'+manifest['identities']['RUNTIME_SERVICE_ACCOUNT']]}]})
        pytest.fail('Unexpected operation')
    monkeypatch.setattr(bootstrap.release,'gcloud',lambda *args: pytest.fail('Wrong auth runner'))
    bootstrap.release.cloud_preflight(manifest,cloud=cloud)
    assert all('access' not in args and 'set-iam-policy' not in args for args in calls)


def test_real_sdk_discovery_has_exact_http_trigger_and_schedule_partition():
    from collections import Counter
    endpoints = bootstrap.discover_endpoints()
    assert Counter(row['kind'] for row in endpoints) == {'http':130,'event':8,'schedule':3}
    import subprocess
    result = subprocess.run(['node',str(ROOT/'scripts/deployment/firebase-bootstrap.cjs'),'selectors'],
        input=json.dumps(endpoints),capture_output=True,text=True)
    assert result.returncode == 0
    selected = result.stdout.strip().split(',')
    assert len(selected) == 130
    assert {item.removeprefix('functions:python_codebase:') for item in selected} == {
        row['id'] for row in endpoints if row['kind'] == 'http'}


def test_deployed_inventory_rejects_worker_extra_wrong_build_and_wrong_runtime(monkeypatch):
    manifest = bootstrap.prepare(environment(),[dict(id='get_event',kind='http'),dict(id='worker',kind='event')])
    row = dict(name=f"projects/{manifest['project']}/locations/us-central1/functions/get_event",
        labels={'firebase-functions-codebase':'python_codebase'},
        buildConfig={'serviceAccount':f"projects/{manifest['project']}/serviceAccounts/"+manifest['identities']['BUILD_SERVICE_ACCOUNT']},
        serviceConfig={'serviceAccountEmail':manifest['identities']['RUNTIME_SERVICE_ACCOUNT']})
    monkeypatch.setattr(bootstrap.release,'verify_function_releases',lambda *a,**k: None)
    bootstrap.verify_deployed(manifest,lambda *a:json.dumps([row]))
    for rows in [[row,{**row,'name':row['name'].replace('get_event','worker')}],
        [{**row,'buildConfig':{}}],[{**row,'serviceConfig':{}}],
        [{**row,'name':row['name'].replace('us-central1','europe-west1')}]]:
        with pytest.raises(ValueError): bootstrap.verify_deployed(manifest,lambda *a:json.dumps(rows))


def test_partial_apply_records_no_secrets_and_never_retries_or_rolls_back(tmp_path,monkeypatch):
    env = {**environment(),'BOOTSTRAP_CLOUD_APPROVED':'true','BOOTSTRAP_DATA_REVIEWED':'true',
        'BOOTSTRAP_OPERATOR_ADC':'/synthetic/private-adc.json'}
    endpoints = [dict(id='get_event',kind='http')]
    manifest = bootstrap.prepare(env,endpoints)
    scratch = tmp_path/'.local/release'
    scratch.mkdir(parents=True)
    monkeypatch.setattr(bootstrap,'ROOT',tmp_path)
    monkeypatch.setattr(bootstrap,'discover_endpoints',lambda:endpoints)
    monkeypatch.setattr(bootstrap,'source_check',lambda *a:None)
    monkeypatch.setattr(bootstrap,'operator_cloud',lambda *a:lambda *a:json.dumps({
        'name':f"projects/{manifest['project']}/locations/us-central1/repositories/gcf-artifacts",
        'labels':{'firebase-functions-cleanup-opted-out':'true'}}))
    monkeypatch.setattr(bootstrap,'initial_inventory',lambda *a:None)
    monkeypatch.setattr(bootstrap.release,'cloud_preflight',lambda *a,**k:None)
    monkeypatch.setattr(bootstrap.release,'write_configuration',lambda *a:None)
    calls=[]
    def command(args,**kwargs):
        calls.append(args[-1])
        assert kwargs['env']['GOOGLE_APPLICATION_CREDENTIALS'] == env['BOOTSTRAP_OPERATOR_ADC']
        assert list(Path(kwargs['env']['XDG_CONFIG_HOME']).iterdir()) == []
        if args[-1] == 'backend': raise ValueError('TOKEN-SENTINEL')
        return ''
    monkeypatch.setattr(bootstrap.release,'command',command)
    with pytest.raises(ValueError) as error: bootstrap.apply(manifest,env)
    assert 'SENTINEL' not in str(error.value)
    assert calls == ['validate','backend']
    assert list(scratch.glob('operator-*')) == []
    result=json.loads((scratch/'bootstrap-result.json').read_text())
    assert result['status'] == 'incomplete-owner-investigation-required'
    assert set(result) == {'schema','project','sha','digest','status'}


def test_inventory_command_rejects_exit_zero_unreachable_warnings_without_echo(monkeypatch):
    import subprocess
    monkeypatch.setattr(subprocess,'run',lambda *a,**k: subprocess.CompletedProcess(a,0,'[]',
        'WARNING regions unreachable TOKEN-SENTINEL'))
    with pytest.raises(ValueError) as error:
        bootstrap.metadata_command(['gcloud','functions','list'],env={})
    assert 'SENTINEL' not in str(error.value)


def test_bootstrap_requires_preconfigured_safe_artifact_retention():
    name = 'projects/mcp-website-dev-39539/locations/us-central1/repositories/gcf-artifacts'
    valid = {'name':name,'labels':{'firebase-functions-cleanup-opted-out':'true'}}
    bootstrap.validate_artifact_retention(valid,name)
    for invalid in [{}, {'name':name}, {**valid,'name':name.replace('us-central1','europe-west1')},
        {**valid,'cleanupPolicies':{'unexpected':{'action':'DELETE','condition':{'olderThan':'86400s'}}}}]:
        with pytest.raises(ValueError): bootstrap.validate_artifact_retention(invalid,name)


def test_gcloud_status_message_is_allowed_but_incomplete_inventory_still_blocks(monkeypatch):
    import subprocess
    def run(args,**kwargs):
        if args[1:3] == ['config','list']:
            return subprocess.CompletedProcess(args,0,json.dumps({'core':{'account':'owner@example.com'}}),
                'Your active configuration is: [default]')
        return subprocess.CompletedProcess(args,0,'[]','WARNING regions unreachable')
    monkeypatch.setattr(subprocess,'run',run)
    cloud = bootstrap.operator_cloud(environment())
    with pytest.raises(ValueError): cloud({'project':'mcp-website-dev-39539'},'functions','list')
