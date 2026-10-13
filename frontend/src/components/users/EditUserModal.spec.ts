import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { mountComponent } from '@/test/mount'
import EditUserModal from '@/components/users/EditUserModal.vue'
import { fetchSkills, resetCatalogsCache } from '@/api/catalogsApi'
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

  it('assigns a new skill through POST on Enter and refreshes the catalog chips', async () => {
    vi.mocked(addUserSkill).mockResolvedValue({
      user_id: 'uid-ana',
      skill_id: 'kubernetes',
      name: 'Kubernetes',
    })
    const { wrapper } = mountModal()
    await flushPromises()

    const input = wrapper.find('input[placeholder="Add skill..."]')
    await input.setValue('Kubernetes')
    await input.trigger('keyup.enter')
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

    const input = wrapper.find('input[placeholder="Add skill..."]')
    await input.setValue('Docker')
    await input.trigger('keyup.enter')
    await flushPromises()

    expect(wrapper.text()).toContain('Could not add the skill. Try again.')
    expect((input.element as HTMLInputElement).value).toBe('Docker')
  })

  it('renders the catalog as visible clickable chips and assigns on click (#576 picker fix)', async () => {
    vi.mocked(fetchSkills).mockResolvedValue([
      { id: 'python', name: 'Python' },
      { id: 'go', name: 'Go' },
      { id: 'docker', name: 'Docker' },
    ])
    vi.mocked(addUserSkill).mockResolvedValue({
      user_id: 'uid-ana',
      skill_id: 'go',
      name: 'Go',
    })
    const { wrapper } = mountModal()
    await flushPromises()

    // Python is already assigned -> excluded; Go/Docker visible without typing.
    const labels = wrapper.text()
    expect(labels).toContain('Catalog')
    expect(labels).toContain('Go')
    expect(labels).toContain('Docker')
    expect(labels).not.toContain('+ Python')

    const goChip = wrapper.findAll('button').find(b => b.text() === '+ Go')
    expect(goChip).toBeDefined()
    await goChip!.trigger('click')
    await flushPromises()

    expect(addUserSkill).toHaveBeenCalledWith('uid-ana', 'Go')
    expect(wrapper.text()).toContain('Go')
  })

  it('filters the catalog chips by what is typed in the input', async () => {
    vi.mocked(fetchSkills).mockResolvedValue([
      { id: 'go', name: 'Go' },
      { id: 'docker', name: 'Docker' },
      { id: 'kubernetes', name: 'Kubernetes' },
    ])
    const { wrapper } = mountModal()
    await flushPromises()

    await wrapper.find('input[placeholder="Add skill..."]').setValue('dock')
    await flushPromises()

    expect(wrapper.text()).toContain('Docker')
    expect(wrapper.text()).not.toContain('Kubernetes')
  })

  it('keeps the mock-mode local chips (no API calls) for the in-memory store', async () => {
    mockState.mockMode = true
    const { wrapper } = mountModal()
    await flushPromises()

    // loadAssignedSkills is skipped in mock mode
    expect(fetchUserSkills).not.toHaveBeenCalled()

    const input = wrapper.find('input[placeholder="Add skill..."]')
    await input.setValue('Local Skill')
    await input.trigger('keyup.enter')
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
    // The modal must not close itself: the parent closes it only after a
    // successful save, so a failed PUT keeps the form open (#566 pattern).
    expect(wrapper.emitted('close')).toBeUndefined()
  })

  it('opens the floating picker on "+" and applies only the delta (#577)', async () => {
    vi.mocked(fetchSkills).mockResolvedValue([
      { id: 'python', name: 'Python' },
      { id: 'vue', name: 'Vue' },
      { id: 'go', name: 'Go' },
    ])
    vi.mocked(addUserSkill).mockResolvedValue({
      user_id: 'uid-ana',
      skill_id: 'go',
      name: 'Go',
    })
    vi.mocked(removeUserSkill).mockResolvedValue(undefined)
    const { wrapper } = mountModal()
    await flushPromises()

    await wrapper.findAll('button').find(b => b.attributes('aria-label') === 'Add skills')!.trigger('click')
    await flushPromises()

    // The picker lists the human catalog with the assignment pre-checked.
    const boxes = wrapper.findAll('input[type="checkbox"]')
    expect(boxes).toHaveLength(3)
    expect((boxes[0].element as HTMLInputElement).checked).toBe(true)
    expect((boxes[1].element as HTMLInputElement).checked).toBe(true)

    await boxes[1].setValue(false) // unlink Vue
    await boxes[2].setValue(true) // link Go
    await wrapper.findAll('button').find(b => b.text() === 'Apply')!.trigger('click')
    await flushPromises()

    expect(addUserSkill).toHaveBeenCalledTimes(1)
    expect(addUserSkill).toHaveBeenCalledWith('uid-ana', 'Go')
    expect(removeUserSkill).toHaveBeenCalledTimes(1)
    expect(removeUserSkill).toHaveBeenCalledWith('uid-ana', 'vue')
    // Assigned chips (spans): Go in, Vue out. The catalog row may offer
    // "+ Vue" again because it is no longer assigned — that is not a chip.
    const chips = wrapper.findAll('span')
    expect(chips.some(s => s.text().includes('Go') && !s.text().includes('+'))).toBe(true)
    expect(chips.some(s => s.text().includes('Vue') && !s.text().includes('+'))).toBe(false)
  })

  it('keeps the picker selection local in mock mode (no skill endpoints)', async () => {
    mockState.mockMode = true
    const { wrapper } = mountModal()
    await flushPromises()

    await wrapper.findAll('button').find(b => b.attributes('aria-label') === 'Add skills')!.trigger('click')
    await wrapper.find('input[placeholder="Type a custom skill name..."]').setValue('Rust')
    await wrapper.findAll('button').find(b => b.text() === 'Add')!.trigger('click')
    await wrapper.findAll('button').find(b => b.text() === 'Apply')!.trigger('click')
    await flushPromises()

    expect(addUserSkill).not.toHaveBeenCalled()
    expect(removeUserSkill).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Rust')
  })
})
