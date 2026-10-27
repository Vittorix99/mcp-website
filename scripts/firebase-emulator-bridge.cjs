// Firebase CLI 14.26.0 drops custom parent variables during Python discovery.
// Forward only the guard-validated, non-secret emulator profile. Never patch
// installed dependencies or relax the application's explicit MCP_ENV check.
const path = require('node:path')

function forwardDiscoveryEnvironment(parent,child) {
  if (!['local','test'].includes(parent.MCP_ENV) || parent.GCLOUD_PROJECT !== `demo-mcp-${parent.MCP_ENV}`) {
    throw new Error('Discovery bridge requires an explicit local/test demo identity')
  }
  const profile = {}
  for (const key of [
    'MCP_ENV','GCLOUD_PROJECT','GOOGLE_CLOUD_PROJECT','STORAGE_BUCKET',
    'FIRESTORE_EMULATOR_HOST','FIREBASE_AUTH_EMULATOR_HOST','STORAGE_EMULATOR_HOST','PUBSUB_EMULATOR_HOST',
    'PAYPAL_MODE','MAIL_MODE','SENDER_MODE','PASS2U_MODE','GENDER_MODE','SOUNDCLOUD_MODE',
  ]) if (parent[key] !== undefined) profile[key] = parent[key]
  const forwarded = {...profile,...child}
  // CLI-generated cloud credentials are unnecessary for the complete emulator
  // profile and must not defeat the application's no-cloud-credential policy.
  for (const key of ['GOOGLE_APPLICATION_CREDENTIALS','FIREBASE_SERVICE_ACCOUNT_JSON','FIREBASE_SERVICE_ACCOUNT']) delete forwarded[key]
  return forwarded
}

if (process.env.MCP_ENABLE_DISCOVERY_BRIDGE === '1') {
  const cliRoot = path.join(__dirname,'../mcp-website/node_modules/firebase-tools')
  if (require(path.join(cliRoot,'package.json')).version !== '14.26.0') throw new Error('Review discovery bridge before changing Firebase CLI version')
  const python = require(path.join(cliRoot,'lib/functions/python.js'))
  const original = python.runWithVirtualEnv
  python.runWithVirtualEnv = function(args,cwd,envs,...rest) {
    return original(args,cwd,forwardDiscoveryEnvironment(process.env,envs),...rest)
  }
}

module.exports = {forwardDiscoveryEnvironment}
