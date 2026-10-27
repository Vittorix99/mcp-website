import assert from 'node:assert/strict'
import test from 'node:test'

import {seedLocalAdmin as seedAdmin} from '../scripts/emulator-admin-seed.mjs'
const localEnv = {GCLOUD_PROJECT:'demo-mcp-local',FIREBASE_AUTH_EMULATOR_HOST:'127.0.0.1:9099'}

// Only the external Auth service is replaced; exercise seed validation and upsert behavior.
function authStore() {
  const users = new Map()
  return {
    users,
    async getUserByEmail(email) {
      const user = [...users.values()].find(user => user.email === email)
      if (!user) throw Object.assign(new Error('No user'),{code:'auth/user-not-found'})
      return user
    },
    async createUser(user) { users.set(user.uid,{...user}); return users.get(user.uid) },
    async updateUser(uid,changes) { Object.assign(users.get(uid),changes); return users.get(uid) },
    async setCustomUserClaims(uid,claims) { users.get(uid).customClaims = claims },
  }
}

test('seed creates a login-enabled local admin and reruns restore the same account',async () => {
  const auth = authStore()
  await seedAdmin(auth,localEnv)
  const admin = [...auth.users.values()][0]
  assert.equal(admin.email,'admin@test.it')
  assert.equal(admin.password,'admin123')
  assert.equal(admin.disabled,false)
  assert.equal(admin.emailVerified,true)
  assert.deepEqual(admin.customClaims,{admin:true})
  admin.password = 'changed-password' // NOSECRET: synthetic in-memory test fixture, never a real credential
  admin.disabled = true
  admin.customClaims = {}
  await seedAdmin(auth,localEnv)
  assert.equal(auth.users.size,1)
  assert.equal(admin.password,'admin123')
  assert.equal(admin.disabled,false)
  assert.deepEqual(admin.customClaims,{admin:true})
})

test('seed refuses cloud projects and non-local Auth endpoints before accessing Auth',async () => {
  for (const env of [
    {...localEnv,GCLOUD_PROJECT:'mcp-production'},
    {...localEnv,FIREBASE_AUTH_EMULATOR_HOST:undefined},
    {...localEnv,FIREBASE_AUTH_EMULATOR_HOST:'auth.example.com:9099'},
    {...localEnv,FIREBASE_AUTH_EMULATOR_HOST:'127.0.0.1:9099@auth.example.com'},
  ]) {
    await assert.rejects(seedAdmin({},env),/local Auth emulator/)
  }
})

test('seed propagates Auth outages instead of treating them as missing users',async () => {
  const failure = new Error('Auth unavailable')
  await assert.rejects(seedAdmin({getUserByEmail:async () => { throw failure }},localEnv),error => error === failure)
})
