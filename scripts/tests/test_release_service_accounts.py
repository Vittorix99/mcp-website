"""Exercise the pinned CLI guard without contacting IAM or changing site identity."""
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize('environment', ['staging', 'production'])
def test_cli_checks_declared_accounts_and_fails_closed(environment):
    code = r"""
const assert = require('node:assert/strict')
const {createRequire} = require('node:module')
const path = require('node:path')
const root = process.argv[1], environment = process.argv[2]
const project = environment === 'staging' ? 'mcp-website-dev-39539' : 'mcp-website-2a1ad'
const web = createRequire(path.join(root,'mcp-website/package.json'))
const cli = createRequire(web.resolve('firebase-tools/package.json'))
const {installCliGuards} = require(path.join(root,'scripts/deployment/cli-guards.cjs'))
const identities = Object.fromEntries([['DEPLOY','github-deploy'],['BUILD','functions-build'],
  ['RUNTIME','app-runtime'],['WEB_RUNTIME','web-runtime']].map(([k,id]) =>
  [k+'_SERVICE_ACCOUNT',`${id}@${project}.iam.gserviceaccount.com`]))
const manifest = {project,environment,identities}
const checks = cli('./lib/deploy/functions/checkIam.js')
const iam = cli('./lib/gcp/iam.js')
const saved = {check:checks.checkServiceAccountIam,test:iam.testResourceIamPermissions}
const calls = []
iam.testResourceIamPermissions = async (origin,version,resource,permissions) => {
  assert.equal(origin,'https://iam.googleapis.com')
  assert.equal(version,'v1')
  assert.deepEqual(permissions,['iam.serviceAccounts.actAs'])
  calls.push(resource)
  return {passed:true}
}
const restore = installCliGuards(cli,manifest)
;(async () => {
  try {
    await checks.checkServiceAccountIam(project)
    assert.deepEqual(calls,['BUILD','RUNTIME','WEB_RUNTIME'].map(k =>
      `projects/${project}/serviceAccounts/${identities[k+'_SERVICE_ACCOUNT']}`))
    assert.ok(calls.every(name => !name.includes('@appspot.')))
    const before = calls.length
    await assert.rejects(checks.checkServiceAccountIam('wrong-project'))
    assert.equal(calls.length,before)
    for (const key of ['BUILD_SERVICE_ACCOUNT','RUNTIME_SERVICE_ACCOUNT','WEB_RUNTIME_SERVICE_ACCOUNT']) {
      for (const outcome of [{passed:false},undefined,{passed:'true'}]) {
        const tested = []
        iam.testResourceIamPermissions = async (origin,version,resource) => {
          tested.push(resource)
          return resource.endsWith('/'+identities[key]) ? outcome : {passed:true}
        }
        await assert.rejects(checks.checkServiceAccountIam(project),/permissions|actAs/)
        assert.ok(tested.some(resource => resource.endsWith('/'+identities[key])))
      }
    }
    iam.testResourceIamPermissions = async () => {throw new Error('Synthetic IAM outage')}
    await assert.rejects(checks.checkServiceAccountIam(project),/Synthetic IAM outage/)
  } finally {
    restore()
    iam.testResourceIamPermissions=saved.test
  }
  assert.equal(checks.checkServiceAccountIam,saved.check)
})().catch(error => {console.error(error);process.exitCode=1})
"""
    result = subprocess.run(['node', '-e', code, str(ROOT), environment],
        cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
