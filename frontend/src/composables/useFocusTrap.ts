import { getCurrentInstance, onBeforeUnmount, onMounted, nextTick, ref, type Ref } from 'vue'

export interface FocusTrapOptions {
  immediate?: boolean
  closeOnEsc?: boolean
  onClose?: () => void
}

const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

export function useFocusTrap(container: Ref<HTMLElement | null>, options: FocusTrapOptions = {}) {
  const { immediate = true, closeOnEsc = true, onClose } = options
  const previousFocus = ref<HTMLElement | null>(null)

  function focusableElements(): HTMLElement[] {
    if (!container.value) return []
    return Array.from(container.value.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR))
  }

  function containsActive(): boolean {
    const active = document.activeElement
    return container.value !== null && active !== null && container.value.contains(active)
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape' && closeOnEsc) {
      e.preventDefault()
      e.stopPropagation()
      onClose?.()
      return
    }
    if (e.key !== 'Tab') return

    const items = focusableElements()
    if (items.length === 0) {
      e.preventDefault()
      container.value?.focus()
      return
    }

    const first = items[0]
    const last = items[items.length - 1]
    const active = document.activeElement

    if (e.shiftKey) {
      if (!containsActive() || active === first) {
        e.preventDefault()
        last.focus()
      }
    } else if (!containsActive() || active === last) {
      e.preventDefault()
      first.focus()
    }
  }

  function activate() {
    previousFocus.value = document.activeElement as HTMLElement | null
    document.addEventListener('keydown', onKeydown, true)
    nextTick(() => {
      const auto = container.value?.querySelector<HTMLElement>('[autofocus]')
      if (auto) {
        auto.focus()
        return
      }
      const items = focusableElements()
      if (items.length > 0) items[0].focus()
      else container.value?.focus()
    })
  }

  function deactivate() {
    document.removeEventListener('keydown', onKeydown, true)
    const prev = previousFocus.value
    previousFocus.value = null
    if (prev && prev.isConnected) prev.focus()
  }

  if (getCurrentInstance()) {
    onBeforeUnmount(deactivate)
    if (immediate) {
      onMounted(activate)
    }
  }

  return { activate, deactivate, focusableElements }
}
