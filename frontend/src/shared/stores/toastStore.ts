import { reactive } from 'vue'

export type ToastKind = 'success' | 'error' | 'info'

export interface Toast {
  id: number
  kind: ToastKind
  message: string
}

interface ToastState {
  items: Toast[]
}

const state = reactive<ToastState>({ items: [] })
let nextId = 1

function remove(id: number): void {
  const idx = state.items.findIndex((t) => t.id === id)
  if (idx !== -1) state.items.splice(idx, 1)
}

function push(kind: ToastKind, message: string, ttl = 3500): void {
  const id = nextId++
  state.items.push({ id, kind, message })
  setTimeout(() => remove(id), ttl)
}

export function useToast() {
  return {
    items: state.items,
    success: (msg: string) => push('success', msg),
    error: (msg: string) => push('error', msg, 5000),
    info: (msg: string) => push('info', msg),
    dismiss: (id: number) => remove(id),
  }
}
