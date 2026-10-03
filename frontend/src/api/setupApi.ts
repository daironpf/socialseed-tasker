import client, { isMockMode } from './client'

export interface SetupStatus {
  installed: boolean
  needSetup: boolean
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
