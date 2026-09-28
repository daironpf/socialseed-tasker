import { describe, it, expect, vi, afterEach } from 'vitest'
import { ref, nextTick } from 'vue'
import { useFocusTrap } from '@/composables/useFocusTrap'

function buildContainer() {
  const container = document.createElement('div')
  container.innerHTML = `
    <button id="first">first</button>
    <input id="field" />
    <button id="last">last</button>
  `
  document.body.appendChild(container)
  return container
}

function press(key: string, init: KeyboardEventInit = {}) {
  const event = new KeyboardEvent('keydown', { key, cancelable: true, bubbles: true, ...init })
  document.dispatchEvent(event)
  return event
}

describe('useFocusTrap', () => {
  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('focuses the first focusable element on activate', async () => {
    const container = ref<HTMLElement | null>(buildContainer())
    const trap = useFocusTrap(container, { immediate: false })

    trap.activate()
    await nextTick()
    await nextTick()

    expect(document.activeElement?.id).toBe('first')
    trap.deactivate()
  })

  it('wraps Tab from last to first and Shift+Tab from first to last', async () => {
    const container = ref<HTMLElement | null>(buildContainer())
    const trap = useFocusTrap(container, { immediate: false })

    trap.activate()
    await nextTick()
    await nextTick()

    const last = document.getElementById('last') as HTMLElement
    last.focus()
    press('Tab')
    expect(document.activeElement?.id).toBe('first')

    const first = document.getElementById('first') as HTMLElement
    first.focus()
    press('Tab', { shiftKey: true })
    expect(document.activeElement?.id).toBe('last')

    trap.deactivate()
  })

  it('does not intercept Tab from a non-boundary element', async () => {
    const container = ref<HTMLElement | null>(buildContainer())
    const trap = useFocusTrap(container, { immediate: false })

    trap.activate()
    await nextTick()
    await nextTick()

    const field = document.getElementById('field') as HTMLElement
    field.focus()
    const event = press('Tab')
    expect(event.defaultPrevented).toBe(false)
    expect(document.activeElement?.id).toBe('field')

    trap.deactivate()
  })

  it('closes on Escape, stops propagation and restores previous focus', async () => {
    const container = ref<HTMLElement | null>(buildContainer())
    const onClose = vi.fn()
    const trigger = document.createElement('button')
    document.body.appendChild(trigger)
    trigger.focus()

    const trap = useFocusTrap(container, { immediate: false, onClose })
    trap.activate()
    await nextTick()
    await nextTick()
    expect(document.activeElement?.id).toBe('first')

    const event = press('Escape')
    expect(onClose).toHaveBeenCalledTimes(1)
    expect(event.defaultPrevented).toBe(true)

    trap.deactivate()
    expect(document.activeElement).toBe(trigger)
  })

  it('removes the listener on deactivate so Escape no longer fires', async () => {
    const container = ref<HTMLElement | null>(buildContainer())
    const onClose = vi.fn()
    const trap = useFocusTrap(container, { immediate: false, onClose })

    trap.activate()
    await nextTick()
    await nextTick()
    trap.deactivate()

    press('Escape')
    expect(onClose).not.toHaveBeenCalled()
  })
})
