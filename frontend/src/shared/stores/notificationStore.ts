import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import * as api from '@/shared/api/notifications'
import type { Notification } from '@/shared/api/types'

type Listener = (notif: Notification) => void
const listeners = new Set<Listener>()

export function onNotification(fn: Listener): () => void {
  listeners.add(fn)
  return () => listeners.delete(fn)
}

function isSilent(n: Notification): boolean {
  return Boolean(n.silent) || n.id === null
}

export const useNotificationStore = defineStore('notifications', () => {
  const items = ref<Notification[]>([])
  const loading = ref(false)

  const unreadCount = computed(() => items.value.filter((n) => !n.read).length)

  async function fetch(): Promise<void> {
    loading.value = true
    try {
      items.value = await api.listNotifications()
    } finally {
      loading.value = false
    }
  }

  function handleIncoming(notif: Notification): void {
    // Silent broadcasts (no DB persistence, e.g. realtime feed refresh
    // for teachers/admins) are not shown in the bell — only fan out to
    // listeners (ClassDetailPage, etc.).
    if (!isSilent(notif)) {
      items.value = [notif, ...items.value]
    }
    for (const fn of listeners) {
      try { fn(notif) } catch { /* swallow */ }
    }
  }

  async function markAllRead(): Promise<void> {
    if (unreadCount.value === 0) return
    await api.markRead({ all: true })
    items.value = items.value.map((n) => ({ ...n, read: true }))
  }

  async function markOneRead(id: string): Promise<void> {
    const target = items.value.find((n) => n.id === id)
    if (!target || target.read) return
    await api.markRead({ ids: [id] })
    items.value = items.value.map((n) => (n.id === id ? { ...n, read: true } : n))
  }

  function reset(): void {
    items.value = []
  }

  return { items, loading, unreadCount, fetch, handleIncoming, markAllRead, markOneRead, reset }
})
