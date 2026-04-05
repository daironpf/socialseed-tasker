import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/api/issuesApi'
import type { Issue, IssueCreateRequest, IssueUpdateRequest, IssueStatus } from '@/types'

export const useIssuesStore = defineStore('issues', () => {
  const issues = ref<Issue[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const openIssuesCount = computed(() =>
    issues.value.filter((i) => i.status !== 'CLOSED').length,
  )

  const blockedIssuesCount = computed(() =>
    issues.value.filter((i) => i.status === 'BLOCKED' || i.status === 'OPEN').length,
  )

  function issuesByStatus(status: IssueStatus) {
    return issues.value.filter((i) => i.status === status)
  }

  function issuesByPriority(priority: string) {
    return issues.value.filter((i) => i.priority === priority)
  }

  function issuesByComponent(componentId: string) {
    return issues.value.filter((i) => i.component_id === componentId)
  }

  async function fetchIssues(filters?: { status?: string; component?: string }) {
    loading.value = true
    error.value = null
    try {
      issues.value = await api.fetchIssues(1, 100, filters?.status, filters?.component)
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  async function fetchIssue(id: string): Promise<Issue | null> {
    try {
      return await api.fetchIssue(id)
    } catch (e) {
      error.value = (e as Error).message
      return null
    }
  }

  async function createIssue(body: IssueCreateRequest): Promise<Issue | null> {
    try {
      const issue = await api.createIssue(body)
      issues.value.unshift(issue)
      return issue
    } catch (e) {
      error.value = (e as Error).message
      return null
    }
  }

  async function updateIssue(id: string, body: IssueUpdateRequest): Promise<Issue | null> {
    try {
      const updated = await api.updateIssue(id, body)
      const idx = issues.value.findIndex((i) => i.id === id)
      if (idx !== -1) issues.value[idx] = updated
      return updated
    } catch (e) {
      error.value = (e as Error).message
      return null
    }
  }

  async function deleteIssue(id: string): Promise<boolean> {
    try {
      await api.deleteIssue(id)
      issues.value = issues.value.filter((i) => i.id !== id)
      return true
    } catch (e) {
      error.value = (e as Error).message
      return false
    }
  }

  async function closeIssue(id: string): Promise<Issue | null> {
    try {
      const updated = await api.closeIssue(id)
      const idx = issues.value.findIndex((i) => i.id === id)
      if (idx !== -1) issues.value[idx] = updated
      return updated
    } catch (e) {
      error.value = (e as Error).message
      return null
    }
  }

  async function fetchBlockedIssues() {
    loading.value = true
    error.value = null
    try {
      const blocked = await api.fetchBlockedIssues()
      blocked.forEach((b) => {
        const idx = issues.value.findIndex((i) => i.id === b.id)
        if (idx !== -1) {
          issues.value[idx] = b
        } else {
          issues.value.push(b)
        }
      })
    } catch (e) {
      error.value = (e as Error).message
    } finally {
      loading.value = false
    }
  }

  return {
    issues,
    loading,
    error,
    openIssuesCount,
    blockedIssuesCount,
    issuesByStatus,
    issuesByPriority,
    issuesByComponent,
    fetchIssues,
    fetchIssue,
    createIssue,
    updateIssue,
    deleteIssue,
    closeIssue,
    fetchBlockedIssues,
  }
})
