import assert from 'node:assert/strict'

export async function verifyEventReadContracts({base,eventId,adminToken,memberToken}) {
  assert.equal(base,'http://127.0.0.1:5001/demo-mcp-test/us-central1','Event contracts require the loopback demo-mcp-test Functions emulator')
  const label = message => `Event contract: ${message}`
  async function request(endpoint,status,{token,method = 'GET',denied = false} = {}) {
    const response = await fetch(`${base}/${endpoint}`,{
      method,headers:token ? {Authorization:`Bearer ${token}`} : {},
      redirect:'error',signal:AbortSignal.timeout(15000),
    })
    assert.equal(response.status,status,label(`${method} ${endpoint} status`))
    if (denied) {
      const body = await response.text()
      // Legacy require_admin emits these plain-text errors; JSON must contain only an error string.
      if (!['No authorization token provided','error'].includes(body)) {
        let error
        try { error = JSON.parse(body) } catch { assert.fail(label('unauthorized response must contain only an error')) }
        assert.ok(error && !Array.isArray(error) && Object.keys(error).length === 1
          && typeof error.error === 'string',label('unauthorized response must contain only an error'))
      }
      return
    }
    assert.match(response.headers.get('content-type') || '',/application\/json/,label('JSON content type'))
    return response.json()
  }
  function noAdminFields(payload) {
    for (const field of ['createdBy','updatedBy','participantsCount']) {
      assert.ok(!Object.hasOwn(payload,field),label(`public payload exposes ${field}`))
    }
  }
  function publicEvent(payload) {
    assert.ok(payload && !Array.isArray(payload),label('public event object'))
    for (const [key,value] of Object.entries({
      id:eventId,title:'WS1 synthetic event',price:10,purchaseMode:'PUBLIC',type:'PUBLIC',
    })) assert.equal(payload[key],value,label(`public event ${key}`))
    noAdminFields(payload)
  }
  const events = await request('get_all_events',200)
  assert.ok(Array.isArray(events),label('public event list'))
  publicEvent(events.find(event => event.id === eventId))
  const cards = await request('get_all_events?view=card',200)
  assert.ok(Array.isArray(cards),label('event card list'))
  const card = cards.find(event => event.id === eventId)
  assert.equal(card?.title,'WS1 synthetic event',label('event card title'))
  noAdminFields(card)
  assert.ok(!Object.hasOwn(card,'price'),label('event card omits price'))
  publicEvent(await request(`get_event_by_id?id=${encodeURIComponent(eventId)}`,200))
  assert.deepEqual(await request(`get_event_by_id?id=${encodeURIComponent(`${eventId}-absent`)}`,404),
    {error:'Event not found'},label('missing event error'))
  const invalid = await request('get_event_by_id',400)
  assert.equal(invalid.error,'Invalid request data',label('invalid lookup error'))
  assert.ok(Array.isArray(invalid.details),label('invalid lookup details'))
  assert.deepEqual(await request('get_all_events',405,{method:'POST'}),
    {error:'Invalid method'},label('invalid method error'))

  const endpoints = ['admin_get_all_events',`admin_get_event_by_id?id=${encodeURIComponent(eventId)}`]
  const adminEvents = await request(endpoints[0],200,{token:adminToken})
  assert.ok(Array.isArray(adminEvents),label('admin event list'))
  assert.ok(adminEvents.some(event => event.id === eventId),label('admin list contains seed'))
  const detail = await request(endpoints[1],200,{token:adminToken})
  assert.equal(detail.event?.id,eventId,label('admin detail envelope'))
  for (const token of [undefined,memberToken,'invalid-emulator-token']) {
    for (const endpoint of endpoints) await request(endpoint,401,{token,denied:true})
  }
}
