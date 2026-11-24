// Owner OAuth bootstrap is deliberately separate from the ordinary WIF release.
const fs = require('node:fs')
const path = require('node:path')
const {createRequire} = require('node:module')
const {execFileSync} = require('node:child_process')
const {installAdapters, limitDeployConcurrency, DEPLOY_CONCURRENCY} = require('./firebase.cjs')
const {bootstrapSelectors,validateIdentities} = require('./cli-guards.cjs')

function ensure(ok, field) { if (!ok) throw new Error('Bootstrap validation failed: ' + field) }
function validateOperatorCredential(credential, manifest) {
  ensure(credential.type === 'authorized_user' && !credential.private_key &&
    !credential.service_account_impersonation_url && !credential.credential_source &&
    ['client_id','client_secret','refresh_token'].every(key => typeof credential[key] === 'string' && credential[key]) &&
    (!credential.quota_project_id || credential.quota_project_id === manifest.project), 'personal OAuth credential')
}
async function verifyOperator(credential, manifest, auth) {
  validateOperatorCredential(credential,manifest)
  const client = auth.fromJSON(credential)
  const {token} = await client.getAccessToken()
  ensure(token, 'operator access token')
  const info = await client.getTokenInfo(token)
  ensure(info.email === manifest.bootstrap.operator && (info.email_verified === true || info.email_verified === 'true'), 'verified operator identity')
}
function validateInvocation(manifest, env, source) {
  ensure(manifest.environment === 'staging' && manifest.project === 'mcp-website-dev-39539', 'staging project')
  ensure(!env.CI && !env.GITHUB_ACTIONS && !env.FIREBASE_TOKEN, 'local operator execution')
  ensure(env.BOOTSTRAP_CLOUD_APPROVED === 'true' && env.BOOTSTRAP_DATA_REVIEWED === 'true', 'cloud and data approval')
  ensure(/^[0-9a-f]{40}$/.test(manifest.sha) && source.sha === manifest.sha &&
    source.clean && source.onMain && env.BOOTSTRAP_APPROVED_SHA === manifest.sha, 'approved clean main source')
  ensure(typeof manifest.bootstrap?.operator === 'string' &&
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(manifest.bootstrap.operator) &&
    manifest.bootstrap.operator === env.BOOTSTRAP_OPERATOR_EMAIL, 'named operator')
}
async function main() {
  ensure(process.versions.node.split('.')[0] === '22', 'Node.js 22')
  const root = path.resolve(__dirname,'../..')
  const cliRoot = path.join(root,'mcp-website/node_modules/firebase-tools')
  const cli = createRequire(path.join(cliRoot,'package.json'))
  ensure(cli('./package.json').version === '14.26.0','pinned CLI')
  if (process.argv.length === 3 && process.argv[2] === 'selectors') {
    console.log(bootstrapSelectors(cli,JSON.parse(fs.readFileSync(0,'utf8'))))
    return
  }
  const operation = process.argv[2]
  ensure(process.argv.length === 3 && ['validate','backend','hosting'].includes(operation), 'scoped target')
  const config = path.join(root,'.local/release/config.json')
  ensure(process.env.MCP_RELEASE_CONFIG === config, 'configuration path')
  const manifest = JSON.parse(fs.readFileSync(config,'utf8'))
  const git = args => execFileSync('git',args,{cwd:root,encoding:'utf8',stdio:['ignore','pipe','ignore']}).trim()
  let onMain = false
  try {git(['merge-base','--is-ancestor',manifest.sha,'origin/main']); onMain = true} catch {}
  validateInvocation(manifest,process.env,{sha:git(['rev-parse','HEAD']),
    clean:git(['status','--porcelain','--untracked-files=normal']) === '',onMain})
  validateIdentities(manifest)
  const credentialPath = process.env.BOOTSTRAP_OPERATOR_ADC
  ensure(credentialPath && path.isAbsolute(credentialPath) &&
    credentialPath === process.env.GOOGLE_APPLICATION_CREDENTIALS, 'explicit operator ADC')
  const stat = fs.lstatSync(credentialPath)
  ensure(stat.isFile() && !stat.isSymbolicLink() && (stat.mode & 0o077) === 0 &&
    stat.uid === process.getuid(), 'private operator credential file')
  const profile = process.env.XDG_CONFIG_HOME
  ensure(profile && path.dirname(profile) === path.join(root,'.local/release') &&
    path.basename(profile).startsWith('operator-') &&
    fs.readdirSync(profile).length === 0, 'fresh Firebase authentication profile')
  const credential = JSON.parse(fs.readFileSync(credentialPath,'utf8'))
  const {GoogleAuth} = cli('google-auth-library')
  await verifyOperator(credential,manifest,new GoogleAuth())
  const only = bootstrapSelectors(cli,manifest.bootstrap.endpoints)
  if (operation === 'validate') return
  installAdapters(root,cli,manifest,credentialPath,{bootstrap:true,
    approvedFunctions:manifest.bootstrap.endpoints.filter(row => row.kind === 'http').map(row => row.id)})
  limitDeployConcurrency(cli)
  Object.assign(process.env,manifest.frontend)
  process.env.__NEXT_PROCESSED_ENV = 'true'
  const entry = path.join(cliRoot,'lib/bin/firebase.js')
  process.argv = [process.execPath,entry,'deploy','--non-interactive','--project',manifest.project,
    '--config',path.join(root,'firebase.release.generated.json'),'--only',operation === 'backend' ? only : 'hosting']
  require(entry)
}
module.exports = {validateOperatorCredential,verifyOperator,validateInvocation,limitDeployConcurrency,DEPLOY_CONCURRENCY}
if (require.main === module) main().catch(() => {console.error('Guarded staging bootstrap failed; diagnostics withheld');process.exitCode = 1})
