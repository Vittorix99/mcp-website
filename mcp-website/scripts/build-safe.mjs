import {spawn} from 'node:child_process'
import {existsSync, mkdtempSync, readFileSync, rmSync} from 'node:fs'
import {tmpdir} from 'node:os'
import path from 'node:path'
import {fileURLToPath} from 'node:url'
import {createRequire} from 'node:module'
import {startBuildFixtureServer} from './build-fixture-server.mjs'

const require = createRequire(import.meta.url)
const catalog = require('../../mcp-backend/functions/config/environment_catalog.json')
const {validatePublicRuntime, publicRuntimeEnvironment} = require('../config/runtime-policy.cjs')
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..')
const release = process.argv.includes('--release')

async function main() {
  if (process.versions.node.split('.')[0] !== '20') throw new Error('Build requires Node.js 20')
  if (release && existsSync(path.join(root,'.env.local'))) throw new Error('Release build rejects .env.local; inject approved environment explicitly')
  let server
  const scratch = mkdtempSync(path.join(tmpdir(),'mcp-build-'))
  try {
    const env = {}
    for (const key of ['PATH','HOME','TMPDIR','SystemRoot','WINDIR','CI']) {
      if (process.env[key] !== undefined) env[key] = process.env[key]
    }
    env.NODE_ENV = 'production'
    env.NEXT_TELEMETRY_DISABLED = '1'
    // Next 15's dotenv loader honors this flag; source is lockfile-pinned.
    // All public values are supplied explicitly below, including in workers.
    env.__NEXT_PROCESSED_ENV = 'true'
    env.MCP_BUILD_MODE = release ? 'release' : 'fixture'
    env.MCP_BUILD_FAILURES_FILE = path.join(scratch,'failures.log')
    env.NODE_OPTIONS = `--require=${JSON.stringify(path.join(root,'scripts/build-network-guard.cjs'))}`
    let config
    if (release) {
      config = validatePublicRuntime(process.env,catalog)
      if (!['staging','production'].includes(config.environment)) throw new Error('Release requires staging or production')
      if (!config.firebase.apiKey || !config.firebase.appId) throw new Error('Release requires public Firebase API key and app ID')
      for (const [key,value] of Object.entries(process.env)) {
        if (key.startsWith('NEXT_PUBLIC_')) env[key] = value
      }
    } else {
      server = await startBuildFixtureServer()
      config = validatePublicRuntime({NEXT_PUBLIC_ENV:'test',NEXT_PUBLIC_BASE_URL:server.baseUrl},catalog)
      env.NEXT_PUBLIC_ENABLE_ANALYTICS = 'false'
      env.NEXT_PUBLIC_PAYPAL_ENV = 'fake'
      env.NEXT_PUBLIC_PAYPAL_CLIENT_ID = 'sb'
      env.MCP_BUILD_DENIALS_FILE = path.join(scratch,'denials.log')
    }
    Object.assign(env,publicRuntimeEnvironment(config))
    env.BACKEND_BASE_URL = config.backendUrl
    for (const endpoint of ['get_all_events','get_next_event','get_membership_price_public','get_published_radio_episodes','get_latest_radio_episode','get_radio_seasons']) {
      const response = await fetch(`${config.backendUrl}/${endpoint}`)
      if (!response.ok) throw new Error(`Required build backend read failed: ${endpoint}`)
      await response.json()
    }
    const exitCode = await new Promise((resolve,reject) => {
      const child = spawn(process.execPath,[require.resolve('next/dist/bin/next'),'build'],{cwd:root,env,stdio:'inherit'})
      child.once('error',reject)
      child.once('exit',(code,signal) => resolve(signal ? 1 : code ?? 1))
    })
    if (server?.unexpectedRequests.length) throw new Error('Fixture build requested an undeclared backend endpoint')
    if (env.MCP_BUILD_DENIALS_FILE && existsSync(env.MCP_BUILD_DENIALS_FILE) && readFileSync(env.MCP_BUILD_DENIALS_FILE,'utf8').trim()) throw new Error('Fixture build attempted external network access')
    if (existsSync(env.MCP_BUILD_FAILURES_FILE) && readFileSync(env.MCP_BUILD_FAILURES_FILE,'utf8').trim()) throw new Error('Required build backend read failed')
    process.exitCode = exitCode
  } finally {
    if (server) await server.close()
    rmSync(scratch,{recursive:true,force:true})
  }
}

main().catch(error => { console.error(error.message); process.exitCode = 1 })
