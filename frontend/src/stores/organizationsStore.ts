import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/api/organizationsApi'
import { useUiStore } from '@/stores/uiStore'
import type {
  Organization,
  OrganizationCreateRequest,
  EnterpriseRole,
  EnterpriseAccount,
} from '@/types/organizations'

const LS_ORG = 'currentOrg'
const LS_WORKSPACE = 'currentWorkspace'
const LS_ACTIVE_ROLE = 'activeEnterpriseRole'

export const useOrganizationsStore = defineStore('organizations', () => {
  const organizations = ref<Organization[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const currentOrgId = ref(localStorage.getItem(LS_ORG) || '')
  const currentWorkspaceId = ref(localStorage.getItem(LS_WORKSPACE) || '')
  const activeRole = ref<EnterpriseRole>(
    (localStorage.getItem(LS_ACTIVE_ROLE) as EnterpriseRole) || 'ENTERPRISE_ADMIN',
  )
  const loadedOnce = ref(false)

  const currentOrg = computed(
    () => organizations.value.find((o) => o.id === currentOrgId.value) || null,
  )

  const currentWorkspace = computed(
    () => currentOrg.value?.workspaces.find((w) => w.id === currentWorkspaceId.value) || null,
  )

  const availableWorkspaces = computed(() => currentOrg.value?.workspaces || [])

  const isAuditor = computed(() => activeRole.value === 'AUDITOR')

  const canEdit = computed(() => activeRole.value !== 'AUDITOR')

  const canManage = computed(
    () => activeRole.value === 'ENTERPRISE_ADMIN' || activeRole.value === 'SECURITY_MANAGER',
  )

  const quotaUsage = computed(() => {
    const org = currentOrg.value
    if (!org) return { compute: 0, storage: 0, tokens: 0 }
    return {
      compute: Math.round((org.quota.computeUsed / org.quota.computeLimit) * 100),
      storage: Math.round((org.quota.storageUsedGb / org.quota.storageLimitGb) * 100),
      tokens: Math.round((org.quota.tokenUsed / org.quota.tokenLimit) * 100),
    }
  })

  function syncProjectToWorkspace() {
    const ws = currentWorkspace.value
    const ui = useUiStore()
    if (!ws) return
    if (ws.projectIds.length && !ws.projectIds.includes(ui.currentProject)) {
      ui.setProject(ws.projectIds[0])
    }
  }

  function ensureSelection() {
    if (!organizations.value.length) return
    if (!currentOrgId.value || !organizations.value.some((o) => o.id === currentOrgId.value)) {
      setOrg(organizations.value[0].id)
    }
    const org = currentOrg.value
    if (org && (!currentWorkspaceId.value || !org.workspaces.some((w) => w.id === currentWorkspaceId.value))) {
      setWorkspace(org.workspaces[0]?.id || '')
    }
    const orgRole = currentOrg.value?.defaultRole
    if (orgRole && !localStorage.getItem(LS_ACTIVE_ROLE)) {
      activeRole.value = orgRole
    }
    syncProjectToWorkspace()
  }

  async function fetchOrganizations(force = false) {
    if (loadedOnce.value && !force) return
    loading.value = true
    error.value = null
    try {
      organizations.value = await api.fetchOrganizations()
      loadedOnce.value = true
      ensureSelection()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load organizations'
      organizations.value = []
    } finally {
      loading.value = false
    }
  }

  async function createOrganization(body: OrganizationCreateRequest): Promise<Organization | null> {
    if (!canManage.value) {
      error.value = 'Not authorized'
      return null
    }
    try {
      const created = await api.createOrganization(body)
      organizations.value.push(created)
      return created
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create organization'
      return null
    }
  }

  async function updateOrganization(
    id: string,
    body: Partial<Organization>,
  ): Promise<Organization | null> {
    if (!canEdit.value) {
      error.value = 'Read-only role'
      return null
    }
    try {
      const updated = await api.updateOrganization(id, body)
      const idx = organizations.value.findIndex((o) => o.id === id)
      if (idx >= 0) organizations.value[idx] = updated
      return updated
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update organization'
      return null
    }
  }

  function setOrg(id: string) {
    currentOrgId.value = id
    localStorage.setItem(LS_ORG, id)
    const org = organizations.value.find((o) => o.id === id)
    if (org) {
      if (!org.workspaces.some((w) => w.id === currentWorkspaceId.value)) {
        setWorkspace(org.workspaces[0]?.id || '')
      }
      activeRole.value = org.defaultRole
      localStorage.setItem(LS_ACTIVE_ROLE, org.defaultRole)
      syncProjectToWorkspace()
    }
  }

  function setWorkspace(id: string) {
    currentWorkspaceId.value = id
    localStorage.setItem(LS_WORKSPACE, id)
    syncProjectToWorkspace()
  }

  function setActiveRole(role: EnterpriseRole) {
    activeRole.value = role
    localStorage.setItem(LS_ACTIVE_ROLE, role)
  }

  function upsertAccount(orgId: string, account: EnterpriseAccount) {
    const org = organizations.value.find((o) => o.id === orgId)
    if (!org || !canManage.value) return
    const idx = org.accounts.findIndex((a) => a.id === account.id)
    if (idx >= 0) org.accounts[idx] = account
    else org.accounts.push(account)
  }

  function removeAccount(orgId: string, accountId: string) {
    const org = organizations.value.find((o) => o.id === orgId)
    if (!org || !canManage.value) return
    org.accounts = org.accounts.filter((a) => a.id !== accountId)
  }

  return {
    organizations,
    loading,
    error,
    currentOrgId,
    currentWorkspaceId,
    activeRole,
    loadedOnce,
    currentOrg,
    currentWorkspace,
    availableWorkspaces,
    isAuditor,
    canEdit,
    canManage,
    quotaUsage,
    fetchOrganizations,
    createOrganization,
    updateOrganization,
    setOrg,
    setWorkspace,
    setActiveRole,
    upsertAccount,
    removeAccount,
  }
})
