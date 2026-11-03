import {parse} from 'acorn'
import {readFileSync} from 'node:fs'
import {execFileSync} from 'node:child_process'
import path from 'node:path'
import {fileURLToPath,pathToFileURL} from 'node:url'

// Known gaps, not verified contracts. Remove each exception when its reference or implementation changes.
export const LEGACY_API_GAPS = {
  newsletter_participants:'No backend export; no named consumer found. See docs/reviews/WS2_API_REFERENCE_AUDIT.md',
  signup_request:'Legacy signup services; UI reachability not established. See docs/reviews/WS2_API_REFERENCE_AUDIT.md',
  get_all_questions:'Legacy questions service; UI reachability not established. See docs/reviews/WS2_API_REFERENCE_AUDIT.md',
  admin_upload_event_photo:'No backend export; no named consumer found. See docs/reviews/WS2_API_REFERENCE_AUDIT.md',
}

export function readFrontendRoutes(source) {
  const tree = parse(source,{ecmaVersion:'latest',sourceType:'module'})
  const declarations = tree.body.flatMap(node => node.type === 'ExportNamedDeclaration'
    && node.declaration?.type === 'VariableDeclaration' ? node.declaration.declarations : [])
  const endpointDeclarations = declarations.filter(node => node.id.type === 'Identifier' && node.id.name === 'endpoints')
  if (endpointDeclarations.length !== 1) throw new Error('Expected one exported endpoints object')
  const routes = new Map()
  function visit(node,prefix = '') {
    if (node?.type !== 'ObjectExpression') throw new Error(`Unsupported API object: ${prefix}`)
    const keys = new Set()
    for (const property of node.properties) {
      if (property.type !== 'Property' || property.computed || property.method || property.kind !== 'init') {
        throw new Error(`Unsupported API property: ${prefix}`)
      }
      const key = property.key.type === 'Identifier' ? property.key.name : property.key.value
      if (typeof key !== 'string' || !/^[A-Za-z_$][\w$]*$/.test(key) || keys.has(key)) {
        throw new Error(`Invalid or duplicate API property: ${prefix}`)
      }
      keys.add(key)
      const location = prefix ? `${prefix}.${key}` : key
      const value = property.value
      if (value.type === 'ObjectExpression') { visit(value,location); continue }
      if (value.type !== 'CallExpression' || value.callee.type !== 'Identifier' || value.callee.name !== 'make'
        || value.arguments.length !== 1 || value.arguments[0].type !== 'Literal'
        || typeof value.arguments[0].value !== 'string' || !/^[a-z][a-z0-9_]*$/.test(value.arguments[0].value)) {
        throw new Error(`Unsupported API route: ${location}`)
      }
      routes.set(location,value.arguments[0].value)
    }
  }
  visit(endpointDeclarations[0].init)
  if (!routes.size) throw new Error('API route map is empty')
  return routes
}

export function checkApiContracts(routes,exports,legacy) {
  const result = {errors:[],legacy:[]}
  for (const [reference,slug] of routes) {
    if (exports.has(slug)) continue
    if (Object.hasOwn(legacy,slug)) result.legacy.push(`${reference}: ${slug} — ${legacy[slug]}`)
    else result.errors.push(`${reference}: missing HTTP export ${slug}`)
  }
  for (const slug of Object.keys(legacy)) {
    if (exports.has(slug) || ![...routes.values()].includes(slug)) {
      result.errors.push(`Remove expired legacy exception: ${slug}`)
    }
  }
  return result
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  try {
    const root = fileURLToPath(new URL('../../',import.meta.url))
    const routes = readFrontendRoutes(readFileSync(path.join(root,'mcp-website/config/endpoints.js'),'utf8'))
    const exports = new Set(JSON.parse(execFileSync(path.join(root,'.venv/bin/python'),[
      path.join(root,'scripts/contracts/export_http_endpoints.py'),'--root',root,
    ],{encoding:'utf8',stdio:['ignore','pipe','pipe']})))
    const result = checkApiContracts(routes,exports,LEGACY_API_GAPS)
    for (const gap of result.legacy) console.log(`LEGACY: ${gap}`)
    for (const error of result.errors) console.error(error)
    console.log(`API references: ${routes.size}; HTTP exports: ${exports.size}; legacy references: ${result.legacy.length}; errors: ${result.errors.length}`)
    process.exitCode = result.errors.length ? 1 : 0
  } catch {
    console.error('API contract inventory failed; check source syntax, supported route structure and Python environment')
    process.exitCode = 1
  }
}
