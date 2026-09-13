import { ref, computed } from 'vue'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface Toast {
  id: string
  type: ToastType
  message: string
  duration: number
  createdAt: number
  persistent?: boolean
}

const toasts = ref<Toast[]>([])
const MAX_TOASTS = 5

let counter = 0

function addToast(type: ToastType, message: string, options: { duration?: number; persistent?: boolean } = {}) {
  const id = `toast-${++counter}-${Date.now()}`
  const duration = options.duration ?? (type === 'error' ? 8000 : type === 'warning' ? 6000 : 4000)

  const toast: Toast = {
    id,
    type,
    message,
    duration,
    createdAt: Date.now(),
    persistent: options.persistent,
  }

  toasts.value.push(toast)

  if (toasts.value.length > MAX_TOASTS) {
    toasts.value = toasts.value.slice(-MAX_TOASTS)
  }

  if (!toast.persistent) {
    setTimeout(() => removeToast(id), duration)
  }

  return id
}

function removeToast(id: string) {
  toasts.value = toasts.value.filter(t => t.id !== id)
}

function clearAll() {
  toasts.value = []
}

export function useToast() {
  const count = computed(() => toasts.value.length)

  function success(message: string, options?: { duration?: number }) {
    return addToast('success', message, options)
  }

  function error(message: string, options?: { duration?: number; persistent?: boolean }) {
    return addToast('error', message, { duration: 8000, ...options })
  }

  function warning(message: string, options?: { duration?: number }) {
    return addToast('warning', message, { duration: 6000, ...options })
  }

  function info(message: string, options?: { duration?: number }) {
    return addToast('info', message, options)
  }

  return {
    toasts,
    count,
    success,
    error,
    warning,
    info,
    remove: removeToast,
    clearAll,
  }
}
