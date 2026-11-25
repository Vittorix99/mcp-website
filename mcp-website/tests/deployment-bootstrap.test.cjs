const {test} = require('node:test')
const assert = require('node:assert/strict')
const {validateOperatorCredential, verifyOperator, validateInvocation, limitDeployConcurrency, DEPLOY_CONCURRENCY} = require('../../scripts/deployment/firebase-bootstrap.cjs')
const project = 'mcp-website-dev-39539'
const operator = 'owner@example.com'
const manifest = {environment:'staging',project,sha:'a'.repeat(40),bootstrap:{operator}}
const env = {BOOTSTRAP_OPERATOR_EMAIL:operator,BOOTSTRAP_APPROVED_SHA:manifest.sha,
  BOOTSTRAP_CLOUD_APPROVED:'true',BOOTSTRAP_DATA_REVIEWED:'true'}
const credential = {type:'authorized_user',client_id:'synthetic',client_secret:'SENTINEL',refresh_token:'SENTINEL',quota_project_id:project}

test('operator bootstrap accepts only explicit personal OAuth, never WIF or private keys', () => {
  validateOperatorCredential(credential,manifest)
  for (const change of [{type:'external_account'},{type:'service_account'}, {private_key:'SENTINEL'},
    {quota_project_id:'production'}, {refresh_token:''}, {service_account_impersonation_url:'anything'}]) {
    assert.throws(() => validateOperatorCredential({...credential,...change},manifest), error => !error.message.includes('SENTINEL'))
  }
})

test('OAuth identity must be verified and match the named operator', async () => {
  const auth = info => ({fromJSON:() => ({getAccessToken:async () => ({token:'example-token'}),
    getTokenInfo:async token => {assert.equal(token,'example-token'); return info}})})
  await verifyOperator(credential,manifest,auth({email:operator,email_verified:true}))
  for (const info of [{email:'other@example.com',email_verified:true},{email:operator,email_verified:false},{}]) {
    await assert.rejects(verifyOperator(credential,manifest,auth(info)), error => !/SENTINEL/.test(error.message))
  }
})

test('bootstrap approvals cannot substitute for source, staging, or local execution', () => {
  validateInvocation(manifest,env,{sha:manifest.sha,clean:true,onMain:true})
  for (const update of [{CI:'true'}, {GITHUB_ACTIONS:'true'}, {FIREBASE_TOKEN:'SENTINEL'},
    {BOOTSTRAP_CLOUD_APPROVED:''},{BOOTSTRAP_DATA_REVIEWED:''},{BOOTSTRAP_OPERATOR_EMAIL:'other@example.com'},
    {BOOTSTRAP_APPROVED_SHA:'b'.repeat(40)}]) assert.throws(() => validateInvocation(manifest,{...env,...update},{sha:manifest.sha,clean:true,onMain:true}))
  for (const source of [{sha:'b'.repeat(40),clean:true,onMain:true}, {sha:manifest.sha,clean:false,onMain:true},
    {sha:manifest.sha,clean:true,onMain:false}]) assert.throws(() => validateInvocation(manifest,env,source))
  assert.throws(() => validateInvocation({...manifest,environment:'production'},env,{sha:manifest.sha,clean:true,onMain:true}))
})

test('real OAuth client preserves verified email string; false strings are rejected', async () => {
  const {createRequire} = require('node:module')
  const cli = createRequire(require.resolve('firebase-tools/package.json'))
  const {OAuth2Client} = cli('google-auth-library')
  const client = new OAuth2Client()
  client.getAccessToken = async () => ({token:'example-token'})
  for (const verified of ['true',true,'false',false,'1',1,undefined]) {
    client.transporter.request = async () => ({data:{email:operator,email_verified:verified,
      scope:'https://www.googleapis.com/auth/cloud-platform',expires_in:3600}})
    const promise = verifyOperator(credential,manifest,{fromJSON:() => client})
    if (verified === 'true' || verified === true) await promise
    else await assert.rejects(promise)
  }
})

test('bootstrap caps firebase-tools function deploy concurrency below the Cloud Run write quota', () => {
  const seen = []
  class QueueExecutor { constructor(options) { seen.push(options) } }
  const executor = {QueueExecutor}
  limitDeployConcurrency(path => { assert.equal(path, './lib/deploy/functions/release/executor'); return executor })
  new executor.QueueExecutor({retries:30,backoff:20000,concurrency:40,maxBackoff:100000})
  new executor.QueueExecutor({concurrency:1})
  assert.deepEqual(seen.map(options => options.concurrency), [DEPLOY_CONCURRENCY, 1])
  assert.equal(seen[0].retries, 30)
  assert.throws(() => limitDeployConcurrency(() => ({QueueExecutor}), 40))
  assert.throws(() => limitDeployConcurrency(() => ({})))
})

test('the ordinary release shares the same deploy concurrency cap as the bootstrap', () => {
  const ordinary = require('../../scripts/deployment/firebase.cjs')
  assert.equal(ordinary.limitDeployConcurrency, limitDeployConcurrency)
  assert.equal(ordinary.DEPLOY_CONCURRENCY, DEPLOY_CONCURRENCY)
  const source = require('node:fs').readFileSync(require.resolve('../../scripts/deployment/firebase.cjs'), 'utf8')
  assert.match(source, /installAdapters\(root,cliRequire,manifest,credentialPath\)\n\s+limitDeployConcurrency\(cliRequire\)/)
})

test('migration updates only approved existing HTTP functions and never creates or deletes', async () => {
  const {createRequire} = require('node:module')
  const {installCliGuards} = require('../../scripts/deployment/cli-guards.cjs')
  const cli = createRequire(require.resolve('firebase-tools/package.json'))
  const functions = cli('./lib/gcp/cloudfunctionsv2.js')
  const guarded = {environment:'staging',project,wif_provider:'projects/1005755179074/locations/global/workloadIdentityPools/p/providers/q',
    identities:{DEPLOY_SERVICE_ACCOUNT:`github-deploy@${project}.iam.gserviceaccount.com`,
      BUILD_SERVICE_ACCOUNT:`functions-build@${project}.iam.gserviceaccount.com`,
      RUNTIME_SERVICE_ACCOUNT:`app-runtime@${project}.iam.gserviceaccount.com`,
      WEB_RUNTIME_SERVICE_ACCOUNT:`web-runtime@${project}.iam.gserviceaccount.com`}}
  const originals = {update:functions.updateFunction, create:functions.createFunction, remove:functions.deleteFunction}
  const updated = []
  functions.updateFunction = async fn => { updated.push(fn.name) }
  const name = id => `projects/${project}/locations/us-central1/functions/${id}`
  const restore = installCliGuards(cli, guarded, {migrate:true, approvedFunctions:['get_event']})
  try {
    await functions.updateFunction({name:name('get_event')})
    assert.deepEqual(updated, [name('get_event')])
    await assert.rejects(functions.updateFunction({name:name('unapproved')}), /Unapproved migration function/)
    await assert.rejects(functions.updateFunction({name:'projects/other/locations/us-central1/functions/get_event'}), /Unapproved migration function/)
    await assert.rejects(functions.createFunction({name:name('get_event')}), /updates existing functions only/)
    await assert.rejects(functions.deleteFunction(name('get_event')), /forbids function deletion/)
    const http = {platform:'gcfv2',id:'get_event',region:'us-central1',project,entryPoint:'get_event',runtime:'python311',
      codebase:'python_codebase',source:{storageSource:{bucket:'b',object:'o'}},
      serviceAccount:guarded.identities.RUNTIME_SERVICE_ACCOUNT,labels:{},httpsTrigger:{}}
    assert.ok(functions.functionFromEndpoint(http).buildConfig)
    assert.throws(() => functions.functionFromEndpoint({...http,id:'unapproved'}), /Unapproved bootstrap function/)
    const eventful = {...http,httpsTrigger:undefined,eventTrigger:{eventType:'google.cloud.firestore.document.v1.written',
      eventFilters:{database:'(default)',namespace:'(default)'},eventFilterPathPatterns:{document:'x/{id}'},retry:false}}
    assert.throws(() => functions.functionFromEndpoint(eventful), /only permit HTTP functions/)
  } finally {
    restore()
    Object.assign(functions, {updateFunction:originals.update, createFunction:originals.create, deleteFunction:originals.remove})
  }
  assert.throws(() => installCliGuards(cli, {...guarded,environment:'production'}, {migrate:true}))
  assert.throws(() => installCliGuards(cli, guarded, {migrate:true, bootstrap:true}))
})
