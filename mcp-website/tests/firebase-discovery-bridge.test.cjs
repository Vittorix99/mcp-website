const {test} = require('node:test')
const assert = require('node:assert/strict')
const {forwardDiscoveryEnvironment} = require('../../scripts/firebase-emulator-bridge.cjs')

test('discovery forwards explicit demo identity and modes but excludes secrets',()=>{
  const result = forwardDiscoveryEnvironment({MCP_ENV:'test',GCLOUD_PROJECT:'demo-mcp-test',PAYPAL_MODE:'fake',PAYPAL_CLIENT_SECRET:'SENTINEL',DEBUG:'release'}, {ADMIN_PORT:'8081',GOOGLE_APPLICATION_CREDENTIALS:'/synthetic/credential.json'})
  assert.equal(result.MCP_ENV,'test')
  assert.equal(result.GCLOUD_PROJECT,'demo-mcp-test')
  assert.equal(result.PAYPAL_MODE,'fake')
  assert.equal(result.ADMIN_PORT,'8081')
  assert.equal(result.PAYPAL_CLIENT_SECRET,undefined)
  assert.equal(result.DEBUG,undefined)
  assert.equal(result.GOOGLE_APPLICATION_CREDENTIALS,undefined)
})

test('discovery bridge refuses cloud identity',()=>{
  assert.throws(()=>forwardDiscoveryEnvironment({MCP_ENV:'production',GCLOUD_PROJECT:'mcp-website-2a1ad'},{}))
})
