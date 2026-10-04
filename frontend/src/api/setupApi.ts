import client, { isMockMode } from './client'

export interface SetupStatus {
  installed: boolean
  needSetup: boolean
}

export interface SetupInitializePayload {
  admin_user: string
  admin_password: string
  project_name: string
  project_summary: string
  policies: string[]
  custom_policies: string[]
  api_key: string
  mcp_port: number
  confirm_wipe: boolean
}

export interface SetupInitializeResult {
  installed: boolean
  adminUsername: string
  projectName: string
  projectId: string
  policies: string[]
  credentials: string
  apiKey: string
  mcpPort: number
}

export async function getSetupStatus(): Promise<SetupStatus> {
  if (isMockMode()) {
    return { installed: true, needSetup: false }
  }
  const { data } = await client.get<{ data?: SetupStatus }>('/setup/status')
  const payload = data?.data
  if (!payload) {
    return { installed: true, needSetup: false }
  }
  return { installed: payload.installed, needSetup: payload.needSetup }
}

export async function postSetupInitialize(
  payload: SetupInitializePayload,
): Promise<SetupInitializeResult | null> {
  if (isMockMode()) {
    return null
  }
  const { data } = await client.post<{ data?: SetupInitializeResult }>(
    '/setup/initialize',
    payload,
    { suppressErrorToast: true },
  )
  return data?.data ?? null
}
