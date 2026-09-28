export type PipelineStageId = 'test_failure' | 'neo4j_root_cause' | 'task_generation' | 'agent_fix' | 'pr_created'
export type PipelineStageStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
export type PipelineRunStatus = 'running' | 'completed' | 'failed' | 'cancelled'

export interface PipelineStage {
  id: PipelineStageId
  label: string
  status: PipelineStageStatus
  startedAt?: string
  completedAt?: string
  durationMs?: number
  details?: string
}

export interface LogEntry {
  id: string
  runId: string
  timestamp: string
  source: 'test' | 'agent' | 'system'
  content: string
}

export interface PatchMeta {
  id: string
  runId: string
  stageId: string
  strategy: string
  filename: string
  files: string[]
  createdAt: string
  sizeBytes: number
  commitSha: string
}

export interface PipelineRun {
  id: string
  issueId: string
  issueTitle: string
  repo: string
  branch: string
  commitSha: string
  stages: PipelineStage[]
  currentStageIndex: number
  startedAt: string
  completedAt?: string
  status: PipelineRunStatus
  prUrl?: string
  neo4jNodeId?: string
  createdIssueId?: string
  patches?: PatchMeta[]
  logs?: LogEntry[]
}

export interface FixAttempt {
  id: string
  runId: string
  timestamp: string
  description: string
  filesChanged: string[]
  status: 'attempting' | 'success' | 'failed'
  diffPreview?: string
  error?: string
}
