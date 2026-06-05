import http from './http'
import type {
  ClassDetail,
  ClassListResponse,
  ClassMember,
  ClassResponse,
  ClassType,
} from './types'

export interface CreateClassPayload {
  name: string
  type: ClassType
}

export interface UpdateClassPayload {
  name?: string
}

export interface ListClassesParams {
  search?: string
  teacher?: string
  sort?: 'created_desc' | 'created_asc' | 'name_asc'
  page?: number
  page_size?: number
}

export async function listOpenClasses(params: ListClassesParams = {}): Promise<ClassListResponse> {
  const { data } = await http.get<ClassListResponse>('/classes', { params })
  return data
}

export async function listMyClasses(): Promise<ClassResponse[]> {
  const { data } = await http.get<ClassResponse[]>('/classes/my')
  return data
}

export async function getClass(id: string): Promise<ClassDetail> {
  const { data } = await http.get<ClassDetail>(`/classes/${id}`)
  return data
}

export async function createClass(payload: CreateClassPayload): Promise<ClassDetail> {
  const { data } = await http.post<ClassDetail>('/classes', payload)
  return data
}

export async function updateClass(id: string, payload: UpdateClassPayload): Promise<ClassDetail> {
  const { data } = await http.patch<ClassDetail>(`/classes/${id}`, payload)
  return data
}

export async function deleteClass(id: string): Promise<void> {
  await http.delete(`/classes/${id}`)
}

export async function regenerateInviteCode(id: string): Promise<ClassDetail> {
  const { data } = await http.post<ClassDetail>(`/classes/${id}/regenerate-invite`)
  return data
}

export async function joinByCode(invite_code: string): Promise<ClassDetail> {
  const { data } = await http.post<ClassDetail>('/classes/join', { invite_code })
  return data
}

export async function joinOpenClass(id: string): Promise<ClassDetail> {
  const { data } = await http.post<ClassDetail>(`/classes/${id}/join`)
  return data
}

export async function listMembers(id: string): Promise<ClassMember[]> {
  const { data } = await http.get<ClassMember[]>(`/classes/${id}/members`)
  return data
}

export async function inviteTeacher(id: string, email: string): Promise<ClassMember> {
  const { data } = await http.post<ClassMember>(`/classes/${id}/invite-teacher`, { email })
  return data
}

export async function removeMember(id: string, userId: string): Promise<void> {
  await http.delete(`/classes/${id}/members/${userId}`)
}

export async function promoteMember(id: string, userId: string): Promise<ClassMember> {
  const { data } = await http.post<ClassMember>(`/classes/${id}/members/${userId}/promote`)
  return data
}

export async function demoteMember(
  id: string,
  userId: string,
  newCreatorId?: string,
): Promise<ClassMember> {
  const { data } = await http.post<ClassMember>(`/classes/${id}/members/${userId}/demote`, {
    new_creator_id: newCreatorId ?? null,
  })
  return data
}
