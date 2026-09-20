import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { CodeNode, CodeEdge, CodeStructureData } from '@/types/codeGraph'

const MOCK_CODE_NODES: CodeNode[] = [
  { id: 'code-001', name: 'server.py', type: 'File', filePath: 'mock-api/server.py', language: 'Python', startLine: 1, endLine: 350, componentId: null },
  { id: 'code-002', name: 'client.ts', type: 'File', filePath: 'frontend/src/api/client.ts', language: 'TypeScript', startLine: 1, endLine: 120, componentId: null },
  { id: 'code-003', name: 'mockApi.ts', type: 'File', filePath: 'frontend/src/api/mockApi.ts', language: 'TypeScript', startLine: 1, endLine: 450, componentId: null },

  { id: 'code-010', name: 'IssueService', type: 'Class', filePath: 'mock-api/server.py', language: 'Python', startLine: 45, endLine: 180, componentId: null },
  { id: 'code-011', name: 'ComponentService', type: 'Class', filePath: 'mock-api/server.py', language: 'Python', startLine: 185, endLine: 260, componentId: null },
  { id: 'code-012', name: 'TaskerClient', type: 'Class', filePath: 'frontend/src/api/client.ts', language: 'TypeScript', startLine: 10, endLine: 115, componentId: null },

  { id: 'code-020', name: 'create_issue', type: 'Function', filePath: 'mock-api/server.py', language: 'Python', startLine: 50, endLine: 75, componentId: null },
  { id: 'code-021', name: 'list_issues', type: 'Function', filePath: 'mock-api/server.py', language: 'Python', startLine: 78, endLine: 100, componentId: null },
  { id: 'code-022', name: 'update_issue', type: 'Function', filePath: 'mock-api/server.py', language: 'Python', startLine: 103, endLine: 130, componentId: null },
  { id: 'code-023', name: 'delete_issue', type: 'Function', filePath: 'mock-api/server.py', language: 'Python', startLine: 133, endLine: 150, componentId: null },
  { id: 'code-024', name: 'fetchIssues', type: 'Function', filePath: 'frontend/src/api/client.ts', language: 'TypeScript', startLine: 15, endLine: 35, componentId: null },
  { id: 'code-025', name: 'createIssue', type: 'Function', filePath: 'frontend/src/api/client.ts', language: 'TypeScript', startLine: 38, endLine: 55, componentId: null },
  { id: 'code-026', name: 'getImpactAnalysis', type: 'Function', filePath: 'frontend/src/api/client.ts', language: 'TypeScript', startLine: 80, endLine: 95, componentId: null },
]

const MOCK_CODE_EDGES: CodeEdge[] = [
  { from: 'code-001', to: 'code-010', type: 'CONTAINS' },
  { from: 'code-001', to: 'code-011', type: 'CONTAINS' },
  { from: 'code-002', to: 'code-012', type: 'CONTAINS' },
  { from: 'code-010', to: 'code-020', type: 'CONTAINS' },
  { from: 'code-010', to: 'code-021', type: 'CONTAINS' },
  { from: 'code-010', to: 'code-022', type: 'CONTAINS' },
  { from: 'code-010', to: 'code-023', type: 'CONTAINS' },
  { from: 'code-012', to: 'code-024', type: 'CONTAINS' },
  { from: 'code-012', to: 'code-025', type: 'CONTAINS' },
  { from: 'code-012', to: 'code-026', type: 'CONTAINS' },
  { from: 'code-020', to: 'code-021', type: 'CALLS' },
  { from: 'code-022', to: 'code-023', type: 'CALLS' },
  { from: 'code-024', to: 'code-020', type: 'AFFECTS', issueId: 'ISS-001' },
  { from: 'code-025', to: 'code-020', type: 'AFFECTS', issueId: 'ISS-003' },
  { from: 'code-026', to: 'code-022', type: 'AFFECTS', issueId: 'ISS-005' },
  { from: 'code-022', to: 'code-021', type: 'CALLS' },
  { from: 'code-011', to: 'code-022', type: 'IMPORTS' },
]

export const useCodeGraphStore = defineStore('codeGraph', () => {
  const nodes = ref<CodeNode[]>([])
  const codeEdges = ref<CodeEdge[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const enabled = ref(false)

  async function fetchCodeStructure(): Promise<CodeStructureData> {
    loading.value = true
    error.value = null
    return new Promise((resolve) => {
      setTimeout(() => {
        nodes.value = [...MOCK_CODE_NODES]
        codeEdges.value = [...MOCK_CODE_EDGES]
        loading.value = false
        resolve({ nodes: nodes.value, edges: codeEdges.value })
      }, 300)
    })
  }

  function toggle() {
    enabled.value = !enabled.value
  }

  return {
    nodes,
    codeEdges,
    loading,
    error,
    enabled,
    fetchCodeStructure,
    toggle,
  }
})
