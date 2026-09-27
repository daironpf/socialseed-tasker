import { cpSync, rmSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const frontendDir = dirname(dirname(fileURLToPath(import.meta.url)))
const source = join(frontendDir, 'dataset-de-pruebas')
const target = join(frontendDir, '.e2e-data')

if (!existsSync(source)) {
  console.error(`Mock dataset not found: ${source}`)
  process.exit(1)
}

rmSync(target, { recursive: true, force: true })
cpSync(source, target, { recursive: true })
console.log(`Mock dataset copied to ${target}`)
