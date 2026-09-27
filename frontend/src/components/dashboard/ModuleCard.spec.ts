import { describe, it, expect } from 'vitest'
import ModuleCard from '@/components/dashboard/ModuleCard.vue'
import { mountComponent } from '@/test/mount'

describe('ModuleCard', () => {
  it('renders the module title', () => {
    const { wrapper } = mountComponent(ModuleCard, { props: { title: 'Team Workload' } })

    expect(wrapper.find('h3').text()).toBe('Team Workload')
  })

  it('renders the default slot content', () => {
    const { wrapper } = mountComponent(ModuleCard, {
      props: { title: 'Activity' },
      slots: { default: '<p class="body">Module body</p>' },
    })

    expect(wrapper.find('.body').text()).toBe('Module body')
  })

  it('renders the action slot inside the header row', () => {
    const { wrapper } = mountComponent(ModuleCard, {
      props: { title: 'Compliance' },
      slots: { action: '<button class="action-btn">Refresh</button>', default: 'content' },
    })

    const action = wrapper.find('.action-btn')
    expect(action.exists()).toBe(true)
    expect(action.text()).toBe('Refresh')
    expect(wrapper.find('h3').text()).toBe('Compliance')
  })

  it('renders even without slots', () => {
    const { wrapper } = mountComponent(ModuleCard, { props: { title: 'Empty' } })

    expect(wrapper.find('h3').exists()).toBe(true)
    expect(wrapper.text()).toContain('Empty')
  })
})
