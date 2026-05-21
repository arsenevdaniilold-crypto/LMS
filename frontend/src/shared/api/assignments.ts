import http from './http'
import type {
  Assignment,
  AssignmentType,
  GradeType,
  GradingType,
  Group,
} from './types'

export interface CreateAssignmentPayload {
  name: string
  description?: string
  type: AssignmentType
  grade_type: GradeType
  grading_type?: GradingType | null
  group_count?: number | null
  deadline?: string | null
  files: File[]
  links: string[]
}

export async function listAssignments(classId: string): Promise<Assignment[]> {
  const { data } = await http.get<Assignment[]>(`/classes/${classId}/assignments`)
  return data
}

export async function getAssignment(id: string): Promise<Assignment> {
  const { data } = await http.get<Assignment>(`/assignments/${id}`)
  return data
}

export async function createAssignment(
  classId: string,
  payload: CreateAssignmentPayload,
): Promise<Assignment> {
  const fd = new FormData()
  fd.append('name', payload.name)
  if (payload.description) fd.append('description', payload.description)
  fd.append('type', payload.type)
  fd.append('grade_type', payload.grade_type)
  if (payload.grading_type) fd.append('grading_type', payload.grading_type)
  if (payload.group_count != null) fd.append('group_count', String(payload.group_count))
  if (payload.deadline) fd.append('deadline', payload.deadline)
  for (const f of payload.files) fd.append('files', f)
  for (const l of payload.links) fd.append('links', l)
  const { data } = await http.post<Assignment>(`/classes/${classId}/assignments`, fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export interface UpdateAssignmentPayload {
  name?: string
  description?: string
  deadline?: string | null
}

export async function updateAssignment(id: string, payload: UpdateAssignmentPayload): Promise<Assignment> {
  const { data } = await http.patch<Assignment>(`/assignments/${id}`, payload)
  return data
}

export async function deleteAssignment(id: string): Promise<void> {
  await http.delete(`/assignments/${id}`)
}

export async function listGroups(assignmentId: string): Promise<Group[]> {
  const { data } = await http.get<Group[]>(`/assignments/${assignmentId}/groups`)
  return data
}

export async function createGroupsAuto(assignmentId: string, group_count: number): Promise<Group[]> {
  const { data } = await http.post<Group[]>(`/assignments/${assignmentId}/groups`, {
    mode: 'auto',
    group_count,
  })
  return data
}

export async function createGroupsManual(assignmentId: string, groups: string[][]): Promise<Group[]> {
  const { data } = await http.post<Group[]>(`/assignments/${assignmentId}/groups`, {
    mode: 'manual',
    groups,
  })
  return data
}
