import http from './http'
import type { Notification } from './types'

export async function listNotifications(): Promise<Notification[]> {
  const { data } = await http.get<Notification[]>('/notifications')
  return data
}

export async function markRead(opts: { ids?: string[]; all?: boolean }): Promise<{ updated: number }> {
  const { data } = await http.post<{ updated: number }>('/notifications/read', opts)
  return data
}
