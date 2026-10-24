import { describe, it, expect, vi, beforeEach } from 'vitest'
import client from '@/api/client'
import {
  fetchAgentSkills,
  createAgentSkill,
  updateAgentSkill,
  deleteAgentSkill,
  importAgentSkill,
} from '@/api/agentSkillsApi'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockedGet = client.get as unknown as ReturnType<typeof vi.fn>
const mockedPost = client.post as unknown as ReturnType<typeof vi.fn>
const mockedPut = client.put as unknown as ReturnType<typeof vi.fn>
const mockedDelete = client.delete as unknown as ReturnType<typeof vi.fn>

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

  it('PUTs the patch to /agent-skills/{id} and returns the updated skill (issue #610)', async () => {
    mockedPut.mockResolvedValue({
      data: { data: { id: 'qa-bot', name: 'QA Bot v2', behavior: 'v2' } },
    })

    const skill = await updateAgentSkill('qa-bot', { name: 'QA Bot v2', behavior: 'v2' })

    expect(mockedPut).toHaveBeenCalledWith('/agent-skills/qa-bot', {
      name: 'QA Bot v2',
      behavior: 'v2',
    })
    expect(skill).toEqual({ id: 'qa-bot', name: 'QA Bot v2', behavior: 'v2' })
  })

  it('DELETEs /agent-skills/{id} (issue #610)', async () => {
    mockedDelete.mockResolvedValue({ data: { data: true } })

    await deleteAgentSkill('qa-bot')

    expect(mockedDelete).toHaveBeenCalledWith('/agent-skills/qa-bot')
  })

  it('uploads the .md as multipart form data on import (issue #610)', async () => {
    mockedPost.mockResolvedValue({
      data: { data: { id: 'data-quality-bot', name: 'Data Quality Bot', behavior: '# Data Quality Bot' } },
    })
    const file = new File(['# Data Quality Bot'], 'data-quality-bot.md', { type: 'text/markdown' })

    const skill = await importAgentSkill(file)

    const [url, form] = mockedPost.mock.calls[0]
    expect(url).toBe('/agent-skills/import')
    expect(form).toBeInstanceOf(FormData)
    expect((form as FormData).get('file')).toBe(file)
    expect(skill.id).toBe('data-quality-bot')
  })
})
