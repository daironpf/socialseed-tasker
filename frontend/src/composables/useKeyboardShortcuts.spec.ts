import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  useKeyboardShortcuts,
  initKeyboardShortcuts,
  destroyKeyboardShortcuts,
  type Shortcut,
} from '@/composables/useKeyboardShortcuts'

function press(key: string, init: KeyboardEventInit = {}) {
  document.dispatchEvent(new KeyboardEvent('keydown', { key, cancelable: true, ...init }))
}

function makeShortcut(overrides: Partial<Shortcut> & { action: () => void }): Shortcut {
  return {
    key: 'k',
    label: 'Test shortcut',
    description: 'test',
    scope: 'global',
    ...overrides,
  }
}

describe('useKeyboardShortcuts', () => {
  const kb = useKeyboardShortcuts()

  beforeEach(() => {
    destroyKeyboardShortcuts()
    kb.unregisterAll()
    initKeyboardShortcuts()
  })

  afterEach(() => {
    destroyKeyboardShortcuts()
    kb.unregisterAll()
    document.body.innerHTML = ''
  })

  describe('registry', () => {
    it('registers shortcuts and exposes them reactively', () => {
      const shortcut = makeShortcut({ action: vi.fn() })
      kb.register(shortcut)

      expect(kb.shortcuts.value).toHaveLength(1)
      expect(kb.shortcuts.value[0]).toEqual(shortcut)
    })

    it('does not register duplicates for the same key, scope and sequence', () => {
      kb.register(makeShortcut({ action: vi.fn() }))
      kb.register(makeShortcut({ action: vi.fn() }))

      expect(kb.shortcuts.value).toHaveLength(1)
    })

    it('unregisters a single shortcut and all shortcuts', () => {
      kb.register(makeShortcut({ key: 'a', action: vi.fn() }))
      kb.register(makeShortcut({ key: 'b', scope: 'local', action: vi.fn() }))

      kb.unregister('a')
      expect(kb.shortcuts.value.map(s => s.key)).toEqual(['b'])

      kb.unregisterAll('local')
      expect(kb.shortcuts.value).toHaveLength(0)

      kb.register(makeShortcut({ key: 'c', action: vi.fn() }))
      kb.unregisterAll()
      expect(kb.shortcuts.value).toHaveLength(0)
    })
  })

  describe('dispatch', () => {
    it('runs the matching global shortcut and prevents the default', () => {
      const action = vi.fn()
      kb.register(makeShortcut({ key: 'j', action }))

      const event = new KeyboardEvent('keydown', { key: 'j', cancelable: true })
      document.dispatchEvent(event)

      expect(action).toHaveBeenCalledTimes(1)
      expect(event.defaultPrevented).toBe(true)
    })

    it('ignores keys when an input is focused', () => {
      const action = vi.fn()
      kb.register(makeShortcut({ key: 'j', action }))

      const input = document.createElement('input')
      document.body.appendChild(input)
      input.focus()
      expect(document.activeElement).toBe(input)

      press('j')
      expect(action).not.toHaveBeenCalled()

      input.blur()
      press('j')
      expect(action).toHaveBeenCalledTimes(1)
    })

    it('respects the enabled predicate', () => {
      const action = vi.fn()
      let enabled = false
      kb.register(makeShortcut({ key: 'x', action, enabled: () => enabled }))

      press('x')
      expect(action).not.toHaveBeenCalled()

      enabled = true
      press('x')
      expect(action).toHaveBeenCalledTimes(1)
    })

    it('requires the declared modifiers', () => {
      const action = vi.fn()
      kb.register(makeShortcut({ key: 's', modifiers: { ctrl: true }, action }))

      press('s')
      expect(action).not.toHaveBeenCalled()

      press('s', { ctrlKey: true })
      expect(action).toHaveBeenCalledTimes(1)
    })

    it('fires sequence shortcuts only after the full sequence', () => {
      const action = vi.fn()
      kb.register(makeShortcut({ key: 'gi', sequence: ['g', 'i'], action }))

      press('g')
      expect(action).not.toHaveBeenCalled()

      press('i')
      expect(action).toHaveBeenCalledTimes(1)

      press('i')
      expect(action).toHaveBeenCalledTimes(1)
    })

    it('does not fire a sequence shortcut on its prefix key alone', () => {
      const action = vi.fn()
      kb.register(makeShortcut({ key: 'g', sequence: ['g', 'i'], action }))

      press('g')
      expect(action).not.toHaveBeenCalled()

      press('i')
      expect(action).toHaveBeenCalledTimes(1)
    })

    it('runs local shortcuts registered by the active view', () => {
      const action = vi.fn()
      kb.register(makeShortcut({ key: 'j', scope: 'local', action }))

      const event = new KeyboardEvent('keydown', { key: 'j', cancelable: true })
      document.dispatchEvent(event)

      expect(action).toHaveBeenCalledTimes(1)
      expect(event.defaultPrevented).toBe(true)
    })

    it('lets sequences win over a local shortcut with the same key', () => {
      const sequenceAction = vi.fn()
      const localAction = vi.fn()
      kb.register(makeShortcut({ key: 'g', sequence: ['g', 'k'], action: sequenceAction }))
      kb.register(makeShortcut({ key: 'k', scope: 'local', action: localAction }))

      press('g')
      press('k')

      expect(sequenceAction).toHaveBeenCalledTimes(1)
      expect(localAction).not.toHaveBeenCalled()
    })

    it('fires escape shortcuts even when an input is focused', () => {
      const action = vi.fn()
      kb.register(makeShortcut({ key: 'escape', scope: 'local', action }))

      const input = document.createElement('input')
      document.body.appendChild(input)
      input.focus()

      press('Escape')
      expect(action).toHaveBeenCalledTimes(1)
    })

    it('skips shortcuts when the event was already handled', () => {
      const action = vi.fn()
      kb.register(makeShortcut({ key: 'x', action }))

      const event = new KeyboardEvent('keydown', { key: 'x', cancelable: true })
      event.preventDefault()
      document.dispatchEvent(event)

      expect(action).not.toHaveBeenCalled()
    })

    it('stops listening after destroyKeyboardShortcuts', () => {
      const action = vi.fn()
      kb.register(makeShortcut({ key: 'j', action }))
      destroyKeyboardShortcuts()

      press('j')

      expect(action).not.toHaveBeenCalled()
    })
  })
})
