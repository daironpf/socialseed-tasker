import { ref } from 'vue'
import type { NotificationCategory } from '@/types/notifications'

const ENABLED_KEY = 'sound-effects-enabled'
const VOLUME_KEY = 'sound-effects-volume'

const enabled = ref(localStorage.getItem(ENABLED_KEY) !== 'false')
const volume = ref(clampVolume(parseInt(localStorage.getItem(VOLUME_KEY) ?? '60', 10)))
const gestured = ref(false)

let audioCtx: AudioContext | null = null
let gestureBound = false

function clampVolume(value: number): number {
  if (Number.isNaN(value)) return 60
  return Math.min(100, Math.max(0, value))
}

function bindGesture() {
  if (gestureBound || typeof window === 'undefined') return
  gestureBound = true
  const onGesture = () => {
    gestured.value = true
    window.removeEventListener('pointerdown', onGesture)
    window.removeEventListener('keydown', onGesture)
  }
  window.addEventListener('pointerdown', onGesture)
  window.addEventListener('keydown', onGesture)
}

bindGesture()

function getAudioContext(): AudioContext | null {
  try {
    if (!audioCtx) {
      const Ctor = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
      if (!Ctor) return null
      audioCtx = new Ctor()
    }
    if (audioCtx.state === 'suspended') void audioCtx.resume()
    return audioCtx
  } catch {
    return null
  }
}

function beep(freq: number, offsetSec: number, durationSec: number, type: OscillatorType = 'sine', gainMul = 1) {
  if (!enabled.value || !gestured.value || volume.value <= 0) return
  const ctx = getAudioContext()
  if (!ctx) return
  try {
    const start = ctx.currentTime + offsetSec
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = type
    osc.frequency.setValueAtTime(freq, start)
    const peak = (volume.value / 100) * 0.22 * gainMul
    gain.gain.setValueAtTime(0.0001, start)
    gain.gain.linearRampToValueAtTime(peak, start + 0.015)
    gain.gain.exponentialRampToValueAtTime(0.0001, start + durationSec)
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start(start)
    osc.stop(start + durationSec + 0.05)
  } catch {
    // audio playback unavailable (autoplay policy, no output device)
  }
}

export function useSoundEffects() {
  function setEnabled(value: boolean) {
    enabled.value = value
    localStorage.setItem(ENABLED_KEY, String(value))
  }

  function setVolume(value: number) {
    volume.value = clampVolume(value)
    localStorage.setItem(VOLUME_KEY, String(volume.value))
  }

  function playAlert() {
    beep(880, 0, 0.14, 'square')
    beep(660, 0.17, 0.16, 'square')
    beep(440, 0.36, 0.22, 'square', 0.9)
  }

  function playSuccess() {
    beep(523.25, 0, 0.14, 'sine')
    beep(659.25, 0.09, 0.14, 'sine')
    beep(783.99, 0.18, 0.14, 'sine')
    beep(1046.5, 0.27, 0.2, 'sine')
  }

  function playPing() {
    beep(1046.5, 0, 0.08, 'sine', 0.7)
    beep(1046.5, 0.13, 0.08, 'sine', 0.7)
  }

  function playForCategory(category: NotificationCategory) {
    if (category === 'constraint_violation' || category === 'agent_failure' || category === 'sla') {
      playAlert()
    } else {
      playPing()
    }
  }

  return {
    enabled,
    volume,
    gestured,
    setEnabled,
    setVolume,
    playAlert,
    playSuccess,
    playPing,
    playForCategory,
  }
}
