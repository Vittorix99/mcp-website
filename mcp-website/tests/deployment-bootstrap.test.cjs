const {test} = require('node:test')
const assert = require('node:assert/strict')
const {validateOperatorCredential, verifyOperator, validateInvocation} = require('../../scripts/deployment/firebase-bootstrap.cjs')
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
  const auth = info => ({fromJSON:() => ({getAccessToken:async () => ({token:'TOKEN-SENTINEL'}),
    getTokenInfo:async token => {assert.equal(token,'TOKEN-SENTINEL'); return info}})})
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
  client.getAccessToken = async () => ({token:'TOKEN-SENTINEL'})
  for (const verified of ['true',true,'false',false,'1',1,undefined]) {
    client.transporter.request = async () => ({data:{email:operator,email_verified:verified,
      scope:'https://www.googleapis.com/auth/cloud-platform',expires_in:3600}})
    const promise = verifyOperator(credential,manifest,{fromJSON:() => client})
    if (verified === 'true' || verified === true) await promise
    else await assert.rejects(promise)
  }
})
