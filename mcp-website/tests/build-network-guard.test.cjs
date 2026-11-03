const {test} = require('node:test')
const assert = require('node:assert/strict')
const {spawnSync} = require('node:child_process')
const {mkdtempSync,readFileSync,rmSync} = require('node:fs')
const {tmpdir} = require('node:os')
const path = require('node:path')
const http = require('node:http')
const {execFile} = require('node:child_process')
const {promisify} = require('node:util')

test('build guard blocks external fetch even if application catches the failure', () => {
  const dir = mkdtempSync(path.join(tmpdir(),'mcp-network-test-'))
  const denial = path.join(dir,'denials.log')
  try {
    const result = spawnSync(process.execPath,['--require',path.resolve(__dirname,'../scripts/build-network-guard.cjs'),'-e',
      "fetch('https://credential:SENTINEL@outside.example.invalid/private').catch(()=>{})"], {
      env:{PATH:process.env.PATH,MCP_BUILD_DENIALS_FILE:denial},encoding:'utf8',timeout:5000,
    })
    assert.equal(result.status,0,result.stderr)
    const log = readFileSync(denial,'utf8')
    assert.match(log,/outside.example.invalid/)
    assert.doesNotMatch(log,/SENTINEL|credential|private/)
  } finally {rmSync(dir,{recursive:true,force:true})}
})

test('required backend failures are recorded even when release code catches them', async () => {
  const dir = mkdtempSync(path.join(tmpdir(),'mcp-fetch-test-'))
  const failure = path.join(dir,'failures.log')
  const server = http.createServer((req,res) => {res.writeHead(500); res.end('{}')})
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve))
  const base = `http://127.0.0.1:${server.address().port}`
  try {
    await promisify(execFile)(process.execPath,['--require',path.resolve(__dirname,'../scripts/build-network-guard.cjs'),'-e',
      "fetch(process.env.BACKEND_BASE_URL+'/get_all_events').catch(()=>{})"], {
      env:{PATH:process.env.PATH,MCP_BUILD_MODE:'release',BACKEND_BASE_URL:base,MCP_BUILD_FAILURES_FILE:failure},timeout:5000,
    })
    assert.match(readFileSync(failure,'utf8'),/Required backend read failed/)
  } finally {await new Promise(resolve => server.close(resolve)); rmSync(dir,{recursive:true,force:true})}
})
