// Preloaded in every fixture-build worker. Record denials even when application
// code catches fetch failures, so a misleading successful build cannot escape.
const fs = require('node:fs')
const net = require('node:net')
const http = require('node:http')
const https = require('node:https')
const tls = require('node:tls')
const path = require('node:path')
const {REQUIRED_BACKEND_READS, backendReadAcceptable} = require(path.join(__dirname,'../config/build-reads.cjs'))

function checkHost(host = 'localhost') {
  if (process.env.MCP_BUILD_MODE === 'release') return
  const normalized = String(host).replace(/^\[|\]$/g,'')
  if (['localhost','127.0.0.1','::1'].includes(normalized)) return
  if (process.env.MCP_BUILD_DENIALS_FILE) fs.appendFileSync(process.env.MCP_BUILD_DENIALS_FILE,`${normalized}\n`)
  throw new Error('External network denied during fixture build')
}
function target(args) {
  const first = args[0]
  if (first instanceof URL || typeof first === 'string' && /^https?:/.test(first)) return new URL(first).hostname
  if (first && typeof first === 'object') return first.hostname || first.host || 'localhost'
  if (typeof first === 'number') return typeof args[1] === 'string' ? args[1] : 'localhost'
  return 'localhost' // local IPC pipes do not resolve cloud hosts
}
for (const [module,name] of [[net,'connect'],[net,'createConnection'],[tls,'connect'],[http,'request'],[http,'get'],[https,'request'],[https,'get']]) {
  const original = module[name]
  module[name] = function(...args) { checkHost(target(args)); return original.apply(this,args) }
}
const originalFetch = globalThis.fetch
globalThis.fetch = async function(input, ...args) {
  const url = new URL(typeof input === 'string' || input instanceof URL ? input : input.url)
  checkHost(url.hostname)
  const base = process.env.BACKEND_BASE_URL ? new URL(process.env.BACKEND_BASE_URL) : null
  const endpoint = url.pathname.split('/').pop()
  const required = base && url.origin === base.origin && REQUIRED_BACKEND_READS.includes(endpoint)
  try {
    const response = await originalFetch.call(this,input,...args)
    if (required) {
      if (!backendReadAcceptable(endpoint,response)) throw new Error('Required backend read failed')
      await response.clone().json()
    }
    return response
  } catch (error) {
    if (required && process.env.MCP_BUILD_FAILURES_FILE) fs.appendFileSync(process.env.MCP_BUILD_FAILURES_FILE,'Required backend read failed\n')
    throw error
  }
}
