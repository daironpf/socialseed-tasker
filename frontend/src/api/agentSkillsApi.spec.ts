import { describe, it, expect, vi, beforeEach } from 'vitest'
import client from '@/api/client'
import { fetchAgentSkills, createAgentSkill } from '@/api/agentSkillsApi'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

const mockedGet = client.get as unknown as ReturnType<typeof vi.fn>
const mockedPost = client.post as unknown as ReturnType<typeof vi.fn>

describe('agentSkillsApi', () => {
  beforeEach(() => vi.clearAllMocks())

  it('unwraps GET /agent-skills with the behavior text (issue #577)', async () => {
    mockedGet.mockResolvedValue({
      data: { data: [{ id: 'code-reviewer', name: 'Code Reviewer', behavior: 'Review carefully.' }] },
    })

    const skills = await fetchAgentSkills()

    expect(mockedGet).toHaveBeenCalledWith('/agent-skills', { suppressErrorToast: true })
    expect(skills).toEqual([
      { id: 'code-reviewer', name: 'Code Reviewer', behavior: 'Review carefully.' },
    ])
  })

  it('falls back to an empty list on an empty envelope', async () => {
    mockedGet.mockResolvedValue({ data: {} })

    await expect(fetchAgentSkills()).resolves.toEqual([])
  })

  it('POSTs name + behavior and returns the created skill', async () => {
    mockedPost.mockResolvedValue({
      data: { data: { id: 'security-analyst', name: 'Security Analyst', behavior: 'Assume hostile input.' } },
    })

    const skill = await createAgentSkill('Security Analyst', 'Assume hostile input.')

    expect(mockedPost).toHaveBeenCalledWith('/agent-skills', {
      name: 'Security Analyst',
      behavior: 'Assume hostile input.',
    })
    expect(skill.id).toBe('security-analyst')
  })
})
