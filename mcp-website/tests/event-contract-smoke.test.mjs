import assert from 'node:assert/strict'
import http from 'node:http'
import {randomUUID} from 'node:crypto'
import test from 'node:test'

import {verifyEventReadContracts as verify} from '../scripts/event-contract-smoke.mjs'
const options = {
  base:'http://127.0.0.1:5001/demo-mcp-test/us-central1',eventId:'fixture-event',
  adminToken:'fixture-admin',memberToken:'fixture-member',
}
const event = {id:'fixture-event',title:'WS1 synthetic event',price:10,purchaseMode:'PUBLIC',type:'PUBLIC'}

async function fixture(t,mutation) {
  const seen = []
  const server = http.createServer((req,res) => {
    const url = new URL(req.url,'http://127.0.0.1')
    const endpoint = url.pathname.split('/').at(-1)
    const token = req.headers.authorization
    let status = 200
    let payload
    if (endpoint.startsWith('admin_')) {
      status = token === 'Bearer fixture-admin' ? 200 : 401
      payload = status === 401 ? {error:'Denied'}
        : endpoint === 'admin_get_all_events' ? [event] : {event}
    } else if (token) {
      status = 500; payload = {error:'Public request must not carry a token'}
    } else if (endpoint === 'get_all_events') {
      if (req.method !== 'GET') { status = 405; payload = {error:'Invalid method'} }
      else payload = url.searchParams.get('view') === 'card'
        ? [{id:event.id,title:event.title}] : [event]
    } else if (!url.searchParams.has('id')) {
      status = 400; payload = {error:'Invalid request data',details:[]}
    } else if (url.searchParams.get('id') !== event.id) {
      status = 404; payload = {error:'Event not found'}
    } else payload = event
    const result = mutation?.({endpoint,url,token,status,payload}) || {status,payload}
    seen.push({endpoint,token,status:result.status})
    res.writeHead(result.status,{'Content-Type':'application/json','X-Request-ID':randomUUID(),...result.headers})
    res.end(JSON.stringify(result.payload))
  })
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve))
  t.after(() => new Promise(resolve => server.close(resolve)))
  const realFetch = globalThis.fetch
  t.mock.method(globalThis,'fetch',(url,init) => {
    assert.equal(new URL(url).origin,'http://127.0.0.1:5001')
    const original = new URL(url)
    return realFetch(`http://127.0.0.1:${server.address().port}${original.pathname}${original.search}`,init)
  })
  return seen
}

test('verifies public payloads, error statuses and admin/member authorization through HTTP',async t => {
  const seen = await fixture(t)
  await verify(options)
  assert.equal(seen.length,14)
  assert.equal(seen.filter(request => request.status === 401).length,6)
  assert.ok(seen.filter(request => !request.endpoint.startsWith('admin_')).every(request => !request.token))
})

test('rejects a public detail response wrapped in the admin envelope',async t => {
  await fixture(t,result => result.endpoint === 'get_event_by_id' && result.status === 200
    ? {...result,payload:{event}} : result)
  await assert.rejects(verify(options),/Event contract:/)
})

test('rejects a changed missing-event error contract',async t => {
  await fixture(t,result => result.status === 404 ? {...result,payload:{error:'Unexpected error'}} : result)
  await assert.rejects(verify(options),/Event contract:/)
})

test('detects public leakage of administrative metadata',async t => {
  await fixture(t,result => result.endpoint === 'get_event_by_id' && result.status === 200
    ? {...result,payload:{...event,createdBy:'private-owner'}} : result)
  await assert.rejects(verify(options),/Event contract:/)
})

test('detects an admin endpoint allowing an ordinary authenticated user',async t => {
  await fixture(t,result => result.endpoint.startsWith('admin_') && result.token === 'Bearer fixture-member'
    ? {...result,status:200,payload:[event]} : result)
  await assert.rejects(verify(options),/Event contract:/)
})

test('rejects event metadata leaked in 401 responses even without an event ID',async t => {
  await fixture(t,result => result.status === 401
    ? {...result,payload:{event:{title:'WS1 synthetic event',createdBy:'synthetic-admin'}}} : result)
  await assert.rejects(verify(options),/Event contract:/)
})

test('rejects HTTP responses without a valid request ID',async t => {
  await fixture(t,result => ({...result,headers:{'X-Request-ID':''}}))
  await assert.rejects(verify(options),/Event contract:/)
})

test('rejects repeated request IDs across different HTTP requests',async t => {
  await fixture(t,result => ({...result,headers:{'X-Request-ID':'00000000-0000-4000-8000-000000000001'}}))
  await assert.rejects(verify(options),/Event contract:/)
})

test('refuses cloud, local-development and redirected credentials destinations before sending requests',async t => {
  let requests = 0
  t.mock.method(globalThis,'fetch',async () => { requests++; throw new Error('Network must not be used') })
  for (const base of [
    'https://cloud.example.com','http://127.0.0.1:5001/demo-mcp-local/us-central1',
    'http://127.0.0.1:5001@cloud.example.com/demo-mcp-test/us-central1',
    'http://127.0.0.1:5001/demo-mcp-test/us-central1/extra',
  ]) await assert.rejects(verify({...options,base}),/demo-mcp-test/)
  assert.equal(requests,0)
})
