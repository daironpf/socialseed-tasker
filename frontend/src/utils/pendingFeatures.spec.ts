import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { setApiMode } from '@/api/client'
import { PENDING_FEATURE_ROUTES, isPendingFeature, isRealPendingFeature } from '@/utils/pendingFeatures'

describe('pendingFeatures', () => {
  beforeEach(() => setApiMode('mock'))
  afterEach(() => setApiMode('mock'))

  it('marks pending routes as pending in mock mode', () => {
    setApiMode('mock')
    expect(isPendingFeature('/finops')).toBe(true)
    expect(isPendingFeature('/organization')).toBe(true)
    expect(isRealPendingFeature('/finops')).toBe(false)
  })

  it('keeps the badge visible when consuming the real REST backend', () => {
    setApiMode('real')
    expect(isPendingFeature('/finops')).toBe(true)
    expect(isRealPendingFeature('/finops')).toBe(true)
    expect(isRealPendingFeature('/chat')).toBe(true)
  })

  it('only exposes the real-mode chip for pending routes', () => {
    setApiMode('real')
    expect(isPendingFeature('/rag')).toBe(false)
    expect(isRealPendingFeature('/rag')).toBe(false)
    expect(isPendingFeature('/profile')).toBe(false)
    expect(isRealPendingFeature('/profile')).toBe(false)
  })

  it('stores absolute nav paths without duplicates', () => {
    expect(PENDING_FEATURE_ROUTES.length).toBeGreaterThan(0)
    expect(PENDING_FEATURE_ROUTES.every(route => route.startsWith('/'))).toBe(true)
    expect(new Set(PENDING_FEATURE_ROUTES).size).toBe(PENDING_FEATURE_ROUTES.length)
  })
})
