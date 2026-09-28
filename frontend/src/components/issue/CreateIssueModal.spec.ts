import { describe, it, expect } from 'vitest'
import { nextTick } from 'vue'
import { mountComponent } from '@/test/mount'
import CreateIssueModal from '@/components/issue/CreateIssueModal.vue'

function press(key: string, init: KeyboardEventInit = {}) {
  document.body.dispatchEvent(new KeyboardEvent('keydown', { key, cancelable: true, bubbles: true, ...init }))
}

describe('CreateIssueModal', () => {
  it('exposes dialog semantics with an accessible name', () => {
    const { wrapper } = mountComponent(CreateIssueModal)

    const root = wrapper.element as HTMLElement
    expect(root.getAttribute('role')).toBe('dialog')
    expect(root.getAttribute('aria-modal')).toBe('true')
    expect(root.getAttribute('aria-label')).toBeTruthy()
  })

  it('moves focus into the dialog on mount', async () => {
    const { wrapper } = mountComponent(CreateIssueModal)
    await nextTick()
    await nextTick()

    const root = wrapper.element as HTMLElement
    expect(root.contains(document.activeElement)).toBe(true)
    expect(document.activeElement?.getAttribute('autofocus')).not.toBeNull()
  })

  it('keeps Tab inside the dialog and closes on Escape', async () => {
    const { wrapper } = mountComponent(CreateIssueModal)
    await nextTick()
    await nextTick()

    const root = wrapper.element as HTMLElement
    const focusables = Array.from(
      root.querySelectorAll<HTMLElement>('a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled])'),
    )
    const first = focusables[0]
    const last = focusables[focusables.length - 1]

    last.focus()
    press('Tab')
    expect(document.activeElement).toBe(first)

    first.focus()
    press('Tab', { shiftKey: true })
    expect(document.activeElement).toBe(last)

    press('Escape')
    expect(wrapper.emitted('close')).toBeTruthy()
  })
})
