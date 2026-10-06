import { describe, it, expect, beforeEach, vi } from 'vitest'
import { nextTick } from 'vue'
import { setActivePinia, createPinia } from 'pinia'
import { mountComponent } from '@/test/mount'
import NotificationsFeed from '@/components/dashboard/NotificationsFeed.vue'
import { useNotificationsStore } from '@/stores/notificationsStore'
import { setApiMode } from '@/api/client'

const { pushMock } = vi.hoisted(() => ({ pushMock: vi.fn() }))
vi.mock('vue-router', () => ({ useRouter: () => ({ push: pushMock }) }))

describe('NotificationsFeed', () => {
  beforeEach(() => {
    setApiMode('mock')
    setActivePinia(createPinia())
    pushMock.mockClear()
  })

  it('expands the full message on click, marks it read, and opens via the Abrir button', async () => {
    const { wrapper, pinia } = mountComponent(NotificationsFeed)
    setActivePinia(pinia)
    const store = useNotificationsStore()
    store.addNotification({
      title: 'Feed detail unique',
      message: 'Mensaje largo del feed que solo se lee expandido',
      category: 'welcome',
      requiresAction: false,
      linkTo: { path: '/users' },
    })
    await nextTick()

    const row = wrapper.find('li')
    expect(row.exists()).toBe(true)
    const messageParagraph = () => row.find('p.text-xs')
    const openButton = () =>
      Array.from(row.findAll('button')).map(b => b.text()).find(t => t === 'Open')

    expect(row.attributes('aria-expanded')).toBe('false')
    expect(messageParagraph().classes()).toContain('truncate')
    expect(openButton()).toBeUndefined()

    await row.trigger('click')

    expect(row.attributes('aria-expanded')).toBe('true')
    expect(messageParagraph().classes()).toContain('whitespace-pre-wrap')
    expect(messageParagraph().classes()).not.toContain('truncate')
    expect(openButton()).toBe('Open')
    expect(store.notifications.find(n => n.title === 'Feed detail unique')?.read).toBe(true)
    expect(pushMock).not.toHaveBeenCalled()

    await row.findAll('button').find(b => b.text() === 'Open')!.trigger('click')
    expect(pushMock).toHaveBeenCalledTimes(1)
    expect(pushMock).toHaveBeenCalledWith({ path: '/users' })

    await row.trigger('click')
    expect(row.attributes('aria-expanded')).toBe('false')
    expect(openButton()).toBeUndefined()
  })

  it('collapses when clicking the same row twice and keeps other rows closed', async () => {
    const { wrapper, pinia } = mountComponent(NotificationsFeed)
    setActivePinia(pinia)
    const store = useNotificationsStore()
    store.addNotification({
      title: 'Feed first unique',
      message: 'primera del feed',
      category: 'welcome',
      requiresAction: false,
    })
    store.addNotification({
      title: 'Feed second unique',
      message: 'segunda del feed',
      category: 'welcome',
      requiresAction: false,
    })
    await nextTick()

    const rows = wrapper.findAll('li')
    expect(rows).toHaveLength(2)

    await rows[0].trigger('click')
    expect(rows[0].attributes('aria-expanded')).toBe('true')

    await rows[1].trigger('click')
    expect(rows[1].attributes('aria-expanded')).toBe('true')
    expect(rows[0].attributes('aria-expanded')).toBe('false')

    await rows[1].trigger('click')
    expect(rows[1].attributes('aria-expanded')).toBe('false')
  })
})
