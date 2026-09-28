import { describe, it, expect } from 'vitest'
import { nextTick } from 'vue'
import { mountComponent } from '@/test/mount'
import KeyboardShortcutsHelp from '@/components/ui/KeyboardShortcutsHelp.vue'

function rowKeys(): string[] {
  const rows = document.body.querySelectorAll('[role="dialog"] .space-y-1\\.5 > div')
  return Array.from(rows).map((row) =>
    Array.from(row.querySelectorAll('kbd'))
      .map((k) => k.textContent?.trim() ?? '')
      .join('+'),
  )
}

describe('KeyboardShortcutsHelp', () => {
  it('renders as a labelled modal dialog', async () => {
    const { wrapper } = mountComponent(KeyboardShortcutsHelp)
    ;(wrapper.vm as unknown as { toggle: () => void }).toggle()
    await nextTick()
    await nextTick()

    const dialog = document.body.querySelector('[role="dialog"]')
    expect(dialog).not.toBeNull()
    expect(dialog?.getAttribute('aria-modal')).toBe('true')
    expect(dialog?.getAttribute('aria-label')).toBeTruthy()

    ;(wrapper.vm as unknown as { close: () => void }).close()
  })

  it('documents exactly the shortcuts that are registered', async () => {
    const { wrapper } = mountComponent(KeyboardShortcutsHelp)
    ;(wrapper.vm as unknown as { open: () => void }).open()
    await nextTick()
    await nextTick()

    expect(rowKeys()).toEqual([
      'C',
      'G+I',
      'G+K',
      'G+G',
      'G+B',
      'G+U',
      'G+C',
      'Ctrl+K',
      'J',
      'K',
      'Enter',
      'Esc',
      '?',
      'D',
    ])

    ;(wrapper.vm as unknown as { close: () => void }).close()
  })

  it('traps focus in the dialog and closes on Escape', async () => {
    const { wrapper } = mountComponent(KeyboardShortcutsHelp)
    ;(wrapper.vm as unknown as { toggle: () => void }).toggle()
    await nextTick()
    await nextTick()

    const dialog = document.body.querySelector('[role="dialog"]') as HTMLElement
    expect(dialog.contains(document.activeElement)).toBe(true)

    document.body.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }))
    await nextTick()
    await nextTick()

    expect(document.body.querySelector('[role="dialog"]')).toBeNull()
  })
})
