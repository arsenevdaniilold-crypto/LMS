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
