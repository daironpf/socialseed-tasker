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

function chipSpans(wrapper: ReturnType<typeof mountModal>['wrapper']) {
  return wrapper.findAll('span').filter(s => !s.text().includes('+'))
}

describe('EditUserModal — skills stay local until Save changes (#576 follow-up)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockState.mockMode = false
  })

  it('renders the skills from the user prop without requesting them', async () => {
    const { wrapper } = mountModal()
    await flushPromises()

    expect(fetchUserSkills).not.toHaveBeenCalled()
    const text = wrapper.text()
    expect(text).toContain('Python')
    expect(text).toContain('Vue')
  })

  it('adds a skill instantly on Enter without any API call', async () => {
    const { wrapper } = mountModal()
    await flushPromises()

    const input = wrapper.find('input[placeholder="Add skill..."]')
    await input.setValue('Kubernetes')
    await input.trigger('keyup.enter')

    // No flushPromises on purpose: the chip must be there right away.
    expect(wrapper.text()).toContain('Kubernetes')
    expect((input.element as HTMLInputElement).value).toBe('')
    expect(addUserSkill).not.toHaveBeenCalled()
    expect(removeUserSkill).not.toHaveBeenCalled()
    expect(fetchUserSkills).not.toHaveBeenCalled()
    expect(resetCatalogsCache).not.toHaveBeenCalled()
  })

  it('removes a chip instantly on × without any API call', async () => {
    const { wrapper } = mountModal()
    await flushPromises()

    const vueChip = wrapper.findAll('span').find(s => s.text().includes('Vue'))
    await vueChip!.find('button').trigger('click')

    expect(wrapper.text()).not.toContain('Vue')
    expect(removeUserSkill).not.toHaveBeenCalled()
    expect(fetchUserSkills).not.toHaveBeenCalled()
  })

  it('ignores a duplicate skill regardless of case', async () => {
    const { wrapper } = mountModal()
    await flushPromises()

    const input = wrapper.find('input[placeholder="Add skill..."]')
    await input.setValue('python')
    await input.trigger('keyup.enter')
    await flushPromises()

    const pythonChips = wrapper.findAll('span').filter(s => s.text().includes('Python'))
    expect(pythonChips).toHaveLength(1)
    expect(addUserSkill).not.toHaveBeenCalled()
  })

  it('assigns from the catalog chips locally (#576 picker fix)', async () => {
    vi.mocked(fetchSkills).mockResolvedValue([
      { id: 'python', name: 'Python' },
      { id: 'go', name: 'Go' },
      { id: 'docker', name: 'Docker' },
    ])
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

    expect(wrapper.text()).toContain('Go')
    expect(addUserSkill).not.toHaveBeenCalled()
    expect(resetCatalogsCache).not.toHaveBeenCalled()
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

    // loadAssignedSkills is gone: nothing requests the skills in mock mode.
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

  it('emits save with the form data including locally added skills', async () => {
    const { wrapper } = mountModal()
    await flushPromises()

    const input = wrapper.find('input[placeholder="Add skill..."]')
    await input.setValue('Kubernetes')
    await input.trigger('keyup.enter')

    await wrapper.findAll('button').find(b => b.text() === 'Save changes')!.trigger('click')

    const saveEvents = wrapper.emitted('save')!
    expect(saveEvents).toHaveLength(1)
    expect(saveEvents[0][0]).toMatchObject({
      id: 'uid-ana',
      username: 'ana',
      skills: ['Python', 'Vue', 'Kubernetes'],
    })
    // Saving invalidates the catalog cache: the PUT upserts catalog rows.
    expect(resetCatalogsCache).toHaveBeenCalledTimes(1)
    // Still no per-skill endpoints: everything went through the save payload.
    expect(addUserSkill).not.toHaveBeenCalled()
    expect(removeUserSkill).not.toHaveBeenCalled()
    // The modal must not close itself: the parent hides it on save and
    // reopens the draft if the PUT fails (#566 pattern).
    expect(wrapper.emitted('close')).toBeUndefined()
  })

  it('applies the floating picker selection locally (#577)', async () => {
    vi.mocked(fetchSkills).mockResolvedValue([
      { id: 'python', name: 'Python' },
      { id: 'vue', name: 'Vue' },
      { id: 'go', name: 'Go' },
    ])
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

    expect(addUserSkill).not.toHaveBeenCalled()
    expect(removeUserSkill).not.toHaveBeenCalled()
    // Assigned chips (spans): Go in, Vue out. The catalog row may offer
    // "+ Vue" again because it is no longer assigned — that is not a chip.
    const chips = chipSpans(wrapper)
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
