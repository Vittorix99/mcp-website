const { test } = require('node:test')
const assert = require('node:assert/strict')
const { createRequire } = require('node:module')
const fs = require('node:fs/promises')
const os = require('node:os')
const path = require('node:path')

const firebaseToolsPackage = require.resolve('firebase-tools/package.json')
const firebaseToolsRequire = createRequire(firebaseToolsPackage)
const { archiveDirectory } = firebaseToolsRequire('./lib/archiveDirectory.js')
const tar = firebaseToolsRequire('tar')

test('firebase-tools archiveDirectory packages nested Unicode files and honors .env ignore', async () => {
  const tempRoot = await fs.mkdtemp(path.join(os.tmpdir(), 'firebase-packaging-contract-'))
  const source = path.join(tempRoot, 'source')
  const extraction = path.join(tempRoot, 'extracted')
  const nestedRelativePath = path.join('nested', 'café', '資料.txt')
  const nestedContent = Buffer.from('deployment payload\n')
  let archive

  try {
    await fs.mkdir(path.join(source, path.dirname(nestedRelativePath)), { recursive: true })
    await fs.mkdir(extraction, { recursive: true })
    await fs.writeFile(path.join(source, nestedRelativePath), nestedContent)
    await fs.writeFile(path.join(source, '.env'), 'PACKAGING_SENTINEL=nonsecret\n')

    archive = await archiveDirectory(source, { ignore: ['.env'] })
    assert.ok(archive.size > 0)

    const entries = []
    await tar.t({ file: archive.file, onentry: entry => entries.push(entry.path) })
    assert.deepEqual(entries.sort(), [nestedRelativePath.split(path.sep).join('/')])

    await tar.x({ file: archive.file, cwd: extraction })
    const extractedPath = path.join(extraction, nestedRelativePath)
    assert.deepEqual(await fs.readFile(extractedPath), nestedContent)
    assert.deepEqual(await fs.readdir(path.dirname(extractedPath)), ['資料.txt'])
    await assert.rejects(fs.access(path.join(extraction, '.env')), { code: 'ENOENT' })
  } finally {
    archive?.stream?.destroy()
    if (archive?.file) await fs.rm(archive.file, { force: true })
    await fs.rm(tempRoot, { recursive: true, force: true })
  }
})
