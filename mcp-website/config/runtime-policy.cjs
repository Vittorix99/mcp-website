const forbidden = /(SECRET|PRIVATE_?KEY|TOKEN|PASSWORD|CREDENTIAL|API_?KEY)/i

function findForbiddenPublicKeys(environ) {
  return Object.keys(environ).filter(key => key.startsWith('NEXT_PUBLIC_') &&
    key !== 'NEXT_PUBLIC_FIREBASE_API_KEY' && forbidden.test(key))
}

function fail(key) { throw new Error(`Unsafe or invalid public runtime setting: ${key}`) }
function loopback(host) { return ['localhost','127.0.0.1','[::1]','::1'].includes(host) }
function host(value, key) {
  try {
    const url = new URL(`http://${value}`)
    if (!value || !loopback(url.hostname) || !url.port || url.username || url.password ||
        url.pathname !== '/' || url.search || url.hash) fail(key)
    return value
  } catch { fail(key) }
}
function backend(value, key, offline) {
  try {
    const url = new URL(value)
    if (!['http:','https:'].includes(url.protocol) || url.username || url.password ||
        (offline ? !loopback(url.hostname) : url.protocol !== 'https:' || loopback(url.hostname))) fail(key)
    return value.replace(/\/$/,'')
  } catch { fail(key) }
}

function validatePublicRuntime(environ, catalog) {
  const badKeys = findForbiddenPublicKeys(environ)
  if (badKeys.length) fail(badKeys.join(', '))
  const environment = environ.NEXT_PUBLIC_ENV
  if (!['local','test','staging','production'].includes(environment)) fail('NEXT_PUBLIC_ENV')
  if (catalog.schema_version !== 1) fail('environment_catalog schema_version')
  const selected = catalog.environments[environment]
  const offline = ['local','test'].includes(environment)
  for (const [key, wanted] of [
    ['NEXT_PUBLIC_FIREBASE_PROJECT_ID',selected.project_id],
    ['NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET',selected.storage_bucket],
  ]) if (environ[key] !== undefined && environ[key] !== wanted) fail(key)
  const backendUrl = backend(environ.NEXT_PUBLIC_BASE_URL ?? environ.BACKEND_BASE_URL ?? selected.backend_url, 'NEXT_PUBLIC_BASE_URL', offline)
  if (environ.BACKEND_BASE_URL !== undefined && backend(environ.BACKEND_BASE_URL,'BACKEND_BASE_URL',offline) !== backendUrl) fail('BACKEND_BASE_URL')
  if (!offline && backendUrl !== selected.backend_url) fail('NEXT_PUBLIC_BASE_URL')
  const emulators = {}
  for (const [name,key,defaultValue] of [
    ['auth','NEXT_PUBLIC_AUTH_EMULATOR_HOST',selected.emulators.auth],
    ['firestore','NEXT_PUBLIC_FIRESTORE_EMULATOR_HOST',selected.emulators.firestore],
    ['storage','NEXT_PUBLIC_STORAGE_EMULATOR_HOST',selected.emulators.storage],
    ['functions','NEXT_PUBLIC_FUNCTIONS_EMULATOR_HOST',offline ? '127.0.0.1:5001' : undefined],
  ]) {
    const value = environ[key] ?? defaultValue
    if (offline) emulators[name] = host(value,key)
    else if (value) fail(key)
  }
  const paypalMode = offline ? 'fake' : environment === 'staging' ? 'sandbox' : 'production'
  if (environ.NEXT_PUBLIC_PAYPAL_ENV !== undefined && environ.NEXT_PUBLIC_PAYPAL_ENV !== paypalMode) fail('NEXT_PUBLIC_PAYPAL_ENV')
  const paypalClientKey = environment === 'production' ? 'NEXT_PUBLIC_PAYPAL_LIVE_CLIENT_ID' : 'NEXT_PUBLIC_PAYPAL_CLIENT_ID'
  const paypalClientId = offline ? '' : (environ[paypalClientKey] || '').trim()
  if (!offline && (!paypalClientId || paypalClientId === 'sb')) fail(paypalClientKey)
  const authDomain = environ.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || `${selected.project_id}.firebaseapp.com`
  if (authDomain !== `${selected.project_id}.firebaseapp.com`) fail('NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN')
  return {
    environment, backendUrl, emulators, paypal: {mode:paypalMode, clientId:paypalClientId},
    firebase: {
      projectId: selected.project_id, storageBucket: selected.storage_bucket, authDomain,
      apiKey: environ.NEXT_PUBLIC_FIREBASE_API_KEY || (offline ? 'demo-api-key' : ''),
      appId: environ.NEXT_PUBLIC_FIREBASE_APP_ID || (offline ? '1:123456789:web:localfixture' : ''),
      messagingSenderId: environ.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || '',
      measurementId: environ.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID || '',
    },
  }
}

function publicRuntimeEnvironment(config) {
  return {
    NEXT_PUBLIC_ENV: config.environment,
    NEXT_PUBLIC_PAYPAL_ENV: config.paypal.mode,
    NEXT_PUBLIC_PAYPAL_CLIENT_ID: config.paypal.mode === 'sandbox' ? config.paypal.clientId : '',
    NEXT_PUBLIC_PAYPAL_LIVE_CLIENT_ID: config.paypal.mode === 'production' ? config.paypal.clientId : '',
    NEXT_PUBLIC_BASE_URL: config.backendUrl,
    NEXT_PUBLIC_FIREBASE_PROJECT_ID: config.firebase.projectId,
    NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET: config.firebase.storageBucket,
    NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN: config.firebase.authDomain,
    NEXT_PUBLIC_FIREBASE_API_KEY: config.firebase.apiKey,
    NEXT_PUBLIC_FIREBASE_APP_ID: config.firebase.appId,
    NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID: config.firebase.messagingSenderId,
    NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID: config.firebase.measurementId,
    NEXT_PUBLIC_AUTH_EMULATOR_HOST: config.emulators.auth || '',
    NEXT_PUBLIC_FIRESTORE_EMULATOR_HOST: config.emulators.firestore || '',
    NEXT_PUBLIC_STORAGE_EMULATOR_HOST: config.emulators.storage || '',
    NEXT_PUBLIC_FUNCTIONS_EMULATOR_HOST: config.emulators.functions || '',
  }
}

module.exports = {validatePublicRuntime, findForbiddenPublicKeys, publicRuntimeEnvironment}
