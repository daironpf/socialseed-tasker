import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { mountComponent } from '@/test/mount'
import SkillPickerModal from '@/components/users/SkillPickerModal.vue'
import { fetchSkills } from '@/api/catalogsApi'
import { fetchAgentSkills, createAgentSkill } from '@/api/agentSkillsApi'
import { useUsersStore } from '@/stores/usersStore'

const mockState = vi.hoisted(() => ({ mockMode: false }))

vi.mock('@/api/client', () => ({
  isMockMode: () => mockState.mockMode,
  default: { get: vi.fn(), post: vi.fn() },
}))
vi.mock('@/api/catalogsApi', () => ({
  fetchSkills: vi.fn().mockResolvedValue([]),
  resetCatalogsCache: vi.fn(),
}))
vi.mock('@/api/agentSkillsApi', () => ({
  fetchAgentSkills: vi.fn().mockResolvedValue([]),
  createAgentSkill: vi.fn(),
}))

function mountPicker(
  mode: 'human' | 'agent' = 'human',
  selected: string[] = [],
  show = true,
) {
  return mountComponent(SkillPickerModal, {
    props: { show, mode, selected },
  })
}

describe('SkillPickerModal (issue #577)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockState.mockMode = false
    vi.mocked(fetchSkills).mockResolvedValue([])
    vi.mocked(fetchAgentSkills).mockResolvedValue([])
  })

  it('renders the human catalog as checkboxes with the current selection checked', async () => {
    vi.mocked(fetchSkills).mockResolvedValue([
      { id: 'python', name: 'Python' },
      { id: 'vue', name: 'Vue' },
      { id: 'go', name: 'Go' },
    ])
    const { wrapper } = mountPicker('human', ['Python'])
    await flushPromises()

    expect(fetchSkills).toHaveBeenCalledTimes(1)
    const boxes = wrapper.findAll('input[type="checkbox"]')
    expect(boxes).toHaveLength(3)
    expect((boxes[0].element as HTMLInputElement).checked).toBe(true)
    expect((boxes[1].element as HTMLInputElement).checked).toBe(false)

    await boxes[1].setValue(true)
    await boxes[2].setValue(true)
    await wrapper.findAll('button').find(b => b.text() === 'Apply')!.trigger('click')

    expect(wrapper.emitted('apply')![0][0]).toEqual(['Python', 'Vue', 'Go'])
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('filters the catalog with the search input', async () => {
    vi.mocked(fetchSkills).mockResolvedValue([
      { id: 'go', name: 'Go' },
      { id: 'docker', name: 'Docker' },
      { id: 'kubernetes', name: 'Kubernetes' },
    ])
    const { wrapper } = mountPicker('human')
    await flushPromises()

    await wrapper.find('input[placeholder="Search skills..."]').setValue('dock')
    await flushPromises()

    expect(wrapper.text()).toContain('Docker')
    expect(wrapper.text()).not.toContain('Kubernetes')
    expect(wrapper.text()).not.toContain('Go')
  })

  it('adds a typed custom name in human mode without a catalog row', async () => {
    const { wrapper } = mountPicker('human', [])
    await flushPromises()

    await wrapper.find('input[placeholder="Type a custom skill name..."]').setValue('Rust')
    await wrapper.findAll('button').find(b => b.text() === 'Add')!.trigger('click')
    await wrapper.findAll('button').find(b => b.text() === 'Apply')!.trigger('click')

    expect(wrapper.emitted('apply')![0][0]).toEqual(['Rust'])
  })

  it('expands the behavior text of an agent skill without loading the human catalog', async () => {
    vi.mocked(fetchAgentSkills).mockResolvedValue([
      {
        id: 'code-reviewer',
        name: 'Code Reviewer',
        behavior: 'Always prefer readable code over clever code.',
      },
    ])
    const { wrapper } = mountPicker('agent')
    await flushPromises()

    expect(fetchAgentSkills).toHaveBeenCalledTimes(1)
    expect(fetchSkills).not.toHaveBeenCalled()
    expect(wrapper.text()).not.toContain('Always prefer readable code')

    await wrapper.findAll('button').find(b => b.text() === 'Behavior')!.trigger('click')

    expect(wrapper.text()).toContain('Always prefer readable code')
  })

  it('creates an agent skill through POST and applies it selected', async () => {
    vi.mocked(createAgentSkill).mockResolvedValue({
      id: 'security-analyst',
      name: 'Security Analyst',
      behavior: 'Assume hostile input.',
    })
    const { wrapper } = mountPicker('agent')
    await flushPromises()

    await wrapper.findAll('button').find(b => b.text().includes('New skill'))!.trigger('click')
    await wrapper.find('input[placeholder="Skill name"]').setValue('Security Analyst')
    await wrapper.find('textarea').setValue('Assume hostile input.')
    await wrapper.findAll('button').find(b => b.text() === 'Create & select')!.trigger('click')
    await flushPromises()

    expect(createAgentSkill).toHaveBeenCalledWith('Security Analyst', 'Assume hostile input.')
    const boxes = wrapper.findAll('input[type="checkbox"]')
    expect(boxes).toHaveLength(1)
    expect((boxes[0].element as HTMLInputElement).checked).toBe(true)

    await wrapper.findAll('button').find(b => b.text() === 'Apply')!.trigger('click')
    expect(wrapper.emitted('apply')![0][0]).toEqual(['Security Analyst'])
  })

  it('shows an inline error when the skill creation fails and keeps the form', async () => {
    vi.mocked(createAgentSkill).mockRejectedValue(new Error('409 conflict'))
    const { wrapper } = mountPicker('agent')
    await flushPromises()

    await wrapper.findAll('button').find(b => b.text().includes('New skill'))!.trigger('click')
    await wrapper.find('input[placeholder="Skill name"]').setValue('Duplicated')
    await wrapper.find('textarea').setValue('behavior')
    await wrapper.findAll('button').find(b => b.text() === 'Create & select')!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Could not create the skill. Try again.')
    expect(wrapper.find('input[placeholder="Skill name"]').exists()).toBe(true)
  })

  it('derives the mock vocabulary from the users store without calling the API', async () => {
    mockState.mockMode = true
    const { wrapper, pinia } = mountPicker('human', [], false)
    const store = useUsersStore(pinia)
    store.users = [
      {
        id: 'u1',
        username: 'ana',
        email: 'ana@x.com',
        type: 'human',
        role: 'DEVELOPER',
        avatar: '👩‍💻',
        skills: ['Python', 'Vue'],
        issues_assigned: 0,
        issues_created: 0,
        last_active: '2026-10-01T00:00:00Z',
      },
    ]
    await wrapper.setProps({ show: true })
    await flushPromises()

    expect(fetchSkills).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Python')
    expect(wrapper.text()).toContain('Vue')
  })

  it('closes without applying when the backdrop is clicked', async () => {
    const { wrapper } = mountPicker('human')
    await flushPromises()

    await wrapper.trigger('click')

    expect(wrapper.emitted('close')).toBeTruthy()
    expect(wrapper.emitted('apply')).toBeUndefined()
  })
})
