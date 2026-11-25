import {test} from 'node:test'
import assert from 'node:assert/strict'
import {readFile} from 'node:fs/promises'

const source = await readFile(new URL('../app/api/deployment-health/route.js', import.meta.url), 'utf8')
const {GET} = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'))

test('release health exposes only public release identity', async () => {
  process.env.NEXT_PUBLIC_ENV = 'staging'
  process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID = 'mcp-website-dev-39539'
  process.env.NEXT_PUBLIC_RELEASE_SHA = 'a'.repeat(40)
  process.env.NEXT_PUBLIC_SITE_TREE = 'c'.repeat(64)
  process.env.NEXT_PUBLIC_CONFIGURATION_DIGEST = 'b'.repeat(64)
  process.env.PRIVATE_SENTINEL = 'private-sentinel'
  const response = await GET()
  assert.equal(response.status, 200)
  assert.deepEqual(await response.json(), {status:'ok', environment:'staging', project_id:'mcp-website-dev-39539', release_sha:'a'.repeat(40), site_tree:'c'.repeat(64), configuration_digest:'b'.repeat(64)})
  assert.equal(response.headers.get('Cache-Control'), 'no-store')
})

test('release health rejects a missing site tree', async () => {
  process.env.NEXT_PUBLIC_RELEASE_SHA = 'a'.repeat(40)
  process.env.NEXT_PUBLIC_SITE_TREE = ''
  const response = await GET()
  assert.equal(response.status, 503)
})

test('release health rejects missing or invalid build stamps', async () => {
  for (const sha of ['', 'private-sentinel']) {
    process.env.NEXT_PUBLIC_RELEASE_SHA = sha
    const response = await GET()
    assert.equal(response.status, 503)
    assert.deepEqual(await response.json(), {status:'unversioned'})
  }
})
