// Version-pinned adapter for Firebase CLI discovery and its framework builder.
// Provider secret payloads never enter the deploy process or build environment.
const fs = require('node:fs')
const path = require('node:path')
const {createRequire} = require('node:module')
const {execFileSync} = require('node:child_process')

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
function main() {
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
  if (!['backend','hosting'].includes(args[0]) || args.length !== 1) throw new Error('Select a scoped release target')
  const cliRequire = createRequire(path.join(cliRoot,'package.json'))
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
    args[0] === 'backend' ? profile.only : 'hosting']
  require(cli)
}

module.exports = {releaseProfile, installAdapters, limitDeployConcurrency, DEPLOY_CONCURRENCY, validateFederation, discoveryEnvironment, releaseBuildInvocation, spawnReleaseBuild}
if (require.main === module) {
  try { main() } catch { console.error('Guarded Firebase release failed'); process.exitCode = 1 }
}
