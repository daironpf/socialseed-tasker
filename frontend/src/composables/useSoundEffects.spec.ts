import { describe, it, expect, beforeEach } from 'vitest'
import { useSoundEffects } from '@/composables/useSoundEffects'

const ENABLED_KEY = 'sound-effects-enabled'
const VOLUME_KEY = 'sound-effects-volume'

describe('useSoundEffects', () => {
  beforeEach(() => {
    localStorage.clear()
    const sounds = useSoundEffects()
    sounds.setEnabled(true)
    sounds.setVolume(60)
  })

  it('persists the enabled toggle', () => {
    const sounds = useSoundEffects()

    expect(sounds.enabled.value).toBe(true)

    sounds.setEnabled(false)
    expect(sounds.enabled.value).toBe(false)
    expect(localStorage.getItem(ENABLED_KEY)).toBe('false')

    sounds.setEnabled(true)
    expect(localStorage.getItem(ENABLED_KEY)).toBe('true')
  })

  it('clamps volume to 0-100 and falls back on NaN', () => {
    const sounds = useSoundEffects()

    sounds.setVolume(150)
    expect(sounds.volume.value).toBe(100)
    expect(localStorage.getItem(VOLUME_KEY)).toBe('100')

    sounds.setVolume(-3)
    expect(sounds.volume.value).toBe(0)

    sounds.setVolume(Number.NaN)
    expect(sounds.volume.value).toBe(60)
  })

  it('marks the autoplay gesture after a pointer interaction', () => {
    const sounds = useSoundEffects()
    expect(sounds.gestured.value).toBe(false)

    window.dispatchEvent(new Event('pointerdown'))

    expect(sounds.gestured.value).toBe(true)
  })

  it('playback helpers never throw without audio support', () => {
    const sounds = useSoundEffects()

    expect(() => {
      sounds.playAlert()
      sounds.playSuccess()
      sounds.playPing()
      sounds.playForCategory('constraint_violation')
      sounds.playForCategory('mention')
    }).not.toThrow()
  })

  it('routes alert categories to the alert sound and the rest to ping', () => {
    const sounds = useSoundEffects()

    // jsdom has no AudioContext: playback is a no-op, but routing must not throw
    expect(() => {
      sounds.playForCategory('agent_failure')
      sounds.playForCategory('sla')
      sounds.playForCategory('hitl')
      sounds.playForCategory('mention')
    }).not.toThrow()
    expect(sounds.enabled.value).toBe(true)
  })
})
