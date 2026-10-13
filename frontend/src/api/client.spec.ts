import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AxiosError, type InternalAxiosRequestConfig, type AxiosResponse } from 'axios'

const { toastError } = vi.hoisted(() => ({ toastError: vi.fn() }))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({ error: toastError, success: vi.fn(), info: vi.fn(), warning: vi.fn() }),
}))

import client, { setApiMode } from './client'

type AdapterConfig = InternalAxiosRequestConfig & { adapter?: unknown }

function reject429(config: InternalAxiosRequestConfig): Promise<never> {
  return Promise.reject(
    new AxiosError(
      'Request failed with status code 429',
      'ERR_BAD_REQUEST',
      config,
      null,
      {
        status: 429,
        statusText: 'Too Many Requests',
        headers: { 'retry-after': '0.01' },
        config,
        data: { error: 'rate_limited' },
      } as AxiosResponse,
    ),
  )
}

describe('client rate-limit retry (429)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setApiMode('real')
  })

  it('replays the request once after Retry-After and resolves on success', async () => {
    let calls = 0
    client.defaults.adapter = (config: AdapterConfig) => {
      calls += 1
      if (calls === 1) return reject429(config)
      return Promise.resolve({
        data: { data: [] },
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      })
    }

    const res = await client.get('/users')

    expect(res.status).toBe(200)
    expect(calls).toBe(2)
    expect(toastError).not.toHaveBeenCalled()
  })

  it('gives up after a single retry and surfaces the 429 error', async () => {
    let calls = 0
    client.defaults.adapter = (config: AdapterConfig) => {
      calls += 1
      return reject429(config)
    }

    await expect(client.get('/users')).rejects.toMatchObject({ status: 429 })
    expect(calls).toBe(2)
    expect(toastError).toHaveBeenCalledTimes(1)
  })

  it('does not retry other error statuses (only 429 replays)', async () => {
    let calls = 0
    client.defaults.adapter = (config: AdapterConfig) => {
      calls += 1
      return Promise.reject(
        new AxiosError(
          'Request failed with status code 500',
          'ERR_BAD_REQUEST',
          config,
          null,
          {
            status: 500,
            statusText: 'Internal Server Error',
            headers: {},
            config,
            data: { detail: 'boom' },
          } as AxiosResponse,
        ),
      )
    }

    await expect(client.post('/users', {})).rejects.toMatchObject({ status: 500 })
    expect(calls).toBe(1)
  })
})
