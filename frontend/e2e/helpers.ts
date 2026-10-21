import type { Page } from '@playwright/test'
import { createRequire } from 'node:module'

// JSON import attributes are not available under Playwright's ESM runner,
// so load the English catalog through CJS require.
const en = createRequire(import.meta.url)('../src/locales/en.json')

/** Resolve a dot-path message from the English catalog (fails loudly). */
export function m(key: string): string {
  const value = key.split('.').reduce<unknown>((node, part) => {
    if (node && typeof node === 'object' && part in (node as Record<string, unknown>)) {
      return (node as Record<string, unknown>)[part]
    }
    return undefined
  }, en)
  if (typeof value !== 'string') {
    throw new Error(`Missing en.json message for "${key}"`)
  }
  return value
}

/** Matches e.g. "12 edges checked" for key `sandbox.edgesChecked`. */
export function numberMessage(key: string): RegExp {
  const escaped = m(key).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return new RegExp(`\\d+\\s+${escaped}`)
}

/** Pin the UI locale so specs do not depend on the app's default locale. */
export async function useEnglishLocale(page: Page): Promise<void> {
  await page.addInitScript(() => {
    localStorage.setItem('locale', 'en')
  })
}
