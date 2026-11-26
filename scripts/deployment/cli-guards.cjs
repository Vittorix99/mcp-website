const catalog = require('../../mcp-backend/functions/config/environment_catalog.json')

function requireCondition(condition, message) {
  if (!condition) throw new Error(message)
}

function validateIdentities(manifest) {
  const resource = catalog.environments[manifest.environment]
  requireCondition(['staging','production'].includes(manifest.environment) &&
    resource?.project_id === manifest.project, 'Invalid deployment project')
  const keys = ['DEPLOY_SERVICE_ACCOUNT','BUILD_SERVICE_ACCOUNT',
    'RUNTIME_SERVICE_ACCOUNT','WEB_RUNTIME_SERVICE_ACCOUNT']
  const suffix = '@' + manifest.project + '.iam.gserviceaccount.com'
  const accounts = keys.map(key => manifest.identities?.[key])
  requireCondition(accounts.every(account => typeof account === 'string' &&
    /^[a-z][a-z0-9-]{4,28}[a-z0-9]@/.test(account) && account.endsWith(suffix) &&
    account.split('@').length === 2) && new Set(accounts).size === 4,
  'Invalid deployment identities')
}

function withBuildIdentity(endpoint, manifest, convert) {
  validateIdentities(manifest)
  const python = endpoint.codebase === 'python_codebase'
  const web = endpoint.codebase === 'firebase-frameworks-' + manifest.project
  requireCondition(endpoint.project === manifest.project && endpoint.platform === 'gcfv2' &&
    endpoint.region === 'us-central1' && (python || web) &&
    endpoint.runtime === (python ? 'python311' : 'nodejs22') &&
    endpoint.serviceAccount === manifest.identities[python ? 'RUNTIME_SERVICE_ACCOUNT' : 'WEB_RUNTIME_SERVICE_ACCOUNT'],
  'Unexpected function build target')
  const result = convert(endpoint)
  requireCondition(result?.buildConfig, 'Missing function build configuration')
  return {...result, buildConfig:{...result.buildConfig,
    serviceAccount:'projects/' + manifest.project + '/serviceAccounts/' + manifest.identities.BUILD_SERVICE_ACCOUNT}}
}

function assertProjectBindings(policy, required) {
  for (const expected of required) {
    const roles = Array.isArray(expected.role) ? expected.role : [expected.role]
    requireCondition(expected.members.every(member => (policy.bindings || []).some(binding =>
      roles.includes(binding.role) && !binding.condition && binding.members?.includes(member))),
    'Required project IAM binding is missing; owner provisioning required')
  }
}

function requiredProjectBindings(manifest, number, endpoints) {
  const rows = [
    // Existing projects may still carry the deprecated service-agent role.
    [['roles/cloudfunctions.standardServiceAgent','roles/cloudfunctions.serviceAgent'],
      `service-${number}@gcf-admin-robot.iam.gserviceaccount.com`],
    ['roles/cloudbuild.serviceAgent',`service-${number}@gcp-sa-cloudbuild.iam.gserviceaccount.com`],
  ]
  if (endpoints.some(endpoint => endpoint.eventTrigger)) {
    rows.push(['roles/eventarc.serviceAgent',`service-${number}@gcp-sa-eventarc.iam.gserviceaccount.com`],
      ['roles/pubsub.serviceAgent',`service-${number}@gcp-sa-pubsub.iam.gserviceaccount.com`],
      ['roles/eventarc.eventReceiver',manifest.identities.RUNTIME_SERVICE_ACCOUNT])
  }
  return rows.map(([role,email]) => ({role,members:['serviceAccount:' + email]}))
}

// Restricted updates require retention that cannot delete saved rollback images.
// The opt-out label alone does not disable an existing DELETE policy.
function migrationRetentionAllowed(repo) {
  const policies = Object.values(repo.cleanupPolicies || {})
  if (repo.cleanupPolicyDryRun !== true && policies.some(policy => policy.action === 'DELETE')) return false
  return repo.labels?.['firebase-functions-cleanup-opted-out'] === 'true' ||
    (policies.length > 0 && (repo.cleanupPolicyDryRun === true || policies.every(policy => policy.action !== 'DELETE')))
}

function installCliGuards(cli, manifest, {bootstrap = false, migrate = false, httpUpdatesOnly = false, approvedFunctions = []} = {}) {
  validateIdentities(manifest)
  requireCondition(!bootstrap || manifest.environment === 'staging', 'Bootstrap requires staging')
  // One-time owner migration: update the existing approved HTTP functions in place, never create or delete.
  requireCondition(!migrate || (!bootstrap && manifest.environment === 'staging'), 'Migration requires staging and excludes bootstrap')
  requireCondition(!httpUpdatesOnly || (!bootstrap && !migrate && manifest.environment === 'staging' &&
    approvedFunctions.length > 0 && approvedFunctions.every(id => /^[a-z][a-z0-9_-]{0,62}$/.test(id)) &&
    new Set(approvedFunctions).size === approvedFunctions.length), 'HTTP updates require an approved staging inventory')
  const restricted = bootstrap || migrate || httpUpdatesOnly
  requireCondition(cli('./package.json').version === '14.26.0', 'Review the pinned CLI adapter')
  const functions = cli('./lib/gcp/cloudfunctionsv2.js')
  const resource = cli('./lib/gcp/resourceManager.js')
  const checks = cli('./lib/deploy/functions/checkIam.js')
  const backend = cli('./lib/deploy/functions/backend.js')
  const run = cli('./lib/gcp/run.js')
  const proto = cli('./lib/gcp/proto.js')
  const artifacts = cli('./lib/functions/artifacts.js')
  const secrets = cli('./lib/gcp/secretManager.js')
  const originals = {deleteFunction:functions.deleteFunction,updateFunction:functions.updateFunction,
    createFunction:functions.createFunction,
    cleanupCheck:artifacts.checkCleanupPolicy,cleanupSet:artifacts.setCleanupPolicies,convert:functions.functionFromEndpoint, projectSet:resource.setIamPolicy,
    secretSet:secrets.setIamPolicy,
    agentCheck:checks.ensureServiceAgentRoles, runSet:run.setIamPolicy,
    invokerCreate:run.setInvokerCreate, invokerUpdate:run.setInvokerUpdate}
  if (bootstrap) {
    functions.deleteFunction = async () => { throw new Error('Bootstrap forbids function deletion and destructive recovery') }
    functions.updateFunction = async () => { throw new Error('Bootstrap requires new functions; updates need owner investigation') }
    artifacts.checkCleanupPolicy = async (project, locations) => {
      requireCondition(project === manifest.project && locations.every(location => location === 'us-central1'), 'Unexpected artifact repository')
      for (const location of locations) {
        const repo = await artifacts.getRepo(project,location,true)
        requireCondition(repo.name === `projects/${project}/locations/${location}/repositories/gcf-artifacts` &&
          repo.labels?.['firebase-functions-cleanup-opted-out'] === 'true' &&
          Object.values(repo.cleanupPolicies || {}).every(policy => policy.action !== 'DELETE'),
        'Approved artifact retention opt-out required before bootstrap')
      }
      return {locationsToSetup:[],locationsWithErrors:[]}
    }
  }
  artifacts.setCleanupPolicies = async () => { throw new Error('Artifact cleanup policy changes require owner provisioning') }
  // Restricted staging modes may only use secret access that already exists.
  if (restricted) secrets.setIamPolicy = async () => { throw new Error('Secret IAM writes require explicit owner provisioning') }
  const newPublicServices = new Set()
  const webFunctions = new Set()
  if (migrate || httpUpdatesOnly) {
    const approved = new Set(approvedFunctions)
    const mode = migrate ? 'Migration' : 'Staging release'
    functions.deleteFunction = async () => { throw new Error(mode + ' forbids function deletion') }
    functions.createFunction = async () => { throw new Error(mode + ' updates existing functions only; creation needs owner investigation') }
    // firebase-tools checks the artifact repository only after the updates; verify it here so a
    // bad state is rejected by the same guard, never left half-migrated and unprompted.
    artifacts.checkCleanupPolicy = async (project, locations) => {
      requireCondition(project === manifest.project && locations.every(location => location === 'us-central1'), 'Unexpected artifact repository')
      for (const location of locations) {
        const repo = await artifacts.getRepo(project,location,true)
        requireCondition(repo.name === `projects/${project}/locations/${location}/repositories/gcf-artifacts` &&
          migrationRetentionAllowed(repo), 'Approved artifact retention required before migration')
      }
      return {locationsToSetup:[],locationsWithErrors:[]}
    }
    functions.updateFunction = async function(cloudFunction, ...rest) {
      const id = String(cloudFunction?.name || '').split('/').at(-1)
      requireCondition(cloudFunction.name === `projects/${manifest.project}/locations/us-central1/functions/${id}` &&
        (approved.has(id) || webFunctions.has(id)), migrate ? 'Unapproved migration function' : 'Unapproved staging release function')
      return originals.updateFunction.call(this,cloudFunction,...rest)
    }
  }
  function serviceTarget(project, name) {
    requireCondition(project === manifest.project && typeof name === 'string' &&
      name === `projects/${manifest.project}/locations/us-central1/services/${name.split('/').at(-1)}` &&
      /^[a-z][a-z0-9-]{0,62}$/.test(name.split('/').at(-1)), 'Unexpected IAM service target')
  }
  functions.functionFromEndpoint = endpoint => {
    const result = withBuildIdentity(endpoint,manifest,originals.convert)
    if (restricted) {
      requireCondition(endpoint.httpsTrigger && !endpoint.eventTrigger && !endpoint.scheduleTrigger &&
        !endpoint.taskQueueTrigger && !endpoint.blockingTrigger, 'Restricted staging modes only permit HTTP functions')
      if (endpoint.codebase === 'python_codebase') {
        requireCondition(approvedFunctions.includes(endpoint.id), 'Unapproved bootstrap function')
      } else {
        webFunctions.add(endpoint.id)
        requireCondition(webFunctions.size === 1, 'Unexpected extra SSR function')
      }
    }
    if (bootstrap) {
      newPublicServices.add(`projects/${manifest.project}/locations/us-central1/services/${endpoint.id.toLowerCase().replaceAll('_','-')}`)
    }
    return result
  }
  resource.setIamPolicy = async () => { throw new Error('Project IAM writes require explicit owner provisioning') }
  run.setIamPolicy = async () => { throw new Error('Service IAM writes require explicit owner provisioning') }
  checks.ensureServiceAgentRoles = async (project, number, want) => {
    requireCondition(project === manifest.project && /^[0-9]+$/.test(String(number)) &&
      String(number) === manifest.wif_provider?.split('/')[1], 'Unexpected IAM project identity')
    const endpoints = backend.allEndpoints(want)
    requireCondition(endpoints.every(endpoint => endpoint.project === manifest.project), 'Unexpected IAM endpoint project')
    if (bootstrap || httpUpdatesOnly) await artifacts.checkCleanupPolicy(project,['us-central1'])
    const policy = await resource.getIamPolicy(String(number))
    assertProjectBindings(policy,requiredProjectBindings(manifest,number,endpoints))
  }
  run.setInvokerCreate = async (project, name, invoker, ...rest) => {
    serviceTarget(project,name)
    requireCondition(bootstrap && newPublicServices.has(name) &&
      JSON.stringify(invoker) === '["public"]', 'New service IAM requires approved operator bootstrap')
    return originals.invokerCreate(project,name,invoker,...rest)
  }
  run.setInvokerUpdate = async (project, name, invoker) => {
    serviceTarget(project,name)
    const expected = proto.getInvokerMembers(invoker,project).sort()
    const policy = await run.getIamPolicy(name)
    const rows = (policy.bindings || []).filter(binding => binding.role === 'roles/run.invoker')
    requireCondition(rows.length === 1 && !rows[0].condition &&
      JSON.stringify([...rows[0].members].sort()) === JSON.stringify(expected),
    'Service IAM differs from approved configuration; owner provisioning required')
  }
  return () => {
    functions.deleteFunction = originals.deleteFunction
    functions.updateFunction = originals.updateFunction
    functions.createFunction = originals.createFunction
    artifacts.checkCleanupPolicy = originals.cleanupCheck
    artifacts.setCleanupPolicies = originals.cleanupSet
    functions.functionFromEndpoint = originals.convert
    resource.setIamPolicy = originals.projectSet
    secrets.setIamPolicy = originals.secretSet
    secrets.setIamPolicy = originals.secretSet
    checks.ensureServiceAgentRoles = originals.agentCheck
    run.setIamPolicy = originals.runSet
    run.setInvokerCreate = originals.invokerCreate
    run.setInvokerUpdate = originals.invokerUpdate
  }
}

function bootstrapSelectors(cli, endpoints) {
  requireCondition(Array.isArray(endpoints) && endpoints.length > 0 &&
    endpoints.every(row => /^[a-z][a-z0-9_-]{0,62}$/.test(row.id) &&
      ['http','event','schedule'].includes(row.kind)) &&
    new Set(endpoints.map(row => row.id)).size === endpoints.length, 'Invalid bootstrap inventory')
  const approved = endpoints.filter(row => row.kind === 'http').map(row => row.id).sort()
  requireCondition(approved.length > 0, 'Empty bootstrap HTTP inventory')
  const only = approved.map(id => 'functions:python_codebase:' + id).join(',')
  const helper = cli('./lib/deploy/functions/functionsDeployHelper.js')
  const filters = helper.getEndpointFilters({only},[{codebase:'python_codebase'}])
  const selected = endpoints.filter(row => helper.endpointMatchesAnyFilter(
    {...row,codebase:'python_codebase'},filters)).map(row => row.id).sort()
  requireCondition(JSON.stringify(selected) === JSON.stringify(approved), 'Ambiguous bootstrap CLI selector')
  return only
}

module.exports = {bootstrapSelectors, validateIdentities, withBuildIdentity, assertProjectBindings, installCliGuards, migrationRetentionAllowed}
