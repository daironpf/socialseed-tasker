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
})
