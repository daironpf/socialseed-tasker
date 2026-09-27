import { describe, it, expect } from 'vitest'
import FilterBuilder from '@/components/ui/FilterBuilder.vue'
import { mountComponent } from '@/test/mount'
import { useUiStore } from '@/stores/uiStore'

function findButtonByText(wrapper: ReturnType<typeof mountComponent>['wrapper'], text: string) {
  return wrapper.findAll('button').find(b => b.text().includes(text))
}

describe('FilterBuilder', () => {
  it('renders the core filter controls', () => {
    const { wrapper } = mountComponent(FilterBuilder, { global: { stubs: { Teleport: true } } })

    expect(findButtonByText(wrapper, 'Status')?.exists()).toBe(true)
    expect(findButtonByText(wrapper, 'Priority')?.exists()).toBe(true)
    expect(findButtonByText(wrapper, 'Labels')?.exists()).toBe(true)
    expect(findButtonByText(wrapper, 'Tech Debt')?.exists()).toBe(true)
    expect(findButtonByText(wrapper, 'Affected Files')?.exists()).toBe(true)
  })

  it('cycles the tri-state tech debt toggle through null/true/false', async () => {
    const { wrapper, pinia } = mountComponent(FilterBuilder, { global: { stubs: { Teleport: true } } })
    const ui = useUiStore(pinia)
    const toggle = findButtonByText(wrapper, 'Tech Debt')!

    expect(ui.filters.hasTechDebt).toBeNull()

    await toggle.trigger('click')
    expect(ui.filters.hasTechDebt).toBe(true)
    expect(toggle.text()).toContain('YES')

    await toggle.trigger('click')
    expect(ui.filters.hasTechDebt).toBe(false)
    expect(toggle.text()).toContain('NO')

    await toggle.trigger('click')
    expect(ui.filters.hasTechDebt).toBeNull()
  })

  it('toggles a status inside the dropdown and shows a removable chip', async () => {
    const { wrapper, pinia } = mountComponent(FilterBuilder, { global: { stubs: { Teleport: true } } })
    const ui = useUiStore(pinia)

    await findButtonByText(wrapper, 'Status')!.trigger('click')

    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    expect(checkboxes.length).toBeGreaterThanOrEqual(5)

    await checkboxes[0].trigger('change')
    expect(ui.filters.status).toEqual(['OPEN'])
    expect(wrapper.text()).toContain('Open')

    const remove = wrapper.find('button[aria-label="Remove Status filter"]')
    expect(remove.exists()).toBe(true)
    await remove.trigger('click')
    expect(ui.filters.status).toEqual([])
    expect(wrapper.text()).not.toContain('Open')
  })

  it('clears every active filter with Clear All', async () => {
    const { wrapper, pinia } = mountComponent(FilterBuilder, { global: { stubs: { Teleport: true } } })
    const ui = useUiStore(pinia)

    await findButtonByText(wrapper, 'Tech Debt')!.trigger('click')
    await findButtonByText(wrapper, 'Priority')!.trigger('click')
    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    await checkboxes[0].trigger('change')

    expect(ui.hasActiveFilters()).toBe(true)
    expect(wrapper.text()).toContain('Clear All')

    await findButtonByText(wrapper, 'Clear All')!.trigger('click')

    expect(ui.hasActiveFilters()).toBe(false)
    expect(ui.filters.priority).toEqual([])
    expect(ui.filters.hasTechDebt).toBeNull()
  })

  it('shows the empty state for labels when none are available', async () => {
    const { wrapper } = mountComponent(FilterBuilder, { global: { stubs: { Teleport: true } } })

    await findButtonByText(wrapper, 'Labels')!.trigger('click')

    expect(wrapper.text()).toContain('No labels available')
  })

  it('closes a dropdown when clicking outside', async () => {
    const { wrapper } = mountComponent(FilterBuilder, { global: { stubs: { Teleport: true } } })

    await findButtonByText(wrapper, 'Status')!.trigger('click')
    expect(wrapper.findAll('input[type="checkbox"]').length).toBeGreaterThan(0)

    await wrapper.trigger('click')

    expect(wrapper.findAll('input[type="checkbox"]')).toHaveLength(0)
  })
})
