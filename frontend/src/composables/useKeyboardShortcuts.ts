import { ref, computed } from 'vue'

export interface Shortcut {
  key: string
  label: string
  description: string
  sequence?: string[]
  scope: 'global' | 'local'
  modifiers?: { ctrl?: boolean; meta?: boolean; shift?: boolean; alt?: boolean }
  action: () => void
  enabled?: () => boolean
}

const registeredShortcuts = ref<Shortcut[]>([])
const sequenceBuffer = ref<string[]>([])
const sequenceTimeout = ref<ReturnType<typeof setTimeout> | null>(null)
const SEQUENCE_TIMEOUT_MS = 1000

function isInputFocused(): boolean {
  const el = document.activeElement
  if (!el) return false
  const tag = el.tagName.toLowerCase()
  return tag === 'input' || tag === 'textarea' || (el as HTMLElement).isContentEditable
}

function matchModifier(e: KeyboardEvent, modifiers?: Shortcut['modifiers']): boolean {
  if (!modifiers) return true
  if (modifiers.ctrl !== undefined && e.ctrlKey !== modifiers.ctrl) return false
  if (modifiers.meta !== undefined && e.metaKey !== modifiers.meta) return false
  if (modifiers.shift !== undefined && e.shiftKey !== modifiers.shift) return false
  if (modifiers.alt !== undefined && e.altKey !== modifiers.alt) return false
  return true
}

function handleKeydown(e: KeyboardEvent) {
  if (isInputFocused()) return

  const key = e.key.toLowerCase()

  const globalMatches = registeredShortcuts.value.filter((s) => {
    if (s.scope !== 'global') return false
    if (s.key !== key) return false
    if (!matchModifier(e, s.modifiers)) return false
    if (s.enabled && !s.enabled()) return false
    return true
  })

  if (globalMatches.length > 0) {
    e.preventDefault()
    globalMatches[0].action()
    return
  }

  sequenceBuffer.value.push(key)
  if (sequenceTimeout.value) clearTimeout(sequenceTimeout.value)
  sequenceTimeout.value = setTimeout(() => {
    sequenceBuffer.value = []
  }, SEQUENCE_TIMEOUT_MS)

  const seqMatches = registeredShortcuts.value.filter((s) => {
    if (!s.sequence) return false
    if (s.enabled && !s.enabled()) return false
    const buf = sequenceBuffer.value
    const seq = s.sequence.map((k) => k.toLowerCase())
    if (buf.length < seq.length) return false
    const tail = buf.slice(-seq.length)
    return tail.every((k, i) => k === seq[i])
  })

  if (seqMatches.length > 0) {
    e.preventDefault()
    seqMatches[0].action()
    sequenceBuffer.value = []
    return
  }
}

export function useKeyboardShortcuts() {
  function register(shortcut: Shortcut) {
    const exists = registeredShortcuts.value.find(
      (s) => s.key === shortcut.key && s.scope === shortcut.scope && JSON.stringify(s.sequence) === JSON.stringify(shortcut.sequence)
    )
    if (!exists) {
      registeredShortcuts.value.push(shortcut)
    }
  }

  function unregister(key: string, scope: 'global' | 'local' = 'global') {
    registeredShortcuts.value = registeredShortcuts.value.filter(
      (s) => !(s.key === key && s.scope === scope)
    )
  }

  function unregisterAll(scope?: 'global' | 'local') {
    if (scope) {
      registeredShortcuts.value = registeredShortcuts.value.filter((s) => s.scope !== scope)
    } else {
      registeredShortcuts.value = []
    }
  }

  const shortcuts = computed(() => registeredShortcuts.value)

  return {
    register,
    unregister,
    unregisterAll,
    shortcuts,
  }
}

let initialized = false

export function initKeyboardShortcuts() {
  if (initialized) return
  initialized = true
  document.addEventListener('keydown', handleKeydown)
}

export function destroyKeyboardShortcuts() {
  document.removeEventListener('keydown', handleKeydown)
  initialized = false
}
