import http from './http'
import type { Announcement } from './types'

export async function listAnnouncements(classId: string): Promise<Announcement[]> {
  const { data } = await http.get<Announcement[]>(`/classes/${classId}/announcements`)
  return data
}

export async function createAnnouncement(
  classId: string,
  title: string,
  text: string,
  files: File[],
): Promise<Announcement> {
  const fd = new FormData()
  fd.append('title', title)
  fd.append('text', text)
  for (const f of files) {
    fd.append('files', f)
  }
  const { data } = await http.post<Announcement>(`/classes/${classId}/announcements`, fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function deleteAnnouncement(id: string): Promise<void> {
  await http.delete(`/announcements/${id}`)
}
