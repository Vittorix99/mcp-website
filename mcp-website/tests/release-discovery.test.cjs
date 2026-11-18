const {test} = require('node:test')
const assert = require('node:assert/strict')
const {discoveryEnvironment, validateFederation, releaseBuildInvocation} = require('../../scripts/deployment/firebase.cjs')

const manifest = {
  project:'mcp-website-dev-39539', environment:'staging',
  sha:'a'.repeat(40), digest:'b'.repeat(64),
  backend:{MCP_ENV:'staging', PAYPAL_MODE:'sandbox', MCP_RUNTIME_SERVICE_ACCOUNT:'runtime@mcp-website-dev-39539.iam.gserviceaccount.com'},
  identities:{DEPLOY_SERVICE_ACCOUNT:'deploy@mcp-website-dev-39539.iam.gserviceaccount.com'},
  wif_provider:'projects/123/locations/global/workloadIdentityPools/github/providers/release',
}
const credential = {type:'external_account', audience:'//iam.googleapis.com/' + manifest.wif_provider,
  service_account_impersonation_url:'https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/' + manifest.identities.DEPLOY_SERVICE_ACCOUNT + ':generateAccessToken',
  credential_source:{url:'https://example.com/oidc',headers:{Authorization:'EPHEMERAL-SENTINEL'}}}

test('WIF accepts exact external account audience and impersonation only',()=>{
  validateFederation(credential, manifest)
  for (const change of [{type:'service_account',private_key:'SENTINEL'}, {audience:'wrong'},
    {service_account_impersonation_url:'https://attacker.example/token'},
    {credential_source:{executable:{command:'anything'}}}]) {
    assert.throws(()=>validateFederation({...credential,...change}, manifest), /Invalid release federation/)
  }
})

test('cloud discovery gets public backend config and ephemeral ADC path, no provider secrets',()=>{
  const result = discoveryEnvironment(manifest, {ADMIN_PORT:'8087',GCLOUD_PROJECT:manifest.project}, '/synthetic/wif.json')
  assert.equal(result.MCP_ENV, 'staging')
  assert.equal(result.ADMIN_PORT, '8087')
  assert.equal(result.GOOGLE_APPLICATION_CREDENTIALS, '/synthetic/wif.json')
  assert.equal(result.PAYPAL_CLIENT_SECRET, undefined)
  assert.throws(()=>discoveryEnvironment(manifest, {GCLOUD_PROJECT:'wrong'}, '/synthetic/wif.json'))
})

test('Firebase framework invokes the guarded release builder exactly for next build',()=>{
  const root = '/synthetic/project'
  const result = releaseBuildInvocation('/synthetic/project/mcp-website/node_modules/.bin/next', ['build'], {cwd:root + '/mcp-website'}, root)
  assert.equal(result.args.at(-1), '--release')
  assert.ok(result.args[0].endsWith('/mcp-website/scripts/build-safe.mjs'))
  assert.equal(releaseBuildInvocation('other', ['build'], {cwd:root + '/mcp-website'}, root), null)
  assert.equal(releaseBuildInvocation('/synthetic/project/mcp-website/node_modules/.bin/next', ['start'], {cwd:root + '/mcp-website'}, root), null)
})

test('release adapter matches the pinned CLI framework spawn and dependency resolution',()=>{
  const path = require('node:path')
  const {createRequire} = require('node:module')
  const root = path.resolve(__dirname,'../..')
  const cli = path.join(root,'mcp-website/node_modules/firebase-tools')
  const cliRequire = createRequire(path.join(cli,'package.json'))
  assert.equal(cliRequire('./package.json').version,'14.26.0')
  assert.equal(typeof cliRequire('cross-spawn').spawn,'function')
  const executable = cliRequire('./lib/frameworks/utils.js').getNodeModuleBin('next',path.join(root,'mcp-website'))
  assert.ok(releaseBuildInvocation(executable,['build'],{cwd:path.join(root,'mcp-website')},root))
})
