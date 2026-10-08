import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, type VueWrapper } from '@vue/test-utils'
import { mountComponent } from '@/test/mount'
import UsersView from '@/views/UsersView.vue'
import { useUsersStore } from '@/stores/usersStore'
import * as usersApi from '@/api/usersApi'
import * as issuesApi from '@/api/issuesApi'
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
