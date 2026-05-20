export type ClassType = 'open' | 'closed'
export type MemberRole = 'teacher_creator' | 'teacher' | 'student'
export type AssignmentType = 'individual' | 'group'
export type GradeType = '0-5' | '0-100' | '0-1'
export type GradingType = 'uniform' | 'individual'
export type MaterialType = 'link' | 'file'
export type SolutionStatus =
  | 'created'
  | 'submitted'
  | 'returned'
  | 'graded'
  | 'pending_redistribution'

export interface UserShort {
  id: string
  username: string
}

export interface ClassResponse {
  id: string
  name: string
  type: ClassType
  creator_id: string
  creator: UserShort | null
  created_at: string
  member_count: number
  my_role: MemberRole | null
}

export interface ClassDetail extends ClassResponse {
  invite_code: string | null
}

export interface ClassListResponse {
  items: ClassResponse[]
  total: number
  page: number
  page_size: number
}

export interface ClassMember {
  user_id: string
  username: string
  email: string
  avatar_url: string | null
  role: MemberRole
  joined_at: string
}

export interface AnnouncementFile {
  id: string
  file_name: string
  file_size: number
  download_url: string
}

export interface Announcement {
  id: string
  class_id: string
  title: string
  text: string
  author: UserShort
  created_at: string
  files: AnnouncementFile[]
}

export interface AssignmentMaterial {
  id: string
  material_type: MaterialType
  url: string | null
  file_name: string | null
  download_url: string | null
}

export interface Assignment {
  id: string
  class_id: string
  name: string
  description: string | null
  type: AssignmentType
  grade_type: GradeType
  grading_type: GradingType | null
  group_count: number | null
  deadline: string | null
  author: UserShort
  created_at: string
  materials: AssignmentMaterial[]
}

export interface Group {
  id: string
  name: string
  members: { user_id: string; username: string }[]
}

export interface SolutionFile {
  id: string
  file_name: string
  file_size: number
  download_url: string
}

export interface RedistributionEntry {
  user_id: string
  username: string
  grade: string
}

export interface Solution {
  id: string
  assignment_id: string
  creator_id: string
  creator_username: string
  group: Group | null
  text: string | null
  status: SolutionStatus
  grade: string | null
  submitted_at: string | null
  graded_at: string | null
  created_at: string
  updated_at: string
  files: SolutionFile[]
  redistribution: RedistributionEntry[] | null
}

export interface GradeMatrixCell {
  solution_id: string | null
  status: SolutionStatus | null
  grade: string | null
}

export interface GradeMatrixStudent {
  user_id: string
  username: string
  grades: Record<string, GradeMatrixCell>
}

export interface GradeMatrixAssignment {
  id: string
  name: string
  grade_type: string
  type: string
}

export interface GradesSummary {
  assignments: GradeMatrixAssignment[]
  students: GradeMatrixStudent[]
}

export interface Notification {
  id: string
  type: string
  payload: Record<string, unknown>
  read: boolean
  created_at: string
}

export interface AdminUser {
  id: string
  email: string
  username: string
  avatar_url: string | null
  is_admin: boolean
  created_at: string
  deleted_at: string | null
}

export interface AdminUsersList {
  items: AdminUser[]
  total: number
  page: number
  page_size: number
}

export interface AdminClass {
  id: string
  name: string
  type: string
  creator_id: string
  creator_username: string
  member_count: number
  created_at: string
  deleted_at: string | null
}

export interface AdminClassList {
  items: AdminClass[]
  total: number
  page: number
  page_size: number
}

export interface AdminStats {
  users_total: number
  users_active: number
  classes_total: number
  classes_active: number
  solutions_total: number
  file_bytes: number
}
