import { describe, it, expect, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createRouter, createMemoryHistory, type RouteRecordRaw } from 'vue-router'
import i18n from '@/i18n'
import Sidebar from '@/components/layout/Sidebar.vue'
import NavItem from '@/components/layout/NavItem.vue'
import { setApiMode } from '@/api/client'

const SIDEBAR_PATHS = [
  '/board',
  '/system',
  '/kanban',
  '/list',
  '/components',
  '/policies',
  '/constraints',
  '/sandbox',
  '/rag',
  '/finops',
  '/auto-healing',
  '/replay',
  '/executive',
  '/users',
  '/chat',
  '/mcp',
  '/hitl',
  '/organization',
  '/governance-matrix',
  '/audit-log',
  '/agents/studio',
  '/graph',
  '/analysis',
  '/analytics',
]

async function mountSidebar() {
  const routes: RouteRecordRaw[] = SIDEBAR_PATHS.map((path) => ({
    path,
    component: { template: '<div />' },
  }))
  const router = createRouter({ history: createMemoryHistory(), routes })
  await router.push('/board')
  await router.isReady()
  const wrapper = mount(Sidebar, {
    global: { plugins: [createPinia(), i18n, router] },
  })
  return wrapper
}

function navItemPaths(wrapper: Awaited<ReturnType<typeof mountSidebar>>) {
  return wrapper.findAllComponents(NavItem).map((item) => (item.props('item') as { path: string }).path)
}

describe('Sidebar', () => {
  afterEach(() => setApiMode('mock'))

  it('renders every nav item in a stable order in real mode', async () => {
    setApiMode('real')
    const wrapper = await mountSidebar()
    expect(navItemPaths(wrapper)).toEqual(SIDEBAR_PATHS)
  })

  it('keeps ADMIN-restricted routes visible in real mode', async () => {
    setApiMode('real')
    const wrapper = await mountSidebar()
    const paths = navItemPaths(wrapper)
    expect(paths).toContain('/constraints')
    expect(paths).toContain('/users')
    expect(paths).toContain('/organization')
    expect(paths).toContain('/audit-log')
  })

  it('renders the same items in mock mode', async () => {
    setApiMode('mock')
    const wrapper = await mountSidebar()
    expect(navItemPaths(wrapper)).toEqual(SIDEBAR_PATHS)
  })

  it('renders localized labels without raw i18n keys', async () => {
    setApiMode('real')
    const wrapper = await mountSidebar()
    const labels = wrapper
      .findAllComponents(NavItem)
      .map((item) => (item.props('item') as { label: string }).label)
    expect(labels.every((label) => label.length > 0)).toBe(true)
    expect(labels.some((label) => label.startsWith('nav.'))).toBe(false)
  })

  it('flags pending features but not completed ones', async () => {
    setApiMode('real')
    const wrapper = await mountSidebar()
    const pending = wrapper
      .findAllComponents(NavItem)
      .filter((item) => item.props('pending'))
      .map((item) => (item.props('item') as { path: string }).path)
    expect(pending).toContain('/finops')
    expect(pending).toContain('/organization')
    expect(pending).not.toContain('/rag')
    expect(pending).not.toContain('/mcp')
  })
})
