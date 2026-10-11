import { describe, it, expect, vi, beforeEach } from 'vitest'
import client from '@/api/client'
import { fetchUserSkills, addUserSkill, removeUserSkill } from '@/api/userSkillsApi'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockedGet = client.get as unknown as ReturnType<typeof vi.fn>
const mockedPost = client.post as unknown as ReturnType<typeof vi.fn>
const mockedDelete = client.delete as unknown as ReturnType<typeof vi.fn>

describe('userSkillsApi', () => {
  beforeEach(() => vi.clearAllMocks())

  it('unwraps GET /users/{id}/skills (issue #576)', async () => {
    mockedGet.mockResolvedValue({
      data: { data: [{ user_id: 'u1', skill_id: 'python', name: 'Python' }] },
    })

    const skills = await fetchUserSkills('u1')

    expect(mockedGet).toHaveBeenCalledWith('/users/u1/skills')
    expect(skills).toEqual([{ user_id: 'u1', skill_id: 'python', name: 'Python' }])
  })

  it('falls back to an empty list on an empty envelope', async () => {
    mockedGet.mockResolvedValue({ data: {} })

    await expect(fetchUserSkills('u1')).resolves.toEqual([])
  })

  it('POSTs the skill name and returns the created assignment', async () => {
    mockedPost.mockResolvedValue({
      data: { data: { user_id: 'u1', skill_id: 'docker', name: 'Docker' } },
    })

    const item = await addUserSkill('u1', 'Docker')

    expect(mockedPost).toHaveBeenCalledWith('/users/u1/skills', { name: 'Docker' })
    expect(item).toEqual({ user_id: 'u1', skill_id: 'docker', name: 'Docker' })
  })

  it('DELETEs the specific assignment by slug', async () => {
    mockedDelete.mockResolvedValue({ data: { data: true } })

    await removeUserSkill('u1', 'machine-learning')

    expect(mockedDelete).toHaveBeenCalledWith('/users/u1/skills/machine-learning')
  })

  it('encodes ids so slugs with dashes survive the URL', async () => {
    mockedDelete.mockResolvedValue({ data: { data: true } })

    await removeUserSkill('u 1', 'ci/cd')

    expect(mockedDelete).toHaveBeenCalledWith('/users/u%201/skills/ci%2Fcd')
  })
})
