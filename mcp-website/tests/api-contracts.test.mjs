import assert from 'node:assert/strict'
import {execFileSync,spawnSync} from 'node:child_process'
import {mkdtempSync,mkdirSync,readFileSync,writeFileSync,rmSync} from 'node:fs'
import {tmpdir} from 'node:os'
import path from 'node:path'
import {fileURLToPath} from 'node:url'
import test from 'node:test'

const root = fileURLToPath(new URL('../../',import.meta.url))
import * as checker from '../scripts/check-api-contracts.mjs'

test('CLI reports no legacy references and no API contract errors',() => {
  const output = execFileSync(process.execPath,[path.join(root,'mcp-website/scripts/check-api-contracts.mjs')],{encoding:'utf8'})
  assert.doesNotMatch(output,/^LEGACY:/m)
  assert.match(output,/legacy references: 0; errors: 0/)
})

test('reads every nested route and retains both references to the same endpoint',() => {
  const routes = checker.readFrontendRoutes('export const endpoints = {list:make("events"), admin:{list:make("events")}}')
  assert.deepEqual([...routes],[['list','events'],['admin.list','events']])
})

test('rejects dynamic, malformed, duplicate or missing endpoint definitions instead of skipping them',() => {
  for (const source of [
    'export const endpoints = {list:make(variable)}',
    'export const endpoints = {list:make("events"), list:make("other")}',
    'export const endpoints = {...shared}',
    'export const endpoints = {[key]:make("events")}',
    'export const endpoints = {list:other("events")}',
    'export const endpoints = {list:make("")}',
    'export const endpoints = {',
    'export const unrelated = {}',
  ]) assert.throws(() => checker.readFrontendRoutes(source))
})

test('rejects endpoint mutations and aliases outside the static map',() => {
  for (const mutation of [
    'endpoints.extra = make("missing_new_endpoint")',
    'Object.assign(endpoints,{extra:make("missing_new_endpoint")})',
    'const alias = endpoints; alias.extra = make("missing_new_endpoint")',
  ]) assert.throws(() => checker.readFrontendRoutes(`export const endpoints = {list:make("events")}; ${mutation}`))
})

test('flags new missing references while naming only exact known legacy exceptions',() => {
  const result = checker.checkApiContracts(new Map([
    ['public.list','events'],['old','legacy'],['admin.one','typo'],['admin.two','typo'],
  ]),new Set(['events']),{legacy:'Known unimplemented feature'})
  assert.equal(result.errors.length,2)
  assert.match(result.errors[0],/admin.one.*typo/)
  assert.match(result.errors[1],/admin.two.*typo/)
  assert.equal(result.legacy.length,1)
  assert.match(result.legacy[0],/old.*legacy.*Known unimplemented feature/)
})

test('rejects legacy exceptions after endpoint restoration or reference removal',() => {
  for (const [routes,exports] of [
    [new Map([['old','legacy']]),new Set(['legacy'])],
    [new Map(),new Set()],
  ]) {
    const result = checker.checkApiContracts(routes,exports,{legacy:'Historical gap'})
    assert.equal(result.errors.length,1)
    assert.match(result.errors[0],/legacy/)
  }
})

function backendFixture(run) {
  const fixture = mkdtempSync(path.join(tmpdir(),'ws2-api-'))
  const functions = path.join(fixture,'mcp-backend/functions')
  mkdirSync(path.join(functions,'api'),{recursive:true})
  writeFileSync(path.join(functions,'main.py'),'from api.example import original as exposed, callable_only, trigger_only\n')
  writeFileSync(path.join(functions,'api/example.py'),[
    'from api.decorators import public_endpoint as public',
    'from firebase_functions import https_fn as http, firestore_fn',
    '@public(methods=("GET",))','def original(req): pass',
    '@http.on_request()','def defined_but_unexported(req): pass',
    '@http.on_call()','def callable_only(req): pass',
    '@firestore_fn.on_document_created(document="events/{id}")','def trigger_only(req): pass',
  ].join('\n'))
  try { return run(functions,fixture) } finally { rmSync(fixture,{recursive:true,force:true}) }
}

test('Python extraction resolves export/decorator aliases and excludes unexported, callable and trigger functions',() => {
  backendFixture((_functions,fixture) => {
    const result = execFileSync(path.join(root,'.venv/bin/python'),[
      path.join(root,'scripts/contracts/export_http_endpoints.py'),'--root',fixture,
    ],{encoding:'utf8'})
    assert.deepEqual(JSON.parse(result),['exposed'])
  })
})

test('Python extraction refuses malformed modules and unsupported wildcard exports',() => {
  backendFixture((functions,fixture) => {
    for (const content of ['from api.example import *','from api.example import (']) {
      writeFileSync(path.join(functions,'main.py'),content)
      const result = spawnSync(path.join(root,'.venv/bin/python'),[
        path.join(root,'scripts/contracts/export_http_endpoints.py'),'--root',fixture,
      ],{encoding:'utf8'})
      assert.equal(result.status,1)
      assert.match(result.stderr,/API inventory rejected:/)
      assert.equal(result.stdout,'')
    }
  })
})

test('Python extraction rejects rebound export names and overwritten decorated definitions',() => {
  for (const target of ['main.py','api/example.py']) {
    backendFixture((functions,fixture) => {
      const destination = path.join(functions,target)
      const original = readFileSync(destination,'utf8')
      writeFileSync(destination,`${original}\n${target === 'main.py' ? 'exposed = None' : 'def original(req): pass'}\n`)
      const result = spawnSync(path.join(root,'.venv/bin/python'),[
        path.join(root,'scripts/contracts/export_http_endpoints.py'),'--root',fixture,
      ],{encoding:'utf8'})
      assert.equal(result.status,1)
      assert.match(result.stderr,/API inventory rejected:/)
      assert.equal(result.stdout,'')
    })
  }
})
