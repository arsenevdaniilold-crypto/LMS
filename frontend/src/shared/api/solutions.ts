import http from './http'
import type { GradesSummary, Solution } from './types'

export async function listSolutions(assignmentId: string): Promise<Solution[]> {
  const { data } = await http.get<Solution[]>(`/assignments/${assignmentId}/solutions`)
  return data
}

export async function getSolution(id: string): Promise<Solution> {
  const { data } = await http.get<Solution>(`/solutions/${id}`)
  return data
}

export async function createSolution(
  assignmentId: string,
  text: string,
  files: File[],
): Promise<Solution> {
  const fd = new FormData()
  if (text) fd.append('text', text)
  for (const f of files) fd.append('files', f)
  const { data } = await http.post<Solution>(`/assignments/${assignmentId}/solutions`, fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function updateSolution(id: string, text: string, files: File[]): Promise<Solution> {
  const fd = new FormData()
  if (text) fd.append('text', text)
  for (const f of files) fd.append('files', f)
  const { data } = await http.patch<Solution>(`/solutions/${id}`, fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function submitSolution(id: string): Promise<Solution> {
  const { data } = await http.post<Solution>(`/solutions/${id}/submit`)
  return data
}

export async function returnSolution(id: string): Promise<Solution> {
  const { data } = await http.post<Solution>(`/solutions/${id}/return`)
  return data
}

export async function gradeSolution(id: string, grade: number): Promise<Solution> {
  const { data } = await http.post<Solution>(`/solutions/${id}/grade`, { grade })
  return data
}

export async function redistributeSolution(
  id: string,
  grades: { user_id: string; grade: number }[],
): Promise<Solution> {
  const { data } = await http.post<Solution>(`/solutions/${id}/redistribute`, { grades })
  return data
}

export async function getClassGrades(classId: string): Promise<GradesSummary> {
  const { data } = await http.get<GradesSummary>(`/classes/${classId}/grades`)
  return data
}
