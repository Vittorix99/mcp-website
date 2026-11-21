const { test } = require('node:test')
const assert = require('node:assert/strict')
const { createRequire } = require('node:module')

const firebaseToolsPackage = require.resolve('firebase-tools/package.json')
const firebaseToolsRequire = createRequire(firebaseToolsPackage)
const { functionFromEndpoint } = firebaseToolsRequire('./lib/gcp/cloudfunctionsv2.js')
const { withBuildIdentity } = require('../../scripts/deployment/cli-guards.cjs')

const project = 'mcp-website-dev-39539'
const identities = {
  DEPLOY_SERVICE_ACCOUNT: `github-deploy@${project}.iam.gserviceaccount.com`,
  BUILD_SERVICE_ACCOUNT: `functions-build@${project}.iam.gserviceaccount.com`,
  RUNTIME_SERVICE_ACCOUNT: `app-runtime@${project}.iam.gserviceaccount.com`,
  WEB_RUNTIME_SERVICE_ACCOUNT: `web-runtime@${project}.iam.gserviceaccount.com`,
}

function manifest(overrides = {}) {
  return {
    environment: 'staging',
    project,
    identities: { ...identities },
    ...overrides,
  }
}

function endpoint(overrides = {}) {
  return {
    platform: 'gcfv2',
    id: 'public_api',
    region: 'us-central1',
    project,
    entryPoint: 'public_api',
    runtime: 'python311',
    codebase: 'python_codebase',
    source: { storageSource: { bucket: 'synthetic-sources', object: 'source.zip' } },
    serviceAccount: identities.RUNTIME_SERVICE_ACCOUNT,
    labels: { release: 'staging-contract' },
    httpsTrigger: {},
    ...overrides,
  }
}

function convert(endpointValue) {
  return functionFromEndpoint(endpointValue)
}

function expectedBuildServiceAccount(email) {
  return `projects/${project}/serviceAccounts/${email}`
}

test('Python endpoint uses build identity for Cloud Build and keeps app runtime identity', () => {
  const originalEndpoint = endpoint()
  const before = structuredClone(originalEndpoint)
  const expected = convert(originalEndpoint)
  const result = withBuildIdentity(originalEndpoint, manifest(), convert)

  assert.equal(result.buildConfig.serviceAccount, expectedBuildServiceAccount(identities.BUILD_SERVICE_ACCOUNT))
  assert.equal(result.serviceConfig.serviceAccountEmail, expected.serviceConfig.serviceAccountEmail)
  assert.equal(result.serviceConfig.serviceAccountEmail, identities.RUNTIME_SERVICE_ACCOUNT)
  assert.deepEqual(result.buildConfig.source, expected.buildConfig.source)
  assert.equal(result.buildConfig.runtime, expected.buildConfig.runtime)
  assert.equal(result.buildConfig.entryPoint, expected.buildConfig.entryPoint)
  assert.deepEqual(result.labels, expected.labels)
  assert.deepEqual(originalEndpoint, before)
})

test('SSR endpoint uses build identity while retaining web runtime and converter metadata', () => {
  const webRuntime = identities.WEB_RUNTIME_SERVICE_ACCOUNT
  const originalEndpoint = endpoint({
    runtime: 'nodejs22',
    codebase: `firebase-frameworks-${project}`,
    serviceAccount: webRuntime,
  })
  const before = structuredClone(originalEndpoint)
  const expected = convert(originalEndpoint)
  const result = withBuildIdentity(originalEndpoint, manifest(), convert)

  assert.equal(result.buildConfig.serviceAccount, expectedBuildServiceAccount(identities.BUILD_SERVICE_ACCOUNT))
  assert.equal(result.serviceConfig.serviceAccountEmail, expected.serviceConfig.serviceAccountEmail)
  assert.equal(result.serviceConfig.serviceAccountEmail, webRuntime)
  assert.deepEqual(result.buildConfig.source, expected.buildConfig.source)
  assert.equal(result.buildConfig.runtime, expected.buildConfig.runtime)
  assert.equal(result.buildConfig.entryPoint, expected.buildConfig.entryPoint)
  assert.deepEqual(result.labels, expected.labels)
  assert.deepEqual(originalEndpoint, before)
})

test('rejects endpoint project, codebase, platform, and runtime identity mismatches', () => {
  assert.throws(() => withBuildIdentity(endpoint({ project: 'mcp-website-2a1ad' }), manifest(), convert))
  assert.throws(() => withBuildIdentity(endpoint({ codebase: 'unexpected' }), manifest(), convert))
  assert.throws(() => withBuildIdentity(endpoint({ platform: 'gcfv1' }), manifest(), convert))
  assert.throws(() => withBuildIdentity(endpoint({ runtime: 'nodejs22' }), manifest(), convert))
  assert.throws(() => withBuildIdentity(endpoint({ serviceAccount: undefined }), manifest(), convert))
  assert.throws(() => withBuildIdentity(endpoint({
    runtime: 'nodejs20',
    codebase: `firebase-frameworks-${project}`,
    serviceAccount: identities.WEB_RUNTIME_SERVICE_ACCOUNT,
  }), manifest(), convert))
})

test('rejects invalid or colliding build identities', () => {
  const buildIdentity = value => manifest({ identities: { ...identities, BUILD_SERVICE_ACCOUNT: value } })
  assert.throws(() => withBuildIdentity(endpoint(), buildIdentity(`functions-build@mcp-website-2a1ad.iam.gserviceaccount.com`), convert))
  assert.throws(() => withBuildIdentity(endpoint(), buildIdentity(identities.RUNTIME_SERVICE_ACCOUNT), convert))
  assert.throws(() => withBuildIdentity(endpoint(), buildIdentity(identities.WEB_RUNTIME_SERVICE_ACCOUNT), convert))
  assert.throws(() => withBuildIdentity(endpoint(), buildIdentity(identities.DEPLOY_SERVICE_ACCOUNT), convert))
  assert.throws(() => withBuildIdentity(endpoint(), buildIdentity(`${project}@developer.gserviceaccount.com`), convert))
})

test('ordinary release adapter installs and restores real converter and IAM guards', async () => {
  const path = require('node:path')
  const {installAdapters} = require('../../scripts/deployment/firebase.cjs')
  const converter = firebaseToolsRequire('./lib/gcp/cloudfunctionsv2.js')
  const resource = firebaseToolsRequire('./lib/gcp/resourceManager.js')
  const python = firebaseToolsRequire('./lib/functions/python.js')
  const before = {convert:converter.functionFromEndpoint,discovery:python.runWithVirtualEnv,set:resource.setIamPolicy}
  const restore = installAdapters(path.resolve(__dirname,'../..'),firebaseToolsRequire,manifest(),'/synthetic/wif.json')
  try {
    assert.equal(converter.functionFromEndpoint(endpoint()).buildConfig.serviceAccount,
      expectedBuildServiceAccount(identities.BUILD_SERVICE_ACCOUNT))
    assert.notEqual(python.runWithVirtualEnv,before.discovery)
    await assert.rejects(resource.setIamPolicy(project,{bindings:[]}),/IAM/)
  } finally { restore() }
  assert.equal(converter.functionFromEndpoint,before.convert)
  assert.equal(python.runWithVirtualEnv,before.discovery)
  assert.equal(resource.setIamPolicy,before.set)
})
