import { ref } from 'vue'

export interface Toast {
  id: number
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
  duration: number
}

const toasts = ref<Toast[]>([])
let nextId = 0

function showToast(message: string, type: Toast['type'] = 'info', duration = 4000) {
  const id = nextId++
  toasts.value.push({ id, message, type, duration })
  setTimeout(() => {
    removeToast(id)
  }, duration)
}

function removeToast(id: number) {
  const idx = toasts.value.findIndex((t) => t.id === id)
  if (idx !== -1) toasts.value.splice(idx, 1)
}

function success(message: string, duration = 4000) {
  showToast(message, 'success', duration)
}

function error(message: string, duration = 8000) {
  showToast(message, 'error', duration)
}

function warning(message: string, duration = 6000) {
  showToast(message, 'warning', duration)
}

function info(message: string, duration = 4000) {
  showToast(message, 'info', duration)
}

export function useToast() {
  return { toasts, showToast, removeToast, success, error, warning, info }
}
