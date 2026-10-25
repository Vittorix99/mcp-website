import assert from 'node:assert/strict'
import {readFile} from 'node:fs/promises'
import {createRequire} from 'node:module'
import {initializeApp,deleteApp} from 'firebase/app'
import {getAuth,connectAuthEmulator,signInWithEmailAndPassword} from 'firebase/auth'
import {getFirestore,connectFirestoreEmulator,doc,getDoc,setDoc,deleteDoc,terminate} from 'firebase/firestore'
import {getStorage,connectStorageEmulator,ref,uploadBytes,getBytes,deleteObject} from 'firebase/storage'
import {initializeApp as initializeAdminApp,deleteApp as deleteAdminApp} from 'firebase-admin/app'
import {getAuth as getAdminAuth} from 'firebase-admin/auth'
import {getFirestore as getAdminFirestore} from 'firebase-admin/firestore'

const require = createRequire(import.meta.url)
const {validatePublicRuntime} = require('../config/runtime-policy.cjs')
const catalog = require('../../mcp-backend/functions/config/environment_catalog.json')
const projectId = process.env.GCLOUD_PROJECT
assert.ok(['demo-mcp-test','demo-mcp-local'].includes(projectId),'Smoke tests require a demo project')
const config = validatePublicRuntime({NEXT_PUBLIC_ENV:projectId.endsWith('local')?'local':'test'},catalog)
for (const key of ['FIRESTORE_EMULATOR_HOST','FIREBASE_AUTH_EMULATOR_HOST','STORAGE_EMULATOR_HOST','PUBSUB_EMULATOR_HOST']) assert.ok(process.env[key]?.startsWith('127.0.0.1:'),`Missing loopback emulator: ${key}`)
const seed = JSON.parse(await readFile(new URL('../tests/fixtures/emulator-seed.json',import.meta.url),'utf8'))
const admin = initializeAdminApp({projectId})
const adminDb = getAdminFirestore(admin)
const adminAuth = getAdminAuth(admin)
const apps = []
const firestoreClients = []
const users = []
let storage
let image
try {
  await adminDb.doc(`events/${seed.event_id}`).set(seed.event)
  await adminDb.doc('membership_settings/price').set(seed.membership_settings)
  if (process.argv.includes('--seed-only')) {
    console.log('Synthetic local seed applied')
  } else {
    async function client(label,role) {
      const user = await adminAuth.createUser({email:`ws1-${label}@example.test`,password:'Synthetic-only-123!'})
      users.push(user.uid)
      if (role) await adminAuth.setCustomUserClaims(user.uid,{admin:true})
      const app = initializeApp(config.firebase,`smoke-${label}`)
      apps.push(app)
      const auth = getAuth(app)
      connectAuthEmulator(auth,`http://${config.emulators.auth}`,{disableWarnings:true})
      const db = getFirestore(app)
      connectFirestoreEmulator(db,'127.0.0.1',8080)
      firestoreClients.push(db)
      const store = getStorage(app)
      connectStorageEmulator(store,'127.0.0.1',9199)
      await signInWithEmailAndPassword(auth,user.email,'Synthetic-only-123!')
      return {db,auth,store}
    }
    const app = initializeApp(config.firebase,'smoke-public')
    apps.push(app)
    const publicDb = getFirestore(app)
    connectFirestoreEmulator(publicDb,'127.0.0.1',8080)
    firestoreClients.push(publicDb)
    assert.equal((await getDoc(doc(publicDb,'events',seed.event_id))).data().title,'WS1 synthetic event')
    const privileged = await client('admin',true)
    await setDoc(doc(privileged.db,'events','smoke-admin-write'),{title:'Synthetic admin write'})
    storage = privileged.store
    image = ref(storage,'events/ws1-smoke.bin')
    await uploadBytes(image,new Uint8Array([1,2,3]),{contentType:'application/octet-stream'})
    assert.deepEqual(new Uint8Array(await getBytes(image)),new Uint8Array([1,2,3]))
    const regular = await client('member',false)
    await assert.rejects(uploadBytes(ref(regular.store,'events/ws1-forbidden.bin'),new Uint8Array([4])),error=>error.code==='storage/unauthorized')
    const token = await privileged.auth.currentUser.getIdToken()
    const base = `http://127.0.0.1:5001/${projectId}/us-central1`
    const publicResponse = await fetch(`${base}/get_membership_price_public?year=2026`)
    assert.equal(publicResponse.status,200)
    assert.equal((await publicResponse.json()).price,20)
    const memberResponse = await fetch(`${base}/member_get_me`,{headers:{Authorization:`Bearer ${token}`}})
    assert.equal(memberResponse.status,404,'Valid emulator Auth token should reach membership lookup')
    assert.equal((await memberResponse.json()).error,'Membership not found for this account')
    await deleteDoc(doc(privileged.db,'events','smoke-admin-write'))
    console.log('Emulator client smoke: PASS (Firestore/Auth/Storage/Functions)')
  }
} finally {
  if (!process.argv.includes('--seed-only')) {
    if (image) await deleteObject(image).catch(()=>{})
    await adminDb.doc(`events/${seed.event_id}`).delete()
    await adminDb.doc('membership_settings/price').delete()
    for (const uid of users) await adminAuth.deleteUser(uid)
  }
  for (const client of firestoreClients) await terminate(client)
  for (const app of apps) await deleteApp(app)
  await adminDb.terminate()
  await deleteAdminApp(admin)
}
