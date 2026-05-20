import http from './http'
import type { AdminClassList, AdminStats, AdminUser, AdminUsersList } from './types'

export interface AdminListParams {
  search?: string
  include_deleted?: boolean
  page?: number
  page_size?: number
}

export async function listUsers(params: AdminListParams = {}): Promise<AdminUsersList> {
  const { data } = await http.get<AdminUsersList>('/admin/users', { params })
  return data
}

export async function blockUser(id: string): Promise<AdminUser> {
  const { data } = await http.post<AdminUser>(`/admin/users/${id}/block`)
  return data
}

export async function unblockUser(id: string): Promise<AdminUser> {
  const { data } = await http.post<AdminUser>(`/admin/users/${id}/unblock`)
  return data
}

export async function listClasses(params: AdminListParams = {}): Promise<AdminClassList> {
  const { data } = await http.get<AdminClassList>('/admin/classes', { params })
  return data
}

export async function deleteClass(id: string): Promise<void> {
  await http.delete(`/admin/classes/${id}`)
}

export async function getStats(): Promise<AdminStats> {
  const { data } = await http.get<AdminStats>('/admin/stats')
  return data
}
