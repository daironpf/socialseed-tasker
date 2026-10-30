import { readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { gzipSync } from 'node:zlib'

const ROOT = fileURLToPath(new URL('..', import.meta.url))
const DIST = join(ROOT, 'dist')
const LIMIT = 500 * 1024

function fail(message) {
  console.error(`Bundle guard failed: ${message}`)
  process.exit(1)
}

function measure(file) {
  const contents = readFileSync(join(DIST, file))
  return { min: contents.length, gzip: gzipSync(contents).length }
}

function format(bytes) {
  return `${(bytes / 1000).toFixed(1)} kB`
}

let manifest
try {
  manifest = JSON.parse(readFileSync(join(DIST, '.vite/manifest.json'), 'utf8'))
} catch {
  fail('dist/.vite/manifest.json is missing; run "vite build" with build.manifest enabled')
}

const entries = Object.entries(manifest)
const entry = entries.find(([, chunk]) => chunk.isEntry)
if (!entry) fail('no entry chunk found in the manifest')

const isElk = (key, chunk) =>
  /elkjs|[\\/]elk[-.]/i.test(`${key} ${chunk.file}`) ||
  (key.includes('mermaid') && chunk.name?.startsWith('elk'))

const initialKeys = new Set()
function collectStaticImports(key, isRoot = false) {
  if (initialKeys.has(key) || (key === 'index.html' && !isRoot)) return
  initialKeys.add(key)
  for (const dependency of manifest[key]?.imports ?? []) collectStaticImports(dependency)
}
collectStaticImports(entry[0], true)

const initialChunks = [...initialKeys]
  .map((key) => ({ key, chunk: manifest[key] }))
  .filter(({ chunk }) => chunk.file.endsWith('.js'))

let initialMin = 0
let initialGzip = 0
for (const { key, chunk } of initialChunks) {
  if (isElk(key, chunk)) fail(`ELK is statically imported by the entry (${key})`)
  const size = measure(chunk.file)
  initialMin += size.min
  initialGzip += size.gzip
  if (size.min > LIMIT) {
    fail(`initial chunk ${chunk.file} is ${format(size.min)} (> 500 kB)`)
  }
}

const elkChunk = entries.find(([key, chunk]) => isElk(key, chunk))
if (!elkChunk) fail('ELK chunk not found; the lazy Mermaid layout may have disappeared')
if (!elkChunk[1].isDynamicEntry) fail(`ELK chunk ${elkChunk[0]} is not a dynamic entry`)

const allowedLazy = (key, chunk) => {
  const identity = `${key} ${chunk.file}`
  if (isElk(key, chunk)) return 'Mermaid optional ELK layout'
  if (identity.includes('mermaid') || identity.includes('cynefin')) {
    return 'Mermaid feature loaded on demand'
  }
  if (identity.includes('GraphView') || identity.includes('vis-network')) {
    return 'graph view loaded on demand'
  }
  return null
}

const lazyExceptions = []
for (const [key, chunk] of entries) {
  if (!chunk.file.endsWith('.js') || initialKeys.has(key)) continue
  const size = measure(chunk.file)
  if (size.min <= LIMIT) continue
  const reason = allowedLazy(key, chunk)
  if (!reason) {
    fail(`lazy chunk ${chunk.file} is ${format(size.min)} with no documented exception`)
  }
  lazyExceptions.push({ file: chunk.file, size, reason })
}

console.log(
  `Bundle guard OK: initial ${initialChunks.length} chunks, ${format(initialMin)} min / ${format(initialGzip)} gzip`,
)
for (const { key, chunk } of initialChunks) {
  const size = measure(chunk.file)
  console.log(`  initial  ${chunk.file} ${format(size.min)} / ${format(size.gzip)}`)
}
for (const { file, size, reason } of lazyExceptions) {
  console.log(`  lazy     ${file} ${format(size.min)} / ${format(size.gzip)} :: ${reason}`)
}
