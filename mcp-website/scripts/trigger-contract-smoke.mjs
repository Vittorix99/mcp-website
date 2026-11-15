import assert from 'node:assert/strict'
import {randomUUID} from 'node:crypto'
import {setTimeout as delay} from 'node:timers/promises'

async function eventually(label, read, accept) {
  const deadline = Date.now() + 45000
  while (Date.now() < deadline) {
    const value = await read()
    if (accept(value)) return value
    await delay(250)
  }
  throw new Error(`Emulator trigger timeout: ${label}`)
}

// Exercise actual Firestore event delivery; never call trigger handlers directly.
export async function verifyFirestoreTriggerContracts({db, auth, eventId}) {
  assert.equal(db.projectId, 'demo-mcp-test', 'Trigger proof requires the disposable test project')
  for (const key of ['FIRESTORE_EMULATOR_HOST', 'FIREBASE_AUTH_EMULATOR_HOST']) {
    assert.match(process.env[key] || '', /^127\.0\.0\.1:\d+$/)
  }
  const id = `trigger-smoke-${randomUUID()}`
  const email = `${id}@example.test`
  const member = db.doc(`memberships/${id}`)
  const participant = db.doc(`participants/${eventId}/participants_event/${id}`)
  const purchase = db.doc(`purchases/${id}`)
  const scan = db.doc(`entrance_scans/${eventId}/scans/${id}`)
  const emptyEvent = db.doc(`events/${id}-empty`)
  const locationJob = db.doc(`location_jobs/${id}`)
  const snapshot = db.doc(`analytics_event/${eventId}`)
  const jobs = db.collection('analytics_jobs')
  async function completed(reason) {
    await eventually(reason, () => jobs.get(), result => {
      const rows = result.docs.map(doc => doc.data())
      return rows.some(row => row.reason === reason && row.status === 'completed') &&
        !rows.some(row => ['queued', 'running'].includes(row.status))
    })
  }
  try {
    await member.set({name:'Giulia', surname:'Smoke', email, birthdate:'10-01-1990',
      membership_years:[new Date().getUTCFullYear()], subscription_valid:true,
      send_card_on_create:false, newsletter_consent:false})
    const processed = await eventually('membership creation', () => member.get(), doc =>
      doc.data()?.trigger_processed === true && Boolean(doc.data()?.uid) &&
      doc.data()?.wallet_pass_id?.startsWith('FAKE-'))
    assert.equal((await auth.getUser(processed.data().uid)).email, email)
    await completed('membership_written')

    await participant.set({event_id:eventId, membershipId:id, name:'Giulia', surname:'Smoke',
      email, birthdate:'10-01-1990', price:0, payment_method:'omaggio',
      entered:false, ticket_sent:true, send_ticket_on_create:false, newsletter_consent:false})
    await eventually('participant enrichment', () => participant.get(), doc =>
      doc.data()?.gender === 'female' && doc.data()?.gender_probability === 1)
    await eventually('participant snapshot', () => snapshot.get(), doc => doc.data()?.kpis?.participants === 1)
    await completed('participant_written')

    await purchase.set({type:'event', ref_id:eventId, event_id:eventId, status:'COMPLETED',
      capture_status:'COMPLETED', amount_total:'7.00', net_amount:'6.00', paypal_fee:'1.00',
      participants_count:1, membership_ids:[id], timestamp:new Date()})
    await eventually('purchase snapshot', () => snapshot.get(), doc => doc.data()?.kpis?.revenue_gross === 7)
    await completed('purchase_written')

    await scan.set({scanned_at:new Date()})
    await eventually('scan snapshot', () => snapshot.get(), doc => doc.data()?.kpis?.entered === 1)
    await completed('entrance_scan_written')
    await scan.delete()
    await eventually('scan deletion snapshot', () => snapshot.get(), doc => doc.data()?.kpis?.entered === 0)
    await completed('entrance_scan_written')
    // No recipients: exercise the location worker without requesting any mail.
    await emptyEvent.set({title:'Synthetic location job', date:'01-01-2099', status:'active'})
    await locationJob.set({type:'send_location', event_id:emptyEvent.id, status:'queued',
      total:0, created_at:new Date(), updated_at:new Date()})
    await eventually('location worker', () => locationJob.get(), doc => doc.data()?.status === 'completed')
    assert.equal((await locationJob.get()).data().total, 0)
    console.log('Firestore trigger smoke: PASS (member/participant creation, four analytics writes, analytics/location workers, scan deletion)')
  } finally {
    await Promise.all([scan.delete(), purchase.delete(), participant.delete(), member.delete(),
      locationJob.delete(), emptyEvent.delete()])
    const user = await auth.getUserByEmail(email).catch(error => {
      if (error.code !== 'auth/user-not-found') throw error
      return null
    })
    if (user) await auth.deleteUser(user.uid)
  }
}
