import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { mountComponent } from '@/test/mount'
import EditUserModal from '@/components/users/EditUserModal.vue'
import { resetCatalogsCache } from '@/api/catalogsApi'
import { fetchUserSkills, addUserSkill, removeUserSkill } from '@/api/userSkillsApi'
import type { User } from '@/types'

const mockState = vi.hoisted(() => ({ mockMode: false }))

vi.mock('@/api/client', () => ({
  isMockMode: () => mockState.mockMode,
  default: { get: vi.fn().mockResolvedValue({ data: { data: [] } }) },
}))
vi.mock('@/api/catalogsApi', () => ({
  fetchSkills: vi.fn().mockResolvedValue([]),
  resetCatalogsCache: vi.fn(),
}))
vi.mock('@/api/userSkillsApi', () => ({
  fetchUserSkills: vi.fn(),
  addUserSkill: vi.fn(),
  removeUserSkill: vi.fn(),
}))

const ana: User = {
  id: 'uid-ana',
  username: 'ana',
  email: 'ana@x.com',
  type: 'human',
  role: 'DEVELOPER',
  avatar: '👩‍💻',
  skills: ['Python', 'Vue'],
  issues_assigned: 0,
  issues_created: 0,
  last_active: '2026-10-01T00:00:00Z',
}

function mountModal(user: User = ana) {
  return mountComponent(EditUserModal, {
    props: { show: true, user },
  })
}

describe('EditUserModal — skills management (issue #576)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockState.mockMode = false
    vi.mocked(fetchUserSkills).mockResolvedValue([
      { user_id: 'uid-ana', skill_id: 'python', name: 'Python' },
      { user_id: 'uid-ana', skill_id: 'vue', name: 'Vue' },
    ])
  })

  it('loads the assigned skills from GET /users/{id}/skills on open', async () => {
    const { wrapper } = mountModal()
    await flushPromises()

    expect(fetchUserSkills).toHaveBeenCalledWith('uid-ana')
    const text = wrapper.text()
    expect(text).toContain('Python')
    expect(text).toContain('Vue')
  })

  it('assigns a new skill through POST and refreshes the datalist (find-or-create)', async () => {
    vi.mocked(addUserSkill).mockResolvedValue({
      user_id: 'uid-ana',
      skill_id: 'kubernetes',
      name: 'Kubernetes',
    })
    const { wrapper } = mountModal()
    await flushPromises()

    const input = wrapper.find('input[list="skills-catalog-edit"]')
    await input.setValue('Kubernetes')
    await wrapper.findAll('button').find(b => b.text() === '+')!.trigger('click')
    await flushPromises()

    expect(addUserSkill).toHaveBeenCalledWith('uid-ana', 'Kubernetes')
    expect(resetCatalogsCache).toHaveBeenCalled()
    expect(wrapper.text()).toContain('Kubernetes')
    expect((input.element as HTMLInputElement).value).toBe('')
  })

  it('unlinks a skill on × without deleting the catalog row', async () => {
    vi.mocked(removeUserSkill).mockResolvedValue(undefined)
    const { wrapper } = mountModal()
    await flushPromises()

    const vueChip = wrapper.findAll('span').find(s => s.text().includes('Vue'))
    await vueChip!.find('button').trigger('click')
    await flushPromises()

    expect(removeUserSkill).toHaveBeenCalledWith('uid-ana', 'vue')
    expect(wrapper.text()).not.toContain('Vue')
  })

  it('shows an inline error when add fails and keeps the input value', async () => {
    vi.mocked(addUserSkill).mockRejectedValue(new Error('boom'))
    const { wrapper } = mountModal()
    await flushPromises()

    await wrapper.find('input[list="skills-catalog-edit"]').setValue('Docker')
    await wrapper.findAll('button').find(b => b.text() === '+')!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Could not add the skill. Try again.')
  })

  it('keeps the mock-mode local chips (no API calls) for the in-memory store', async () => {
    mockState.mockMode = true
    const { wrapper } = mountModal()
    await flushPromises()

    // loadAssignedSkills is skipped in mock mode
    expect(fetchUserSkills).not.toHaveBeenCalled()

    await wrapper.find('input[list="skills-catalog-edit"]').setValue('Local Skill')
    await wrapper.findAll('button').find(b => b.text() === '+')!.trigger('click')
    await flushPromises()

    expect(addUserSkill).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Local Skill')

    const chip = wrapper.findAll('span').find(s => s.text().includes('Local Skill'))
    await chip!.find('button').trigger('click')
    await flushPromises()
    expect(removeUserSkill).not.toHaveBeenCalled()
    expect(wrapper.text()).not.toContain('Local Skill')
  })

  it('emits save with the form data including the current skill chips', async () => {
    const { wrapper } = mountModal()
    await flushPromises()

    await wrapper.findAll('button').find(b => b.text() === 'Save changes')!.trigger('click')

    const saveEvents = wrapper.emitted('save')!
    expect(saveEvents).toHaveLength(1)
    expect(saveEvents[0][0]).toMatchObject({
      id: 'uid-ana',
      username: 'ana',
      skills: ['Python', 'Vue'],
    })
  })
})
