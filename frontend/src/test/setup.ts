import { beforeEach, afterEach } from 'vitest'
import { enableAutoUnmount } from '@vue/test-utils'

// Components are attached to document.body (needed for document-level
// listeners); unmount them after every test to avoid leaking DOM nodes
enableAutoUnmount(afterEach)

// jsdom does not implement matchMedia (used by dark-mode detection)
if (typeof window.matchMedia !== 'function') {
  window.matchMedia = (query: string): MediaQueryList =>
    ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }) as unknown as MediaQueryList
}

if (typeof window.ResizeObserver !== 'function') {
  window.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof ResizeObserver
}

if (typeof Element.prototype.scrollIntoView !== 'function') {
  Element.prototype.scrollIntoView = () => {}
}

// Stores persist to localStorage; start every test from a clean slate
beforeEach(() => {
  localStorage.clear()
})
