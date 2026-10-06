import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mountComponent } from '@/test/mount'
import LoginScreen from '@/components/auth/LoginScreen.vue'
import { setApiMode } from '@/api/client'
import * as authApi from '@/api/authApi'
import type { SessionUser } from '@/api/authSession'

vi.mock('@/api/authApi', () => ({
  login: vi.fn(),
  loginWithCredentials: vi.fn(),
  restoreSession: vi.fn(),
  logout: vi.fn(),
  exchange: vi.fn(),
  startOAuth: vi.fn(),
  refresh: vi.fn(),
  fetchMe: vi.fn(),
}))

const ADMIN_USER: SessionUser = {
  id: 'u-admin',
  username: 'admin',
  role: 'ADMIN',
  permissions: ['admin', 'create:issue', 'delete:issue', 'read:context', 'read:impact'],
}

describe('LoginScreen', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setApiMode('mock')
  })

  it('shows username/password inputs by default, not the API key field', () => {
    const { wrapper } = mountComponent(LoginScreen)
    expect(wrapper.find('[data-testid="login-username"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="login-password"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="login-apikey"]').exists()).toBe(false)
  })

  it('disables submit until username and password are filled', async () => {
    const { wrapper } = mountComponent(LoginScreen)
    const submit = wrapper.find('[data-testid="login-submit"]')
    expect(submit.attributes('disabled')).toBeDefined()

    await wrapper.find('[data-testid="login-username"]').setValue('admin')
    expect(submit.attributes('disabled')).toBeDefined()

    await wrapper.find('[data-testid="login-password"]').setValue('admin')
    expect(submit.attributes('disabled')).toBeUndefined()
  })

  it('logs in with username/password and emits loggedIn', async () => {
    vi.mocked(authApi.loginWithCredentials).mockResolvedValue(ADMIN_USER)
    const { wrapper } = mountComponent(LoginScreen)

    await wrapper.find('[data-testid="login-username"]').setValue('admin')
    await wrapper.find('[data-testid="login-password"]').setValue('admin')
    await wrapper.find('form').trigger('submit')

    expect(authApi.loginWithCredentials).toHaveBeenCalledWith('admin', 'admin')
    expect(authApi.login).not.toHaveBeenCalled()
    await vi.waitFor(() => {
      expect(wrapper.emitted('loggedIn')).toHaveLength(1)
    })
  })

  it('switches to API key mode, logs in with the key, and switches back', async () => {
    vi.mocked(authApi.login).mockResolvedValue(ADMIN_USER)
    const { wrapper } = mountComponent(LoginScreen)

    await wrapper.find('[data-testid="login-toggle-apikey"]').trigger('click')
    expect(wrapper.find('[data-testid="login-apikey"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="login-password"]').exists()).toBe(false)

    await wrapper.find('[data-testid="login-apikey"]').setValue('tasker_sk_live_test')
    await wrapper.find('form').trigger('submit')
    expect(authApi.login).toHaveBeenCalledWith('tasker_sk_live_test')
    expect(authApi.loginWithCredentials).not.toHaveBeenCalled()
    await vi.waitFor(() => {
      expect(wrapper.emitted('loggedIn')).toHaveLength(1)
    })

    await wrapper.find('[data-testid="login-toggle-credentials"]').trigger('click')
    expect(wrapper.find('[data-testid="login-password"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="login-apikey"]').exists()).toBe(false)
  })

  it('surfaces the store error when credentials are rejected', async () => {
    vi.mocked(authApi.loginWithCredentials).mockRejectedValue(new Error('401'))
    const { wrapper } = mountComponent(LoginScreen)

    await wrapper.find('[data-testid="login-username"]').setValue('admin')
    await wrapper.find('[data-testid="login-password"]').setValue('wrong')
    await wrapper.find('form').trigger('submit').catch(() => {})

    await vi.waitFor(() => {
      expect(wrapper.find('[data-testid="login-error"]').exists()).toBe(true)
    })
    expect(wrapper.emitted('loggedIn')).toBeUndefined()
  })
})
