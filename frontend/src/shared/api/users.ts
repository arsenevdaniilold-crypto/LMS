import http from './http'

export interface UpdateMePayload {
  username?: string
  avatar_url?: string | null
}

export interface UserMe {
  id: string
  email: string
  username: string
  avatar_url: string | null
  is_admin: boolean
  created_at: string
}

export async function updateMe(payload: UpdateMePayload): Promise<UserMe> {
  const { data } = await http.patch<UserMe>('/users/me', payload)
  return data
}

export async function uploadAvatar(file: File): Promise<UserMe> {
  const fd = new FormData()
  fd.append('file', file)
  const { data } = await http.post<UserMe>('/users/me/avatar', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function deleteAvatar(): Promise<UserMe> {
  const { data } = await http.delete<UserMe>('/users/me/avatar')
  return data
}
