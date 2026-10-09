import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { flushPromises, type VueWrapper } from '@vue/test-utils'
import { mountComponent } from '@/test/mount'
import UsersView from '@/views/UsersView.vue'
import CreateUserModal from '@/components/users/CreateUserModal.vue'
import { useUsersStore } from '@/stores/usersStore'
import * as usersApi from '@/api/usersApi'
import * as issuesApi from '@/api/issuesApi'
import { createAgentProfile, fetchAgentProfiles } from '@/api/agentProfilesApi'
import { apiMode } from '@/api/client'
import type { User } from '@/types'

const { toastSuccess, toastError } = vi.hoisted(() => ({
  toastSuccess: vi.fn(),
  toastError: vi.fn(),
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({
    success: toastSuccess,
    error: toastError,
    warning: vi.fn(),
    info: vi.fn(),
  }),
}))

vi.mock('@/api/usersApi', () => ({
  fetchUsers: vi.fn(),
  updateUser: vi.fn(),
  createUser: vi.fn(),
  deleteUser: vi.fn(),
}))

vi.mock('@/api/issuesApi', () => ({
  fetchIssues: vi.fn(),
  fetchIssue: vi.fn(),
}))

  vi.mock('@/api/agentProfilesApi', () => ({
    fetchAgentProfiles: vi.fn(),
    createAgentProfile: vi.fn(),
    updateAgentProfile: vi.fn(),
  }))

function makeHuman(id: string, username: string): User {
  return {
    id,
    username,
    email: `${username}@socialseed.com`,
    role: 'VIEWER',
    type: 'human',
    avatar: '🦊',
    skills: ['python', 'vue'],
    issues_assigned: 0,
    issues_created: 0,
    last_active: '2026-10-01T08:00:00Z',
    is_active: true,
  }
}

async function mountView() {
  const mounted = mountComponent(UsersView)
  await flushPromises()
  await mounted.wrapper.vm.$nextTick()
  return mounted.wrapper
}

async function openEditAndSave(wrapper: VueWrapper, username: string) {
  await wrapper.findAll('button[aria-label="Edit user"]')[0].trigger('click')
  await wrapper.vm.$nextTick()
  await wrapper.find('input[type="text"]').setValue(username)
  const save = wrapper.findAll('button').find(b => b.text() === 'Save changes')
  expect(save).toBeTruthy()
  await save!.trigger('click')
  await flushPromises()
}

describe('UsersView edit flow (issue #560)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(usersApi.fetchUsers).mockResolvedValue([
      makeHuman('uid-ana', 'ana'),
      makeHuman('uid-bea', 'bea'),
    ])
    vi.mocked(usersApi.deleteUser).mockResolvedValue()
    vi.mocked(issuesApi.fetchIssues).mockResolvedValue({
      items: [],
      pagination: { page: 1, limit: 200, total: 0, has_next: false, has_prev: false },
    })
  })

  it('keeps badge, avatar and buttons on the card after saving an edit', async () => {
    vi.mocked(usersApi.updateUser).mockResolvedValue({
      ...makeHuman('uid-ana', 'ana-g'),
      username: 'ana-g',
      role: 'ADMIN',
    })

    const wrapper = await mountView()

    expect(wrapper.text()).toContain('Human')
    expect(wrapper.text()).toContain('🦊')

    await openEditAndSave(wrapper, 'ana-g')

    expect(usersApi.updateUser).toHaveBeenCalledWith(
      'uid-ana',
      expect.objectContaining({ username: 'ana-g', type: 'human', avatar: '🦊' }),
    )
    const store = useUsersStore()
    expect(store.users[0].username).toBe('ana-g')
    expect(store.users[0].type).toBe('human')
    expect(toastSuccess).toHaveBeenCalledWith('User updated successfully')

    // The regression from #556: a raw response must not strip the card.
    expect(wrapper.text()).toContain('ana-g')
    expect(wrapper.text()).toContain('Human')
    expect(wrapper.text()).toContain('🦊')
    expect(wrapper.find('button[aria-label="Edit user"]').exists()).toBe(true)
    expect(wrapper.find('button[aria-label="Delete user"]').exists()).toBe(true)
    // both cards still render the human badge (a raw response flips them to "AI")
    const badges = wrapper.findAll('span.rounded-full').filter(b => b.text() === 'Human')
    expect(badges).toHaveLength(2)
  })

  it('translates a 409 conflict into the username toast', async () => {
    vi.mocked(usersApi.updateUser).mockRejectedValue(
      Object.assign(new Error('username already exists'), { status: 409 }),
    )

    const wrapper = await mountView()
    await openEditAndSave(wrapper, 'otro')

    expect(toastError).toHaveBeenCalledWith('That username is already taken')
    expect(toastSuccess).not.toHaveBeenCalled()
    expect(useUsersStore().users[0].username).toBe('ana') // untouched on failure
  })

  it('shows the backend detail when the backend answers 422', async () => {
    vi.mocked(usersApi.updateUser).mockRejectedValue(
      Object.assign(new Error("invalid role: 'lead' (expected one of ADMIN, DEVELOPER, VIEWER)"), {
        status: 422,
      }),
    )

    const wrapper = await mountView()
    await openEditAndSave(wrapper, 'ana')

    expect(toastError).toHaveBeenCalledWith(
      "Error: invalid role: 'lead' (expected one of ADMIN, DEVELOPER, VIEWER)",
    )
    expect(toastSuccess).not.toHaveBeenCalled()
  })
})

describe('UsersView delete flow (issue #562)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(usersApi.fetchUsers).mockResolvedValue([
      makeHuman('uid-ana', 'ana'),
      makeHuman('uid-bea', 'bea'),
    ])
    vi.mocked(usersApi.deleteUser).mockResolvedValue()
    vi.mocked(issuesApi.fetchIssues).mockResolvedValue({
      items: [],
      pagination: { page: 1, limit: 200, total: 0, has_next: false, has_prev: false },
    })
  })

  it('shows the backend detail when the delete fails', async () => {
    vi.mocked(usersApi.deleteUser).mockRejectedValue(
      Object.assign(new Error('Cannot delete the last user'), { status: 409 }),
    )

    const wrapper = await mountView()
    await wrapper.findAll('button[aria-label="Delete user"]')[0].trigger('click')
    await flushPromises()

    expect(toastError).toHaveBeenCalledWith('Error: Cannot delete the last user')
    expect(useUsersStore().users).toHaveLength(2) // untouched on failure
  })

  it('removes the card when the delete succeeds', async () => {
    const wrapper = await mountView()
    await wrapper.findAll('button[aria-label="Delete user"]')[0].trigger('click')
    await flushPromises()

    expect(usersApi.deleteUser).toHaveBeenCalledWith('uid-ana')
    expect(useUsersStore().users).toHaveLength(1)
    expect(toastError).not.toHaveBeenCalled()
  })
})

describe('UsersView create flow (issue #563)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(usersApi.fetchUsers).mockResolvedValue([makeHuman('uid-ana', 'ana')])
    vi.mocked(usersApi.deleteUser).mockResolvedValue()
    vi.mocked(issuesApi.fetchIssues).mockResolvedValue({
      items: [],
      pagination: { page: 1, limit: 200, total: 0, has_next: false, has_prev: false },
    })
  })

  async function emitSave(wrapper: VueWrapper) {
    const modal = wrapper.findComponent(CreateUserModal)
    ;(modal.vm as unknown as { $emit: (e: string, d: unknown) => void }).$emit('save', {
      username: 'boss',
      email: 'boss@x.com',
      role: 'admin',
      type: 'human',
      avatar: '🦊',
      skills: [],
    })
    await flushPromises()
  }

  it('shows the one-time password dialog and clears it on acknowledge', async () => {
    vi.mocked(usersApi.createUser).mockResolvedValue({
      user: { ...makeHuman('uid-boss', 'boss'), role: 'ADMIN' },
      temporaryPassword: 'temp-abc123',
    })

    const wrapper = await mountView()
    await emitSave(wrapper)

    expect(usersApi.createUser).toHaveBeenCalledWith(
      expect.objectContaining({ username: 'boss' }),
    )
    const code = wrapper.find('[data-testid="temp-password"]')
    expect(code.exists()).toBe(true)
    expect(code.text()).toBe('temp-abc123')
    expect(wrapper.text()).toContain('Shown only once. Copy it now and share it securely with the user.')

    // the card is normalized: the plaintext never lands on the user object
    const store = useUsersStore()
    const created = store.users.find(u => u.id === 'uid-boss')
    expect(created).toBeTruthy()
    expect(created).not.toHaveProperty('temporary_password')

    await wrapper.find('[data-testid="temp-password-ack"]').trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-testid="temp-password"]').exists()).toBe(false)
  })

  it('does not open the dialog when the backend sends no temporary password', async () => {
    vi.mocked(usersApi.createUser).mockResolvedValue({
      user: makeHuman('uid-boss', 'boss'),
      temporaryPassword: null,
    })

    const wrapper = await mountView()
    await emitSave(wrapper)

    expect(wrapper.find('[data-testid="temp-password"]').exists()).toBe(false)
    expect(useUsersStore().users.some(u => u.id === 'uid-boss')).toBe(true)
  })
})

describe('UsersView create agent flow (issue #566)', () => {
  let previousMode: typeof apiMode.value

  beforeEach(() => {
    vi.clearAllMocks()
    previousMode = apiMode.value
    apiMode.value = 'real'
    vi.mocked(usersApi.fetchUsers).mockResolvedValue([makeHuman('uid-ana', 'ana')])
    vi.mocked(fetchAgentProfiles).mockResolvedValue([])
    vi.mocked(issuesApi.fetchIssues).mockResolvedValue({
      items: [],
      pagination: { page: 1, limit: 200, total: 0, has_next: false, has_prev: false },
    })
  })

  afterEach(() => {
    apiMode.value = previousMode
  })

  async function openCreateModal(wrapper: VueWrapper) {
    const openButton = wrapper.findAll('button').find(b => b.text() === '+ New User')
    expect(openButton).toBeTruthy()
    await openButton!.trigger('click')
    await wrapper.vm.$nextTick()
    expect(wrapper.findComponent(CreateUserModal).props('show')).toBe(true)
  }

  async function emitAgentSave(wrapper: VueWrapper) {
    const modal = wrapper.findComponent(CreateUserModal)
    ;(modal.vm as unknown as { $emit: (e: string, d: unknown) => void }).$emit('save', {
      username: 'bot-qa',
      email: 'bot@socialseed.com',
      role: 'developer',
      type: 'agent',
      avatar: '🤖',
      skills: ['Testing'],
      model: 'gpt-4o',
      specialization: 'testing',
      system_prompt: 'You are a QA bot.',
    })
    return flushPromises()
  }

  it('routes the agent tab to POST /agents/profiles without the temporary-password dialog', async () => {
    vi.mocked(createAgentProfile).mockResolvedValue({
      ...makeHuman('pg-agent-1', 'bot-qa'),
      type: 'agent',
      role: 'ai-agent',
      model: 'gpt-4o',
      specialization: 'testing',
      avatar: '🤖',
    })

    const wrapper = await mountView()
    await openCreateModal(wrapper)
    await emitAgentSave(wrapper)

    expect(createAgentProfile).toHaveBeenCalledWith({
      username: 'bot-qa',
      email: 'bot@socialseed.com',
      avatar: '🤖',
      model: 'gpt-4o',
      specialization: 'testing',
      system_prompt: 'You are a QA bot.',
      skills: ['Testing'],
    })
    expect(usersApi.createUser).not.toHaveBeenCalled()

    const store = useUsersStore()
    const card = store.users.find(u => u.id === 'pg-agent-1')
    expect(card).toBeTruthy()
    expect(card).toMatchObject({ type: 'agent', role: 'ai-agent', model: 'gpt-4o' })
    expect(wrapper.find('[data-testid="temp-password"]').exists()).toBe(false)

    // modal closes only on success (#566)
    expect(wrapper.findComponent(CreateUserModal).props('show')).toBe(false)
  })

  it('keeps the modal open and toasts the backend detail on a 409 duplicate', async () => {
    vi.mocked(createAgentProfile).mockRejectedValue(
      Object.assign(new Error('username already exists'), { status: 409 }),
    )

    const wrapper = await mountView()
    await openCreateModal(wrapper)
    await emitAgentSave(wrapper)

    expect(toastError).toHaveBeenCalledWith('That username is already taken')
    expect(wrapper.findComponent(CreateUserModal).props('show')).toBe(true) // stays open (#566)
    expect(useUsersStore().users.some(u => u.type === 'agent')).toBe(false)
  })

  it('keeps humans on createUser and agents on createAgent (branch by type)', async () => {
    vi.mocked(usersApi.createUser).mockResolvedValue({
      user: makeHuman('uid-new', 'nuevo'),
      temporaryPassword: null,
    })
    vi.mocked(createAgentProfile).mockResolvedValue({
      ...makeHuman('pg-agent-1', 'bot-qa'),
      type: 'agent',
      role: 'ai-agent',
    })

    const wrapper = await mountView()
    await openCreateModal(wrapper)
    const modal = wrapper.findComponent(CreateUserModal)
    const emit = (data: unknown) =>
      (modal.vm as unknown as { $emit: (e: string, d: unknown) => void }).$emit('save', data)

    emit({ username: 'nuevo', email: 'n@x.com', role: 'viewer', type: 'human', avatar: '🦊', skills: [] })
    await flushPromises()
    expect(usersApi.createUser).toHaveBeenCalledTimes(1)
    expect(createAgentProfile).not.toHaveBeenCalled()

    emit({ username: 'bot-qa', email: 'b@x.com', role: 'developer', type: 'agent', avatar: '🤖', skills: [], model: 'gpt-4o' })
    await flushPromises()
    expect(createAgentProfile).toHaveBeenCalledTimes(1)
    expect(usersApi.createUser).toHaveBeenCalledTimes(1) // still just the human
  })
})
