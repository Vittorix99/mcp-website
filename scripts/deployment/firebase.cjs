// Version-pinned adapter for Firebase CLI discovery and its framework builder.
// Provider secret payloads never enter the deploy process or build environment.
const fs = require('node:fs')
const path = require('node:path')
const {createRequire} = require('node:module')
const {execFileSync} = require('node:child_process')

async function probeReleaseAccess(cli, manifest) {
  console.error('RELEASE_PROBE_PHASE=firebase-auth')
  await cli('./lib/requireAuth.js').requireAuth({project:manifest.project,nonInteractive:true})
  console.error('RELEASE_PROBE_PHASE=hosting-read')
  const sites = await cli('./lib/hosting/api.js').listSites(manifest.project)
  if (!sites.some(site => site.name?.split('/').at(-1) === manifest.project)) throw new Error('Expected Hosting site not found')
  const iam = cli('./lib/gcp/iam.js')
  console.error('RELEASE_PROBE_PHASE=project-permissions')
  const permissions = ['run.services.get','run.services.update','firebasehosting.sites.get','firebasehosting.sites.update',
    'cloudfunctions.functions.get','cloudfunctions.functions.update','apikeys.keys.getKeyString']
  const result = await iam.testIamPermissions(manifest.project,permissions)
  if (!result.passed) {
    console.error('RELEASE_PERMISSION_DENIED')
    for (const permission of permissions.filter(p => result.missing?.includes(p))) {
      console.error(`RELEASE_MISSING_PERMISSION=${permission}`)
    }
    throw new Error('Missing permissions for release probe')
  }
  console.error('RELEASE_PROBE_PHASE=web-config')
  await cli('./lib/fetchWebSetup.js').fetchWebSetup({project:manifest.project})
  console.error('RELEASE_PROBE_PHASE=admin-config')
  await cli('./lib/functionsConfig.js').getFirebaseConfig({project:manifest.project})
  console.error('RELEASE_PROBE_PHASE=account-actas')
  for (const key of ['BUILD_SERVICE_ACCOUNT','RUNTIME_SERVICE_ACCOUNT','WEB_RUNTIME_SERVICE_ACCOUNT']) {
    console.error(`RELEASE_ACCOUNT_ROLE=${key}`)
    const access = await iam.testResourceIamPermissions('https://iam.googleapis.com','v1',
      `projects/${manifest.project}/serviceAccounts/${manifest.identities[key]}`,['iam.serviceAccounts.actAs'])
    if (!access.passed) {
      console.error('RELEASE_PERMISSION_DENIED')
      console.error('RELEASE_MISSING_PERMISSION=iam.serviceAccounts.actAs')
      throw new Error('Missing permissions for dedicated service account')
    }
  }
  return {mode:'read-only',firebase_auth:true,hosting_read:true,web_config_read:true,
    admin_config_read:true,project_permissions:true,account_actas:true}
}

// Non-secret locator of a denied Google API call: host plus method path with every resource id masked.
const API_PATH_WORDS = new Set(['v1','v1beta1','v1beta2','v2','v2beta','v2alpha','projects','locations','functions','services',
  'sites','versions','releases','channels','serviceAccounts','secrets','repositories','apps','webApps','config','operations',
  'keys','namespaces','policy','buckets','objects','files','domains','apiKeys','iam','roles','permissions'])
function apiTarget(error) {
  for (let depth = 0; error && depth < 4; depth++, error = error.original || error.cause) {
    // firebase-tools carries the failing URL in the message ("Request to <url> had HTTP Error"); only that URL is read.
    const fromMessage = typeof error.message === 'string' ?
      error.message.match(/^Request to (https:\/\/[a-z0-9-]+\.googleapis\.com\/\S*) had HTTP Error/)?.[1] : undefined
    const raw = error.context?.response?.url || error.response?.url || fromMessage
    if (typeof raw !== 'string') continue
    try {
      const url = new URL(raw)
      if (!/^[a-z0-9-]+\.googleapis\.com$/.test(url.hostname)) continue
      const path = url.pathname.split('/').filter(Boolean).slice(0, 12).map(part => {
        const [name, verb] = part.split(':')
        const masked = API_PATH_WORDS.has(name) ? name : '*'
        return /^[A-Za-z][A-Za-z0-9]{0,40}$/.test(verb || '') ? masked + ':' + verb : masked
      }).join('/')
      return url.hostname + '/' + path
    } catch {}
  }
}

// Static messages owned by cli-guards.cjs and IAM permission names (service.resource.verb) quoted by the CLI.
const GUARD_MESSAGE = /^(Missing permissions on configured service account|Required project IAM binding is missing|Secret IAM writes require|Project IAM writes require|Service IAM (?:writes require|differs from)|Artifact cleanup policy changes require|New service IAM requires|Missing function build configuration|Unexpected [A-Za-z ]{1,40}|Unapproved [A-Za-z ]{1,40}|Bootstrap [A-Za-z ]{1,60}|Migration [A-Za-z ]{1,60})[A-Za-z ;,'().-]{0,100}$/
const PERMISSION_NAME = /\b(?:cloudfunctions|run|iam|secretmanager|artifactregistry|cloudbuild|eventarc|cloudscheduler|pubsub|storage|firebase|firebasehosting|firebaseextensions|serviceusage|resourcemanager|apikeys|cloudbilling|logging)\.[a-zA-Z]+\.[a-zA-Z]+\b/g
function guardDetails(error) {
  let guard
  const permissions = new Set()
  for (let depth = 0; error && depth < 4; depth++, error = error.original || error.cause) {
    const message = typeof error.message === 'string' ? error.message : ''
    if (!guard && GUARD_MESSAGE.test(message)) guard = message
    for (const match of message.matchAll(PERMISSION_NAME)) if (permissions.size < 8) permissions.add(match[0])
  }
  return {guard, permissions: [...permissions]}
}

// Staging only: first line of the failing error with identifiers and numbers masked, to locate unknown denials.
function maskedMessage(error) {
  try {
    if (JSON.parse(require('node:fs').readFileSync(process.env.MCP_RELEASE_CONFIG, 'utf8')).environment !== 'staging') return
  } catch { return }
  const lines = []
  for (let depth = 0; error && depth < 4; depth++, error = error.original || error.cause) {
    const line = typeof error.message === 'string' ? error.message.split('\n')[0] : ''
    if (!line) continue
    const masked = line.replace(/https?:\/\/\S+/g, url => url.replace(/^(https?:\/\/[a-z0-9.-]+)(\/[^?\s]*)?.*$/, (_, host, path) =>
        host + (path || '').split('/').map(part => /^[a-z]{2,20}$/.test(part) || /^v\d/.test(part) ? part : (part ? '*' : '')).join('/')))
      .replace(/[A-Za-z0-9_-]{16,}/g, '*').replace(/\d{3,}/g, '*').replace(/[^A-Za-z0-9 _.,:;/*()'\[\]-]/g, '').slice(0, 200)
    if (masked && !lines.includes(masked)) lines.push(masked)
  }
  return lines.slice(0, 3).join(' | ').slice(0, 400) || undefined
}

function reportEntryFailure(error) {
  const message = maskedMessage(error)
  if (message) console.error(`RELEASE_MESSAGE=${message}`)
  const details = guardDetails(error)
  if (details.guard) console.error(`RELEASE_GUARD=${details.guard}`)
  if (details.permissions.length) console.error(`RELEASE_PERMISSIONS=${details.permissions.join(',')}`)
  const target = apiTarget(error)
  if (target) console.error(`RELEASE_API_TARGET=${target}`)
  // FirebaseError defaults to status 500: report SDK status, not a proven HTTP response.
  let lastStatus
  const kind = ['Error','FirebaseError','TypeError','SyntaxError','RangeError'].includes(error?.name) ? error.name : 'unknown'
  console.error(`RELEASE_ERROR_TYPE=${kind}`)
  for (let depth = 0; error && depth < 4; depth++, error = error.original || error.cause) {
    const status = error.status || error.response?.status
    if (Number.isInteger(status) && status >= 400 && status <= 599) {
      lastStatus = status
    }
  }
  if (lastStatus) console.error(`RELEASE_SDK_STATUS=${lastStatus}`)
  console.error('Guarded Firebase release failed; arbitrary diagnostics withheld')
}

function installFailureReporter(cli) {
  const client = cli('./lib/index.js')
  const original = client.errorOut
  client.errorOut = function(error) {
    reportEntryFailure(error)
    return original.call(this,error)
  }
  return () => {client.errorOut=original}
}

function releaseProfile(cli, manifest, endpoints) {
  if (manifest.environment === 'production') return {only:'functions:python_codebase',guards:{}}
  if (manifest.environment !== 'staging') throw new Error('Invalid release environment')
  const only = require('./cli-guards.cjs').bootstrapSelectors(cli,endpoints)
  return {only,guards:{httpUpdatesOnly:true,
    approvedFunctions:endpoints.filter(row => row.kind === 'http').map(row => row.id)}}
}

function validateFederation(credential, manifest) {
  const expected = 'https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/' + manifest.identities.DEPLOY_SERVICE_ACCOUNT + ':generateAccessToken'
  if (credential.type !== 'external_account' ||
      credential.audience !== '//iam.googleapis.com/' + manifest.wif_provider ||
      decodeURI(credential.service_account_impersonation_url || '') !== expected ||
      !credential.credential_source || credential.credential_source.executable || credential.private_key) {
    throw new Error('Invalid release federation')
  }
}

function discoveryEnvironment(manifest, child, credentialPath) {
  if (!['staging','production'].includes(manifest.environment) ||
      child.GCLOUD_PROJECT && child.GCLOUD_PROJECT !== manifest.project ||
      child.GOOGLE_CLOUD_PROJECT && child.GOOGLE_CLOUD_PROJECT !== manifest.project) {
    throw new Error('Invalid release discovery project')
  }
  return {...child, ...manifest.backend, GCLOUD_PROJECT:manifest.project,
    GOOGLE_CLOUD_PROJECT:manifest.project, GOOGLE_APPLICATION_CREDENTIALS:credentialPath}
}

// firebase-tools 14.26 ignores the exit code of `next build` and would otherwise package a
// stale .next (e.g. an old fixture build). Remove it first and abort the deploy if the build fails.
function spawnReleaseBuild(originalSpawn, replacement, options, root, {remove = fs.rmSync, fail = () => process.exit(1)} = {}) {
  remove(path.join(root,'mcp-website/.next'),{recursive:true,force:true})
  const child = originalSpawn(replacement.executable,replacement.args,options)
  child.once('exit',(code,signal) => {
    if (code !== 0 || signal) {
      console.error('Release build failed; deployment aborted')
      fail()
    }
  })
  return child
}

function releaseBuildInvocation(executable, args, options, root) {
  if (path.resolve(options.cwd || '') !== path.join(root,'mcp-website') ||
      !/[/\\]next(?:\.cmd)?$/.test(executable) || args.length !== 1 || args[0] !== 'build') return null
  return {executable:process.execPath, args:[path.join(root,'mcp-website/scripts/build-safe.mjs'),'--release']}
}

function installAdapters(root, cliRequire, manifest, credentialPath, options = {}) {
  const restoreGuards = require('./cli-guards.cjs').installCliGuards(cliRequire,manifest,options)
  const python = cliRequire('./lib/functions/python.js')
  const originalDiscovery = python.runWithVirtualEnv
  python.runWithVirtualEnv = (command,cwd,env,...rest) => originalDiscovery(command,cwd,
    discoveryEnvironment(manifest,env,credentialPath),...rest)
  // Firebase 14.26.0 ignores custom package.json build commands. Substitute only
  // its Next build spawn, preserving framework analysis and SSR code generation.
  const crossSpawn = cliRequire('cross-spawn')
  const originalSpawn = crossSpawn.spawn
  crossSpawn.spawn = function(executable,args,options) {
    const replacement = releaseBuildInvocation(executable,args,options,root)
    return replacement ? spawnReleaseBuild(originalSpawn,replacement,options,root)
      : originalSpawn(executable,args,options)
  }
  return () => {
    python.runWithVirtualEnv = originalDiscovery
    crossSpawn.spawn = originalSpawn
    restoreGuards()
  }
}

// firebase-tools runs 40 parallel function creations; on the first release that
// exceeded Cloud Run's regional write quota and failed 77 of 130 functions
// inside the cloud operations (not retryable by the client). Keep it low; shared by the
// bootstrap and the ordinary release so neither can exceed the quota.
const DEPLOY_CONCURRENCY = 3
function limitDeployConcurrency(cli, limit = DEPLOY_CONCURRENCY) {
  const executor = cli('./lib/deploy/functions/release/executor')
  const Original = executor.QueueExecutor
  if (typeof Original !== 'function' || !Number.isInteger(limit) || limit < 1 || limit > 5) throw new Error('Invalid deploy concurrency')
  executor.QueueExecutor = class extends Original {
    constructor(options) { super({...options, concurrency: Math.min(options?.concurrency ?? limit, limit)}) }
  }
}
async function main() {
  if (process.versions.node.split('.')[0] !== '22') throw new Error('Release requires Node.js 22')
  const root = path.resolve(__dirname,'../..')
  const cliRoot = path.join(root,'mcp-website/node_modules/firebase-tools')
  if (require(path.join(cliRoot,'package.json')).version !== '14.26.0') throw new Error('Review release adapter before changing Firebase CLI')
  const expectedPath = path.join(root,'.local/release/config.json')
  if (process.env.MCP_RELEASE_CONFIG !== expectedPath) throw new Error('Invalid release configuration path')
  const manifest = JSON.parse(fs.readFileSync(expectedPath,'utf8'))
  const credentialPath = process.env.GOOGLE_APPLICATION_CREDENTIALS
  if (!credentialPath) throw new Error('Missing ephemeral federation configuration')
  validateFederation(JSON.parse(fs.readFileSync(credentialPath,'utf8')), manifest)
  const args = process.argv.slice(2)
  if (args.length === 1 && args[0] === 'validate') return
  if (!['backend','backend-check','hosting','probe'].includes(args[0]) || args.length !== 1) throw new Error('Select a scoped release target')
  const cliRequire = createRequire(path.join(cliRoot,'package.json'))
  if (args[0] === 'probe') {
    require('./cli-guards.cjs').validateIdentities(manifest)
    console.log(JSON.stringify(await probeReleaseAccess(cliRequire,manifest)))
    return
  }
  const endpoints = manifest.environment === 'staging' ? JSON.parse(execFileSync(
    path.join(root,'.venv/bin/python'), ['-c',
      'import json; from bootstrap_staging import discover_endpoints; print(json.dumps(discover_endpoints()))'],
    {cwd:path.join(root,'scripts/deployment'),encoding:'utf8'})) : undefined
  const profile = releaseProfile(cliRequire,manifest,endpoints)
  installAdapters(root,cliRequire,manifest,credentialPath,profile.guards)
  limitDeployConcurrency(cliRequire)
  Object.assign(process.env, manifest.frontend)
  process.env.__NEXT_PROCESSED_ENV = 'true'
  const cli = path.join(cliRoot,'lib/bin/firebase.js')
  process.argv = [process.execPath,cli,'deploy','--non-interactive','--project',manifest.project,
    '--config',path.join(root,'firebase.release.generated.json'),'--only',
    args[0] === 'hosting' ? 'hosting' : profile.only,
    // backend-check runs the CLI's validation phase only: nothing is built, uploaded or updated.
    ...(args[0] === 'backend-check' ? ['--dry-run'] : [])]
  installFailureReporter(cliRequire)
  require(cli)
}

module.exports = {installFailureReporter, probeReleaseAccess, reportEntryFailure, releaseProfile, installAdapters, limitDeployConcurrency, DEPLOY_CONCURRENCY, validateFederation, discoveryEnvironment, releaseBuildInvocation, spawnReleaseBuild}
if (require.main === module) {
  main().catch(error => { reportEntryFailure(error); process.exitCode = 1 })
}
