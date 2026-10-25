const { test } = require('node:test')
const assert = require('node:assert/strict')
const catalog = require('../../mcp-backend/functions/config/environment_catalog.json')
const { validatePublicRuntime, findForbiddenPublicKeys } = require('../config/runtime-policy.cjs')

test('all four environments select their own resources', () => {
  for (const environment of ['local', 'test', 'staging', 'production']) {
    const config = validatePublicRuntime({ NEXT_PUBLIC_ENV: environment,
      NEXT_PUBLIC_PAYPAL_CLIENT_ID:'fake-sandbox-public-client',
      NEXT_PUBLIC_PAYPAL_LIVE_CLIENT_ID:'fake-live-public-client' }, catalog)
    assert.equal(config.firebase.projectId, catalog.environments[environment].project_id)
  }
})

test('cloud PayPal requires the selected client ID and never accepts sandbox demo IDs', () => {
  for (const env of [
    {NEXT_PUBLIC_ENV:'production',NEXT_PUBLIC_PAYPAL_CLIENT_ID:'sb'},
    {NEXT_PUBLIC_ENV:'production',NEXT_PUBLIC_PAYPAL_LIVE_CLIENT_ID:'sb'},
    {NEXT_PUBLIC_ENV:'production',NEXT_PUBLIC_PAYPAL_LIVE_CLIENT_ID:'   '},
    {NEXT_PUBLIC_ENV:'staging',NEXT_PUBLIC_PAYPAL_LIVE_CLIENT_ID:'fake-live-client'},
    {NEXT_PUBLIC_ENV:'test',NEXT_PUBLIC_PAYPAL_ENV:'sandbox'},
  ]) assert.throws(() => validatePublicRuntime(env,catalog))
})

test('canonical PayPal mode and selected public client ID reach browser config', async () => {
  const {publicRuntimeEnvironment} = require('../config/runtime-policy.cjs')
  const {readFileSync} = require('node:fs')
  const source = readFileSync(require.resolve('../config/paypal.js'),'utf8')
  for (const [environment,mode,clientId] of [
    ['production','production','fake-live-client'],
    ['staging','sandbox','fake-sandbox-client'],
    ['test','fake',null],
  ]) {
    const config = validatePublicRuntime({NEXT_PUBLIC_ENV:environment,
      NEXT_PUBLIC_PAYPAL_CLIENT_ID:'fake-sandbox-client',NEXT_PUBLIC_PAYPAL_LIVE_CLIENT_ID:'fake-live-client'},catalog)
    assert.equal(config.paypal.mode,mode)
    const selected = publicRuntimeEnvironment(config)
    const saved = {...process.env}
    try {
      for (const key of Object.keys(process.env)) if (key.startsWith('NEXT_PUBLIC_')) delete process.env[key]
      Object.assign(process.env,selected)
      const mod = await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64')+'#'+environment)
      assert.equal(mod.isFakePayment,mode === 'fake')
      assert.equal(mod.initialOptions?.['client-id'] ?? null,clientId)
    } finally {
      for (const key of Object.keys(process.env)) if (!(key in saved)) delete process.env[key]
      Object.assign(process.env,saved)
    }
  }
})

test('unknown and legacy environments are rejected without echoing values', () => {
  for (const environment of ['', 'prod', 'development', 'SENTINEL']) {
    assert.throws(() => validatePublicRuntime({NEXT_PUBLIC_ENV: environment}, catalog), error => !error.message.includes('SENTINEL'))
  }
})

test('secret-shaped public variables are rejected and values stay redacted', () => {
  const env = {NEXT_PUBLIC_ENV:'test', NEXT_PUBLIC_PAYPAL_CLIENT_SECRET:'SENTINEL_SECRET', NEXT_PUBLIC_MAILERSEND_API_KEY:'SENTINEL_KEY'}
  assert.deepEqual(findForbiddenPublicKeys(env).sort(), ['NEXT_PUBLIC_MAILERSEND_API_KEY','NEXT_PUBLIC_PAYPAL_CLIENT_SECRET'])
  assert.throws(() => validatePublicRuntime(env,catalog), error => !error.message.includes('SENTINEL'))
})

test('public Firebase API key is browser configuration', () => {
  assert.deepEqual(findForbiddenPublicKeys({NEXT_PUBLIC_FIREBASE_API_KEY:'demo-api-key'}),[])
})

test('project, bucket, backend and emulator mismatches fail closed', () => {
  for (const env of [
    {NEXT_PUBLIC_ENV:'local',NEXT_PUBLIC_FIREBASE_PROJECT_ID:'mcp-website-2a1ad'},
    {NEXT_PUBLIC_ENV:'test',NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET:'mcp-website-dev-39539.appspot.com'},
    {NEXT_PUBLIC_ENV:'staging',NEXT_PUBLIC_BASE_URL:'https://us-central1-mcp-website-2a1ad.cloudfunctions.net'},
    {NEXT_PUBLIC_ENV:'production',NEXT_PUBLIC_BASE_URL:'http://localhost:5001'},
    {NEXT_PUBLIC_ENV:'production',NEXT_PUBLIC_AUTH_EMULATOR_HOST:'127.0.0.1:9099'},
    {NEXT_PUBLIC_ENV:'local',NEXT_PUBLIC_AUTH_EMULATOR_HOST:'auth.googleapis.com:443'},
    {NEXT_PUBLIC_ENV:'test',NEXT_PUBLIC_AUTH_EMULATOR_HOST:''},
    {NEXT_PUBLIC_ENV:'test',NEXT_PUBLIC_BASE_URL:'https://cloud.example.com'},
    {NEXT_PUBLIC_ENV:'test',NEXT_PUBLIC_BASE_URL:'http://127.0.0.1:5001',BACKEND_BASE_URL:'https://cloud.example.com'},
  ]) assert.throws(() => validatePublicRuntime(env,catalog))
})

test('production cannot select PayPal sandbox and local cannot select production', () => {
  assert.throws(() => validatePublicRuntime({NEXT_PUBLIC_ENV:'production',NEXT_PUBLIC_PAYPAL_ENV:'sandbox'},catalog))
  assert.throws(() => validatePublicRuntime({NEXT_PUBLIC_ENV:'test',NEXT_PUBLIC_PAYPAL_ENV:'production'},catalog))
})

test('local defaults point every Firebase capability to emulators', () => {
  const config = validatePublicRuntime({NEXT_PUBLIC_ENV:'local'},catalog)
  assert.equal(config.emulators.auth, '127.0.0.1:9099')
  assert.equal(config.emulators.firestore, '127.0.0.1:8080')
  assert.equal(config.emulators.storage, '127.0.0.1:9199')
  assert.equal(config.emulators.functions, '127.0.0.1:5001')
})
