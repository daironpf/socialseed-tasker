import { describe, it, expect, vi, beforeEach } from 'vitest'
import client from '@/api/client'
import { analyzeImpact, analyzeRootCause, fetchTestFailures } from '@/api/analysisApi'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

const mockedGet = client.get as unknown as ReturnType<typeof vi.fn>
const mockedPost = client.post as unknown as ReturnType<typeof vi.fn>

describe('analysisApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('analyzeImpact calls /analyze/impact/{id} and unwraps the envelope', async () => {
    const impact = { issue_id: 'ISS-1', issue_title: 'Test', risk_level: 'LOW' }
    mockedGet.mockResolvedValue({ data: { data: impact } })

    const result = await analyzeImpact('ISS-1')

    expect(mockedGet).toHaveBeenCalledWith('/analyze/impact/ISS-1')
    expect(result).toEqual(impact)
  })

  it('analyzeImpact throws when the envelope has no data', async () => {
    mockedGet.mockResolvedValue({ data: {} })

    await expect(analyzeImpact('ISS-1')).rejects.toThrow('Failed to analyze impact')
  })

  it('analyzeRootCause posts to /analyze/root-cause with a generated test_id', async () => {
    mockedPost.mockResolvedValue({ data: { data: [] } })

    await analyzeRootCause({
      test_name: 'test_login',
      error_message: 'AssertionError',
      component: 'Backend API',
      labels: ['auth'],
    })

    expect(mockedPost).toHaveBeenCalledTimes(1)
    const [url, body] = mockedPost.mock.calls[0]
    expect(url).toBe('/analyze/root-cause')
    expect(body.test_id).toMatch(/^manual-/)
    expect(body.test_name).toBe('test_login')
    expect(body.error_message).toBe('AssertionError')
    expect(body.component).toBe('Backend API')
    expect(body.labels).toEqual(['auth'])
  })

  it('analyzeRootCause defaults labels to an empty list', async () => {
    mockedPost.mockResolvedValue({ data: { data: [] } })

    await analyzeRootCause({ test_name: 't', error_message: 'e' })

    const [, body] = mockedPost.mock.calls[0]
    expect(body.labels).toEqual([])
    expect(body.component).toBeUndefined()
  })

  it('fetchTestFailures calls /test-failures and unwraps the list', async () => {
    const failures = [{ test_id: 'TEST-001', test_name: 'test_a' }]
    mockedGet.mockResolvedValue({ data: { data: failures } })

    const result = await fetchTestFailures()

    expect(mockedGet).toHaveBeenCalledWith('/test-failures')
    expect(result).toEqual(failures)
  })
})
