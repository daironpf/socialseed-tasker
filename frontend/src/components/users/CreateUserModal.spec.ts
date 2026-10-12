import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { mountComponent } from '@/test/mount'
import CreateUserModal from '@/components/users/CreateUserModal.vue'
import { fetchSkills } from '@/api/catalogsApi'

vi.mock('@/api/client', () => ({
  isMockMode: () => false,
  default: { get: vi.fn().mockResolvedValue({ data: { data: [] } }) },
}))
vi.mock('@/api/catalogsApi', () => ({
  fetchSkills: vi.fn().mockResolvedValue([]),
}))

describe('CreateUserModal', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders the human form on open and loads skill suggestions', async () => {
    const { wrapper } = mountComponent(CreateUserModal, { props: { show: false } })
    await wrapper.setProps({ show: true })
    await flushPromises()

    expect(wrapper.find('h2').text()).toBe('New User')
    expect(fetchSkills).toHaveBeenCalledTimes(1)
  })

  it('switches to agent mode without closing the modal (regression: @ in i18n placeholder)', async () => {
    const { wrapper } = mountComponent(CreateUserModal, { props: { show: true } })
    await flushPromises()

    const agentButton = wrapper.findAll('button').find(b => b.text().includes('AiAgent'))
    await agentButton!.trigger('click')
    await flushPromises()

    // The agent email placeholder contains '@'; vue-i18n must not treat it as
    // a linked-message operator (it used to throw and kill the modal render).
    const emailInput = wrapper.findAll('input').find(i => i.attributes('type') === 'email')
    expect(emailInput!.attributes('placeholder')).toBe('agent@socialseed.ai')

    expect(wrapper.find('.fixed').exists()).toBe(true)
    expect(wrapper.find('h2').text()).toBe('Create AI Agent')
  })

  it('renders the catalog skills as clickable chips and adds them without typing (#576 picker fix)', async () => {
    vi.mocked(fetchSkills).mockResolvedValue([
      { id: 'python', name: 'Python' },
      { id: 'vue', name: 'Vue' },
    ])
    const { wrapper } = mountComponent(CreateUserModal, { props: { show: false } })
    await wrapper.setProps({ show: true })
    await flushPromises()

    // The native datalist never opened on "+"; the picker chips are always visible.
    expect(wrapper.find('datalist').exists()).toBe(false)
    const pythonChip = wrapper.findAll('button').find(b => b.text() === '+ Python')
    expect(pythonChip).toBeDefined()

    await pythonChip!.trigger('click')
    await flushPromises()

    const chips = wrapper.findAll('span')
    expect(chips.some(s => s.text().includes('Python') && !s.text().includes('+'))).toBe(true)
  })

  it('resets to human and reopens after the parent closes it', async () => {
    const { wrapper } = mountComponent(CreateUserModal, { props: { show: true } })
    await flushPromises()

    await wrapper.findAll('button').find(b => b.text().includes('AiAgent'))!.trigger('click')
    await wrapper.setProps({ show: false })
    await flushPromises()
    expect(wrapper.find('.fixed').exists()).toBe(false)

    await wrapper.setProps({ show: true })
    await flushPromises()
    expect(wrapper.find('.fixed').exists()).toBe(true)
    expect(wrapper.find('h2').text()).toBe('New User')
  })

  it('opens the floating picker on "+" and applies the selection (issue #577)', async () => {
    vi.mocked(fetchSkills).mockResolvedValue([
      { id: 'python', name: 'Python' },
      { id: 'vue', name: 'Vue' },
    ])
    const { wrapper } = mountComponent(CreateUserModal, { props: { show: false } })
    await wrapper.setProps({ show: true })
    await flushPromises()

    await wrapper.findAll('button').find(b => b.attributes('aria-label') === 'Add skills')!.trigger('click')
    await flushPromises()

    const boxes = wrapper.findAll('input[type="checkbox"]')
    expect(boxes).toHaveLength(2)
    await boxes[0].setValue(true)
    await wrapper.findAll('button').find(b => b.text() === 'Apply')!.trigger('click')
    await flushPromises()

    // The picker closed and the chip is selected without typing.
    expect(wrapper.find('input[placeholder="Search skills..."]').exists()).toBe(false)
    const chips = wrapper.findAll('span')
    expect(chips.some(s => s.text().includes('Python') && !s.text().includes('+'))).toBe(true)
  })
})
