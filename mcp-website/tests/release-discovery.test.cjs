const {test} = require('node:test')
const assert = require('node:assert/strict')
const {discoveryEnvironment, validateFederation, releaseBuildInvocation, spawnReleaseBuild} = require('../../scripts/deployment/firebase.cjs')

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

test('ordinary staging selects HTTP only while production keeps the complete codebase', () => {
  const {createRequire} = require('node:module')
  const cli = createRequire(require.resolve('firebase-tools/package.json'))
  const {releaseProfile} = require('../../scripts/deployment/firebase.cjs')
  const endpoints = [{id:'get_event',kind:'http'},{id:'on_member',kind:'event'},{id:'cleanup',kind:'schedule'}]
  assert.deepEqual(releaseProfile(cli,manifest,endpoints), {
    only:'functions:python_codebase:get_event',
    guards:{httpUpdatesOnly:true,approvedFunctions:['get_event']},
  })
  assert.deepEqual(releaseProfile(cli,{environment:'production'}), {
    only:'functions:python_codebase',guards:{},
  })
  assert.throws(() => releaseProfile(cli,manifest,[{id:'api',kind:'http'},{id:'api-extra',kind:'event'}]))
  assert.throws(() => releaseProfile(cli,manifest,[]))
  assert.throws(() => releaseProfile(cli,{environment:'unknown'},endpoints))
})

test('WIF probe uses only Firebase reads and permission tests under the pinned CLI', async () => {
  const {probeReleaseAccess} = require('../../scripts/deployment/firebase.cjs')
  const accounts = {BUILD_SERVICE_ACCOUNT:'build',RUNTIME_SERVICE_ACCOUNT:'backend',WEB_RUNTIME_SERVICE_ACCOUNT:'web'}
  const calls = []
  const probeManifest = {...manifest,identities:accounts}
  const cli = name => {
    if (name === './lib/requireAuth.js') return {requireAuth:async options => {
      calls.push('auth');assert.equal(options.project,manifest.project)
    }}
    if (name === './lib/hosting/api.js') return {listSites:async project => {
      calls.push('hosting-read');return [{name:`projects/${project}/sites/${project}`}]
    }}
    if (name === './lib/fetchWebSetup.js') return {fetchWebSetup:async options => {
      assert.equal(options.project,manifest.project)
      calls.push('web-config');return {private:'PRIVATE_SENTINEL'}
    }}
    if (name === './lib/functionsConfig.js') return {getFirebaseConfig:async options => {
      assert.equal(options.project,manifest.project)
      calls.push('admin-config');return {private:'PRIVATE_SENTINEL'}
    }}
    if (name === './lib/gcp/iam.js') return {
      testIamPermissions:async (project,permissions) => {
        calls.push('project-permissions')
        assert.ok(permissions.includes('run.services.update'))
        assert.ok(permissions.includes('firebasehosting.sites.update'))
        assert.ok(permissions.includes('apikeys.keys.getKeyString'))
        return {passed:true}
      },
      testResourceIamPermissions:async (origin,version,resource,permissions) => {
        calls.push(resource)
        assert.equal(origin,'https://iam.googleapis.com')
        assert.equal(version,'v1')
        assert.deepEqual(permissions,['iam.serviceAccounts.actAs'])
        return {passed:true}
      },
    }
    throw new Error('Probe requested a module outside the read-only allowlist')
  }
  assert.deepEqual(await probeReleaseAccess(cli,probeManifest), {mode:'read-only',firebase_auth:true,
    hosting_read:true,web_config_read:true,admin_config_read:true,project_permissions:true,account_actas:true})
  assert.deepEqual(calls,['auth','hosting-read','project-permissions','web-config','admin-config',...Object.values(accounts).map(
    a => `projects/${manifest.project}/serviceAccounts/${a}`)])
  const denied = name => name === './lib/gcp/iam.js'
    ? {testIamPermissions:async () => ({passed:false,missing:['run.services.update','PRIVATE_SENTINEL']})} : cli(name)
  const saved = console.error
  const output = []
  console.error = line => output.push(line)
  try {
    await assert.rejects(probeReleaseAccess(denied,probeManifest),/permissions/)
  } finally {console.error=saved}
  assert.ok(output.includes('RELEASE_MISSING_PERMISSION=run.services.update'))
  assert.ok(!output.join('\n').includes('PRIVATE_SENTINEL'))
})

test('entry failure diagnostics expose nested status and safe type without SDK messages', () => {
  const {reportEntryFailure} = require('../../scripts/deployment/firebase.cjs')
  const saved = console.error
  const output = []
  console.error = line => output.push(line)
  try {
    reportEntryFailure({status:500,message:'PRIVATE_SENTINEL',original:{status:403,message:'PRIVATE_SENTINEL'}})
  } finally {console.error=saved}
  assert.ok(output.includes('RELEASE_SDK_STATUS=403'))
  assert.ok(!output.includes('RELEASE_SDK_STATUS=500'))
  assert.ok(!output.join('\n').includes('PRIVATE_SENTINEL'))
})

test('entry failure reports only a masked Google API target', () => {
  const {reportEntryFailure} = require('../../scripts/deployment/firebase.cjs')
  const saved = console.error
  const output = []
  console.error = line => output.push(line)
  try {
    reportEntryFailure({status:403,context:{response:{url:'https://cloudfunctions.googleapis.com/v2/projects/secret-project/locations/us-central1/functions/privateName:setIamPolicy?key=PRIVATE_SENTINEL'}}})
    reportEntryFailure({status:403,context:{response:{url:'https://evil.example.com/v2/projects/x'}}})
    reportEntryFailure({status:403,message:'Request to https://firebasehosting.googleapis.com/v1beta1/projects/secret-project/sites/privateSite/versions/abc123:finalize?key=PRIVATE_SENTINEL had HTTP Error: 403, PRIVATE_SENTINEL'})
  } finally {console.error=saved}
  assert.ok(output.includes('RELEASE_API_TARGET=cloudfunctions.googleapis.com/v2/projects/*/locations/*/functions/*:setIamPolicy'))
  assert.ok(output.includes('RELEASE_API_TARGET=firebasehosting.googleapis.com/v1beta1/projects/*/sites/*/versions/*:finalize'))
  assert.equal(output.filter(line => line.startsWith('RELEASE_API_TARGET=')).length,2)
  assert.ok(!output.join('\n').match(/PRIVATE_SENTINEL|secret-project|privateName|privateSite|abc123|evil/))
})

test('entry failure reports only static guard messages and quoted permission names', () => {
  const {reportEntryFailure} = require('../../scripts/deployment/firebase.cjs')
  const saved = console.error
  const output = []
  console.error = line => output.push(line)
  try {
    reportEntryFailure({status:500,message:'Missing permissions on configured service account; owner provisioning required'})
    reportEntryFailure({status:500,message:'Missing required permission on project secret-project to deploy functions: cloudfunctions.functions.create and run.services.setIamPolicy PRIVATE_SENTINEL',
      original:{message:'Request to https://evil.example.com/x'}})
    reportEntryFailure({status:500,message:'Arbitrary SDK text PRIVATE_SENTINEL'})
  } finally {console.error=saved}
  assert.ok(output.includes('RELEASE_GUARD=Missing permissions on configured service account; owner provisioning required'))
  assert.ok(output.includes('RELEASE_PERMISSIONS=cloudfunctions.functions.create,run.services.setIamPolicy'))
  assert.equal(output.filter(line => line.startsWith('RELEASE_GUARD=')).length,1)
  assert.ok(!output.join('\n').match(/PRIVATE_SENTINEL|secret-project|evil|Arbitrary/))
})

test('pinned CLI asynchronous failures reach the sanitizer and preserve original error handling', {timeout:2000}, async () => {
  const {createRequire} = require('node:module')
  const cli = createRequire(require.resolve('firebase-tools/package.json'))
  const {Command} = cli('./lib/command.js')
  const {Command:Program} = cli('commander')
  const track = cli('./lib/track.js')
  const {installFailureReporter} = require('../../scripts/deployment/firebase.cjs')
  const error = Object.assign(new Error('PRIVATE_SENTINEL'),{status:403})
  const output = []
  const saved = {track:track.trackGA4,stderr:console.error}
  let resolveDone
  const done = new Promise(resolve => {resolveDone=resolve})
  let handled
  const client = {cli:new Program(),errorOut:received => {handled=received;resolveDone()}}
  track.trackGA4 = async () => undefined
  console.error = line => output.push(line)
  const restore = installFailureReporter(name => {
    assert.equal(name,'./lib/index.js')
    return client
  })
  try {
    const command = new Command('synthetic-diagnostic')
    command.runner = () => async () => {throw error}
    command.register(client)
    client.cli.parse(['node','synthetic','synthetic-diagnostic'])
    await done
    assert.equal(handled,error)
    assert.ok(output.includes('RELEASE_SDK_STATUS=403'))
    assert.ok(!output.join('\n').includes('PRIVATE_SENTINEL'))
  } finally {
    restore()
    console.error=saved.stderr
    track.trackGA4=saved.track
  }
})

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

test('release build removes the stale .next first and aborts the deploy when the build fails',()=>{
  const {EventEmitter} = require('node:events')
  const calls = []
  const replacement = {executable:'node',args:['build-safe.mjs','--release']}
  for (const [code,signal,aborts] of [[0,null,false],[1,null,true],[null,'SIGKILL',true]]) {
    const child = new EventEmitter()
    let aborted = false
    const result = spawnReleaseBuild((exe,args) => {calls.push(['spawn',exe]); return child},replacement,{},'/synthetic/project',
      {remove:target => calls.push(['remove',target]),fail:() => {aborted = true}})
    assert.equal(result,child)
    child.emit('exit',code,signal)
    assert.equal(aborted,aborts)
  }
  assert.deepEqual(calls.slice(0,2),[['remove','/synthetic/project/mcp-website/.next'],['spawn','node']])
})
