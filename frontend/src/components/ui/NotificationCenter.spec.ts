import { describe, it, expect, beforeEach, vi } from 'vitest'
import { nextTick } from 'vue'
import { setActivePinia, createPinia } from 'pinia'
import { mountComponent } from '@/test/mount'
import NotificationCenter from '@/components/ui/NotificationCenter.vue'
import { useNotificationsStore } from '@/stores/notificationsStore'
import { useHitlStore } from '@/stores/hitlStore'
import { setApiMode } from '@/api/client'

const { pushMock } = vi.hoisted(() => ({ pushMock: vi.fn() }))
vi.mock('vue-router', () => ({ useRouter: () => ({ push: pushMock }) }))

function bodyButtonByText(text: string): HTMLButtonElement | undefined {
  return Array.from(document.body.querySelectorAll('button')).find(
    b => b.textContent?.trim() === text,
  )
}

function rowByText(text: string): HTMLElement {
  const row = Array.from(document.body.querySelectorAll('div.group')).find(el =>
    el.textContent?.includes(text),
  )
  if (!row) throw new Error(`notification row not found: ${text}`)
  return row as HTMLElement
}

function messageParagraph(row: HTMLElement): HTMLElement {
  const p = row.querySelector('p')
  if (!p) throw new Error('message paragraph not found')
  return p as HTMLElement
}

async function openPanel(wrapper: ReturnType<typeof mountComponent>['wrapper']) {
  await wrapper.find('button').trigger('click')
  await nextTick()
  await nextTick()
}

describe('NotificationCenter', () => {
  beforeEach(() => {
    setApiMode('mock')
    setActivePinia(createPinia())
    pushMock.mockClear()
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

    await openPanel(wrapper)

    const systemChip = bodyButtonByText('System')
    expect(systemChip).toBeDefined()
    expect(document.body.textContent).toContain('Welcome to Tasker')
    expect(document.body.textContent).toContain('HITL Approval Required')

    systemChip!.click()
    await nextTick()

    expect(document.body.textContent).toContain('Welcome to Tasker')
    expect(document.body.textContent).not.toContain('HITL Approval Required')
  })

  it('expands the full message inline without navigating, and opens via the Abrir button', async () => {
    const { wrapper, pinia } = mountComponent(NotificationCenter)
    setActivePinia(pinia)
    const store = useNotificationsStore()
    store.addNotification({
      title: 'Inline detail unique',
      message: 'Mensaje completo de la notificacion que no cabe en una linea',
      category: 'welcome',
      requiresAction: false,
      linkTo: { path: '/users' },
    })

    await openPanel(wrapper)

    const row = rowByText('Inline detail unique')
    expect(row.getAttribute('aria-expanded')).toBe('false')
    expect(messageParagraph(row).className).toContain('truncate')
    expect(row.textContent).not.toContain('Open')
    expect(store.notifications.find(n => n.title === 'Inline detail unique')?.read).toBe(false)

    row.click()
    await nextTick()

    expect(row.getAttribute('aria-expanded')).toBe('true')
    expect(messageParagraph(row).className).toContain('whitespace-pre-wrap')
    expect(messageParagraph(row).className).not.toContain('truncate')
    expect(pushMock).not.toHaveBeenCalled()
    expect(store.notifications.find(n => n.title === 'Inline detail unique')?.read).toBe(true)

    const openButton = Array.from(row.querySelectorAll('button')).find(
      b => b.textContent?.trim() === 'Open',
    )
    expect(openButton).toBeDefined()

    openButton!.click()
    await nextTick()
    expect(pushMock).toHaveBeenCalledTimes(1)
    expect(pushMock).toHaveBeenCalledWith({ path: '/users' })

    row.click()
    await nextTick()
    expect(row.getAttribute('aria-expanded')).toBe('false')
    expect(row.textContent).not.toContain('Open')
  })

  it('keeps a single expanded row at a time', async () => {
    const { wrapper, pinia } = mountComponent(NotificationCenter)
    setActivePinia(pinia)
    const store = useNotificationsStore()
    store.addNotification({
      title: 'First expanded unique',
      message: 'primera notificacion',
      category: 'welcome',
      requiresAction: false,
    })
    store.addNotification({
      title: 'Second expanded unique',
      message: 'segunda notificacion',
      category: 'welcome',
      requiresAction: false,
    })

    await openPanel(wrapper)

    const firstRow = rowByText('First expanded unique')
    firstRow.click()
    await nextTick()
    expect(firstRow.getAttribute('aria-expanded')).toBe('true')

    const secondRow = rowByText('Second expanded unique')
    secondRow.click()
    await nextTick()

    expect(secondRow.getAttribute('aria-expanded')).toBe('true')
    expect(firstRow.getAttribute('aria-expanded')).toBe('false')
    expect(firstRow.textContent).not.toContain('Open')
  })

  it('opens the HITL quick action instead of expanding', async () => {
    const { wrapper, pinia } = mountComponent(NotificationCenter)
    setActivePinia(pinia)
    const store = useNotificationsStore()
    const hitlStore = useHitlStore()
    store.addNotification({
      title: 'HITL quick action unique',
      message: 'solicitud pendiente de aprobacion',
      category: 'hitl',
      requiresAction: true,
      hitlRequestId: 'req-77',
      linkTo: { path: '/hitl' },
    })

    await openPanel(wrapper)

    const row = rowByText('HITL quick action unique')
    row.click()
    await nextTick()

    expect(hitlStore.quickActionRequestId).toBe('req-77')
    expect(row.getAttribute('aria-expanded')).toBe('false')
    expect(row.textContent).not.toContain('Open')
    expect(pushMock).not.toHaveBeenCalled()
  })
})
