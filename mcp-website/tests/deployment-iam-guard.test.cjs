const {test} = require('node:test')
const assert = require('node:assert/strict')
const {createRequire} = require('node:module')
const cli = createRequire(require.resolve('firebase-tools/package.json'))
const {installCliGuards} = require('../../scripts/deployment/cli-guards.cjs')

const project = 'mcp-website-dev-39539'
const number = '1005755179074'
const manifest = {project,environment:'staging',wif_provider:`projects/${number}/locations/global/workloadIdentityPools/github-actions/providers/main-release`,
  identities:Object.fromEntries([['DEPLOY','github-deploy'],['BUILD','functions-build'],
    ['RUNTIME','app-runtime'],['WEB_RUNTIME','web-runtime']].map(([key,id]) =>
    [key + '_SERVICE_ACCOUNT',`${id}@${project}.iam.gserviceaccount.com`]))}
const endpoint = {project,region:'us-central1',platform:'gcfv2',id:'on_member_created',
  entryPoint:'on_member_created',runtime:'python311',codebase:'python_codebase',
  serviceAccount:manifest.identities.RUNTIME_SERVICE_ACCOUNT,
  eventTrigger:{eventType:'google.cloud.firestore.document.v1.created',eventFilters:{database:'(default)'}}}
const policy = {bindings:[
  ['roles/cloudfunctions.serviceAgent',`service-${number}@gcf-admin-robot.iam.gserviceaccount.com`],
  ['roles/cloudbuild.serviceAgent',`service-${number}@gcp-sa-cloudbuild.iam.gserviceaccount.com`],
  ['roles/eventarc.serviceAgent',`service-${number}@gcp-sa-eventarc.iam.gserviceaccount.com`],
  ['roles/pubsub.serviceAgent',`service-${number}@gcp-sa-pubsub.iam.gserviceaccount.com`],
  ['roles/eventarc.eventReceiver',manifest.identities.RUNTIME_SERVICE_ACCOUNT],
].map(([role,email]) => ({role,members:['serviceAccount:' + email]}))}

test('first Firestore deployment validates explicit bindings and cannot write project IAM', async () => {
  const resource = cli('./lib/gcp/resourceManager.js')
  const checks = cli('./lib/deploy/functions/checkIam.js')
  const savedGet = resource.getIamPolicy
  const savedSet = resource.setIamPolicy
  let writes = 0
  resource.getIamPolicy = async () => structuredClone(policy)
  resource.setIamPolicy = async () => { writes++; throw new Error('Unexpected live mutation') }
  const restore = installCliGuards(cli,manifest)
  try {
    const want = {endpoints:{'us-central1':{on_member_created:endpoint}}}
    await checks.ensureServiceAgentRoles(project,number,want,{endpoints:{}},false)
    assert.equal(writes,0)
    await assert.rejects(resource.setIamPolicy(number,{bindings:[]}),/IAM/)
    assert.equal(writes,0)
    resource.getIamPolicy = async () => ({bindings:policy.bindings.slice(0,2)})
    await assert.rejects(checks.ensureServiceAgentRoles(project,number,want,{endpoints:{}},false),/IAM/)
    assert.equal(writes,0)
    await assert.rejects(checks.ensureServiceAgentRoles('other-project',number,want,{endpoints:{}},false))
  } finally {
    restore()
    resource.getIamPolicy = savedGet
    resource.setIamPolicy = savedSet
  }
})

test('ordinary releases preserve invoker policy and refuse implicit policy changes', async () => {
  const run = cli('./lib/gcp/run.js')
  const savedGet = run.getIamPolicy
  run.getIamPolicy = async () => ({bindings:[{role:'roles/run.invoker',members:['allUsers']}]})
  const restore = installCliGuards(cli,manifest)
  const service = `projects/${project}/locations/us-central1/services/public-api`
  try {
    await run.setInvokerUpdate(project,service,['public'])
    await assert.rejects(run.setInvokerUpdate(project,service,[manifest.identities.RUNTIME_SERVICE_ACCOUNT]),/IAM/)
    await assert.rejects(run.setInvokerCreate(project,service,['public']),/IAM/)
    await assert.rejects(run.setIamPolicy(service,{bindings:[]}),/IAM/)
    await assert.rejects(run.setInvokerUpdate('other-project',service,['public']))
  } finally {
    restore()
    run.getIamPolicy = savedGet
  }
})

test('service IAM refuses nested paths and bootstrap refuses production', async () => {
  const run = cli('./lib/gcp/run.js')
  const restore = installCliGuards(cli,manifest)
  try {
    await assert.rejects(run.setInvokerUpdate(project,
      `projects/${project}/locations/us-central1/services/extra/public-api`,['public']),/target/)
  } finally { restore() }
  const prod = 'mcp-website-2a1ad'
  assert.throws(() => installCliGuards(cli,{...manifest,environment:'production',project:prod,
    identities:Object.fromEntries(Object.entries(manifest.identities).map(([key,value]) => [key,value.replace(project,prod)]))},
  {bootstrap:true}),/staging/)
})

test('real CLI selectors select exactly HTTP endpoints and reject prefix collisions', () => {
  const {bootstrapSelectors} = require('../../scripts/deployment/cli-guards.cjs')
  const endpoints = [{id:'get_event',kind:'http'},{id:'on_member',kind:'event'},{id:'cleanup',kind:'schedule'}]
  assert.equal(bootstrapSelectors(cli,endpoints),'functions:python_codebase:get_event')
  for (const rows of [[], [...endpoints,endpoints[0]], [{id:'api',kind:'http'},{id:'api-extra',kind:'event'}],
    [{id:'unknown',kind:'other'}]]) assert.throws(() => bootstrapSelectors(cli,rows))
})

test('real Fabricator resource exhaustion cannot delete or recreate during bootstrap', async () => {
  const functions = cli('./lib/gcp/cloudfunctionsv2.js')
  const poller = cli('./lib/operation-poller.js')
  const {Fabricator} = cli('./lib/deploy/functions/release/fabricator.js')
  const saved = {create:functions.createFunction,delete:functions.deleteFunction,poll:poller.pollOperation}
  let creates = 0, deletes = 0
  functions.createFunction = async () => {
    creates++
    if (creates === 1) throw Object.assign(new Error('Synthetic resource exhaustion'),{code:8})
    return {name:'synthetic-create'}
  }
  functions.deleteFunction = async () => {deletes++;return {name:'synthetic-delete'}}
  poller.pollOperation = async () => ({serviceConfig:{}})
  const restore = installCliGuards(cli,manifest,{bootstrap:true,approvedFunctions:['get_event']})
  try {
    const executor = {run:async callback => callback()}
    const fabricator = new Fabricator({executor,functionExecutor:executor,
      sources:{python_codebase:{storage:{bucket:'synthetic',object:'source.zip'}}},projectNumber:number})
    const http = {...endpoint,id:'get_event',entryPoint:'get_event',httpsTrigger:{}}
    delete http.eventTrigger
    await assert.rejects(fabricator.createV2Function(http,{abort(){},getToken:async () => undefined,poller(){}}))
    assert.equal(creates,1)
    assert.equal(deletes,0)
    await assert.rejects(functions.updateFunction({}),/Bootstrap/)
  } finally {
    restore()
    functions.createFunction = saved.create
    functions.deleteFunction = saved.delete
    poller.pollOperation = saved.poll
  }
})

test('bootstrap checks real CLI cleanup metadata before deployment and never changes policy', async () => {
  const artifacts = cli('./lib/functions/artifacts.js')
  const savedGet = artifacts.getRepo
  const name = `projects/${project}/locations/us-central1/repositories/gcf-artifacts`
  let repo = {name,labels:{'firebase-functions-cleanup-opted-out':'true'}}
  artifacts.getRepo = async () => repo
  const restore = installCliGuards(cli,manifest,{bootstrap:true,approvedFunctions:['get_event']})
  try {
    assert.deepEqual(await artifacts.checkCleanupPolicy(project,['us-central1']),{locationsToSetup:[],locationsWithErrors:[]})
    repo = {name}
    await assert.rejects(artifacts.checkCleanupPolicy(project,['us-central1']),/retention/)
    await assert.rejects(artifacts.setCleanupPolicies(project,['us-central1'],1),/policy/)
  } finally {restore();artifacts.getRepo = savedGet}
})
