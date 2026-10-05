import { describe, it, expect, beforeEach } from 'vitest'
import { nextTick } from 'vue'
import { setActivePinia, createPinia } from 'pinia'
import { mountComponent } from '@/test/mount'
import NotificationCenter from '@/components/ui/NotificationCenter.vue'
import { useNotificationsStore } from '@/stores/notificationsStore'
import { setApiMode } from '@/api/client'

function bodyButtonByText(text: string): HTMLButtonElement | undefined {
  return Array.from(document.body.querySelectorAll('button')).find(
    b => b.textContent?.trim() === text,
  )
}

describe('NotificationCenter', () => {
  beforeEach(() => {
    setApiMode('mock')
    setActivePinia(createPinia())
  })

  it('opens the panel with the System channel chip and welcome notifications', async () => {
    const { wrapper, pinia } = mountComponent(NotificationCenter)
    setActivePinia(pinia)
    const store = useNotificationsStore()
    store.addNotification({
      title: 'Welcome to Tasker',
      message: 'installed correctly',
      category: 'welcome',
      requiresAction: true,
      linkTo: { path: '/users' },
    })

    await wrapper.find('button').trigger('click')
    await nextTick()
    await nextTick()

    const systemChip = bodyButtonByText('System')
    expect(systemChip).toBeDefined()
    expect(document.body.textContent).toContain('Welcome to Tasker')
    expect(document.body.textContent).toContain('HITL Approval Required')

    systemChip!.click()
    await nextTick()

    expect(document.body.textContent).toContain('Welcome to Tasker')
    expect(document.body.textContent).not.toContain('HITL Approval Required')
  })
})
