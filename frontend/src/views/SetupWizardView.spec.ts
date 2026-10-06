import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia } from 'pinia'
import { mountComponent } from '@/test/mount'
import SetupWizardView from '@/views/SetupWizardView.vue'
import { useUiStore } from '@/stores/uiStore'
import { useAuthStore } from '@/stores/authStore'
import { useToast } from '@/composables/useToast'
import * as setupApi from '@/api/setupApi'
import * as authApi from '@/api/authApi'
import { setApiMode } from '@/api/client'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

vi.mock('@/api/setupApi', () => ({
  getSetupStatus: vi.fn(),
  postSetupInitialize: vi.fn(),
}))

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

async function goToConfirm(wrapper: ReturnType<typeof mountComponent>['wrapper']) {
  await wrapper.find('[data-testid="setup-next"]').trigger('click')
  await wrapper.find('[data-testid="setup-project-name"]').setValue('Proyecto Demo')
  await wrapper.find('[data-testid="setup-project-summary"]').setValue('Resumen del proyecto demo')
  await wrapper.find('[data-testid="setup-next"]').trigger('click')
  await wrapper.find('[data-testid="setup-next"]').trigger('click')
}

describe('SetupWizardView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    push.mockReset()
    useToast().clearAll()
    setApiMode('mock')
    vi.mocked(authApi.loginWithCredentials).mockResolvedValue({
      id: 'u-admin',
      username: 'admin',
      role: 'ADMIN',
      permissions: ['admin'],
    })
  })

  it('walks the four steps with the default credentials and submits the payload', async () => {
    vi.mocked(setupApi.postSetupInitialize).mockResolvedValue({
      installed: true,
      adminUsername: 'admin',
      projectName: 'Proyecto Demo',
      projectId: 'p-1',
      policies: ['Prevent circular dependencies', 'Require solution summary'],
      credentials: 'created',
      apiKey: 'tasker_sk_live_test_key',
      mcpPort: 0,
    })
    const { wrapper, pinia } = mountComponent(SetupWizardView)
    setActivePinia(pinia)

    expect(wrapper.find('[data-testid="setup-step-1"]').attributes('aria-current')).toBe('step')
    const userInput = wrapper.find<HTMLInputElement>('[data-testid="setup-admin-user"]')
    const passInput = wrapper.find<HTMLInputElement>('[data-testid="setup-admin-password"]')
    expect(userInput.element.value).toBe('admin')
    expect(passInput.element.value).toBe('admin')
    expect(passInput.element.type).toBe('password')

    await wrapper.find('[data-testid="setup-password-toggle"]').trigger('click')
    expect(wrapper.find<HTMLInputElement>('[data-testid="setup-admin-password"]').element.type).toBe('text')

    await wrapper.find('[data-testid="setup-next"]').trigger('click')
    expect(wrapper.find('[data-testid="setup-step-2"]').attributes('aria-current')).toBe('step')
    await wrapper.find('[data-testid="setup-project-name"]').setValue('Proyecto Demo')
    await wrapper.find('[data-testid="setup-project-summary"]').setValue('Resumen del proyecto demo')

    await wrapper.find('[data-testid="setup-next"]').trigger('click')
    const circular = wrapper.find<HTMLInputElement>('[data-testid="setup-policy-prevent_circular_dependencies"]')
    const solution = wrapper.find<HTMLInputElement>('[data-testid="setup-policy-require_solution_summary"]')
    const human = wrapper.find<HTMLInputElement>('[data-testid="setup-policy-require_human_approval_core"]')
    expect(circular.element.checked).toBe(true)
    expect(solution.element.checked).toBe(true)
    expect(human.element.checked).toBe(false)

    await wrapper.find('[data-testid="setup-next"]').trigger('click')
    expect(wrapper.find('[data-testid="setup-summary-admin"]').text()).toBe('admin')
    expect(wrapper.find('[data-testid="setup-summary-project"]').text()).toBe('Proyecto Demo')
    expect(wrapper.find('[data-testid="setup-summary-description"]').text()).toBe('Resumen del proyecto demo')
    expect(wrapper.find('[data-testid="setup-summary-policies"]').text()).toContain('Prevent circular dependencies')
    expect(wrapper.find('[data-testid="setup-summary-custom"]').text()).toBe('None')

    await wrapper.find('[data-testid="setup-submit"]').trigger('click')
    await vi.waitFor(() =>
      expect(wrapper.find('[data-testid="setup-ai-key"]').exists()).toBe(true),
    )
    expect(wrapper.find('[data-testid="setup-ai-key"]').text()).toBe('tasker_sk_live_test_key')

    expect(setupApi.postSetupInitialize).toHaveBeenCalledTimes(1)
    expect(vi.mocked(setupApi.postSetupInitialize).mock.calls[0][0]).toEqual({
      admin_user: 'admin',
      admin_password: 'admin',
      project_name: 'Proyecto Demo',
      project_summary: 'Resumen del proyecto demo',
      policies: ['prevent_circular_dependencies', 'require_solution_summary'],
      custom_policies: [],
      api_key: '',
      mcp_port: 0,
      confirm_wipe: true,
    })
    expect(useUiStore(pinia).isInstalled).toBe(true)
    expect(localStorage.getItem('socialseed-api-mode')).toBe('real')
    // notas.md #3: the wizard logs the admin in so the onboarding
    // notifications are fetched as soon as /board opens.
    expect(authApi.loginWithCredentials).toHaveBeenCalledWith('admin', 'admin')
    expect(useAuthStore(pinia).user?.username).toBe('admin')
    expect(push).not.toHaveBeenCalled()

    await wrapper.find('[data-testid="setup-finish"]').trigger('click')
    expect(push).toHaveBeenCalledWith('/board')
  })

  it('sends the configured MCP port and shows it in the credentials panel', async () => {
    vi.mocked(setupApi.postSetupInitialize).mockResolvedValue({
      installed: true,
      adminUsername: 'admin',
      projectName: 'Proyecto Demo',
      projectId: 'p-1',
      policies: [],
      credentials: 'created',
      apiKey: 'tasker_sk_live_port_key',
      mcpPort: 8888,
    })
    const { wrapper } = mountComponent(SetupWizardView)

    await goToConfirm(wrapper)
    await wrapper.find<HTMLInputElement>('[data-testid="setup-mcp-port"]').setValue('8888')
    await wrapper.find('[data-testid="setup-submit"]').trigger('click')
    await vi.waitFor(() =>
      expect(wrapper.find('[data-testid="setup-ai-key"]').exists()).toBe(true),
    )

    expect(vi.mocked(setupApi.postSetupInitialize).mock.calls[0][0].mcp_port).toBe(8888)
    expect(wrapper.find('[data-testid="setup-mcp-snippet"]').text()).toContain(':8888/mcp')
    expect(wrapper.find('[data-testid="setup-finish"]').exists()).toBe(true)
  })

  it('completes the wizard even when the auto-login fails', async () => {
    vi.mocked(setupApi.postSetupInitialize).mockResolvedValue({
      installed: true,
      adminUsername: 'admin',
      projectName: 'Proyecto Demo',
      projectId: 'p-1',
      policies: [],
      credentials: 'created',
      apiKey: 'tasker_sk_live_test_key',
      mcpPort: 0,
    })
    vi.mocked(authApi.loginWithCredentials).mockRejectedValue(new Error('nope'))
    const { wrapper, pinia } = mountComponent(SetupWizardView)
    setActivePinia(pinia)

    await goToConfirm(wrapper)
    await wrapper.find('[data-testid="setup-submit"]').trigger('click')
    await vi.waitFor(() =>
      expect(wrapper.find('[data-testid="setup-ai-key"]').exists()).toBe(true),
    )

    const auth = useAuthStore(pinia)
    expect(auth.user).toBeNull()
    expect(auth.error).toBeNull()
  })

  it('adds and removes custom policies', async () => {
    const { wrapper } = mountComponent(SetupWizardView)
    await wrapper.find('[data-testid="setup-next"]').trigger('click')
    await wrapper.find('[data-testid="setup-project-name"]').setValue('Proyecto Demo')
    await wrapper.find('[data-testid="setup-project-summary"]').setValue('Resumen')
    await wrapper.find('[data-testid="setup-next"]').trigger('click')

    expect(wrapper.find('[data-testid="setup-custom-item"]').exists()).toBe(false)
    await wrapper.find('[data-testid="setup-custom-input"]').setValue('Regla custom A')
    await wrapper.find('[data-testid="setup-add-policy"]').trigger('click')
    await wrapper.find('[data-testid="setup-custom-input"]').setValue('Regla custom B')
    await wrapper.find('[data-testid="setup-custom-input"]').trigger('keyup.enter')

    const items = wrapper.findAll('[data-testid="setup-custom-item"]')
    expect(items).toHaveLength(2)
    expect(items[0].text()).toBe('Regla custom A')

    await wrapper.findAll('[data-testid="setup-remove-policy"]')[0].trigger('click')
    expect(wrapper.findAll('[data-testid="setup-custom-item"]')).toHaveLength(1)
    expect(wrapper.find('[data-testid="setup-custom-item"]').text()).toBe('Regla custom B')
  })

  it('blocks navigation while a required field is empty', async () => {
    const { wrapper } = mountComponent(SetupWizardView)
    const next = wrapper.find('[data-testid="setup-next"]')
    expect(next.attributes('disabled')).toBeUndefined()

    await wrapper.find<HTMLInputElement>('[data-testid="setup-admin-user"]').setValue('   ')
    expect(next.attributes('disabled')).toBeDefined()

    await wrapper.find<HTMLInputElement>('[data-testid="setup-admin-user"]').setValue('admin')
    expect(next.attributes('disabled')).toBeUndefined()

    await next.trigger('click')
    const projectNext = wrapper.find('[data-testid="setup-next"]')
    expect(projectNext.attributes('disabled')).toBeDefined()
    await wrapper.find('[data-testid="setup-project-name"]').setValue('Proyecto Demo')
    expect(projectNext.attributes('disabled')).toBeDefined()
    await wrapper.find('[data-testid="setup-project-summary"]').setValue('Resumen')
    expect(projectNext.attributes('disabled')).toBeUndefined()
  })

  it('redirects to /board with a toast when the system is already installed (403)', async () => {
    vi.mocked(setupApi.postSetupInitialize).mockRejectedValue({ status: 403 })
    const { wrapper, pinia } = mountComponent(SetupWizardView)
    setActivePinia(pinia)

    await goToConfirm(wrapper)
    await wrapper.find('[data-testid="setup-submit"]').trigger('click')
    await vi.waitFor(() => expect(push).toHaveBeenCalledWith('/board'))

    const errors = useToast().toasts.value.filter((toast) => toast.type === 'error')
    expect(errors).toHaveLength(1)
    expect(useUiStore(pinia).isInstalled).toBe(true)
    expect(localStorage.getItem('socialseed-api-mode')).toBe('real')
  })

  it('keeps the wizard open with an error toast on unexpected failures', async () => {
    vi.mocked(setupApi.postSetupInitialize).mockRejectedValue({ status: 500 })
    const { wrapper } = mountComponent(SetupWizardView)

    await goToConfirm(wrapper)
    await wrapper.find('[data-testid="setup-submit"]').trigger('click')
    await vi.waitFor(() =>
      expect(useToast().toasts.value.some((toast) => toast.type === 'error')).toBe(true),
    )

    expect(push).not.toHaveBeenCalled()
    expect(wrapper.find('[data-testid="setup-submit"]').exists()).toBe(true)
  })
})
