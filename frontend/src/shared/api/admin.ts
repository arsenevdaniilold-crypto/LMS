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

/** Hard-deletes a user; throws 409 with details.classes_owned if any.
 *  Pass force=true to wipe all of the user's content and classes outright. */
export async function deleteUser(id: string, force = false): Promise<void> {
  await http.delete(`/admin/users/${id}`, { params: force ? { force: true } : {} })
}

/** Reassigns a class to a new creator. */
export async function transferClass(classId: string, newCreatorId: string): Promise<void> {
  await http.post(`/admin/classes/${classId}/transfer`, { new_creator_id: newCreatorId })
}

/** Shape of the 409 response detail returned by DELETE /admin/users/{id}. */
export interface DeleteUserConflict {
  code: 'USER_HAS_CONTENT'
  message: string
  details: {
    classes_owned: { id: string; name: string }[]
    announcements: number
    assignments: number
    solutions: number
  }
}
