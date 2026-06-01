import http from './http'
import type { Material } from './types'

export async function listMaterials(classId: string): Promise<Material[]> {
  const { data } = await http.get<Material[]>(`/classes/${classId}/materials`)
  return data
}

export async function createMaterial(
  classId: string,
  title: string,
  description: string,
  files: File[],
  links: string[],
): Promise<Material> {
  const fd = new FormData()
  fd.append('title', title)
  fd.append('description', description)
  for (const url of links) {
    fd.append('links', url)
  }
  for (const f of files) {
    fd.append('files', f)
  }
  const { data } = await http.post<Material>(`/classes/${classId}/materials`, fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export interface UpdateMaterialPayload {
  title?: string
  description?: string
}

export async function updateMaterial(
  id: string,
  payload: UpdateMaterialPayload,
): Promise<Material> {
  const { data } = await http.patch<Material>(`/materials/${id}`, payload)
  return data
}

export async function deleteMaterial(id: string): Promise<void> {
  await http.delete(`/materials/${id}`)
}
