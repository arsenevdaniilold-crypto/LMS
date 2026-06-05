<template>
  <div class="container page">
    <div v-if="loading" class="card sk-card">
      <span class="sk-line" style="width: 35%"></span>
      <span class="sk-line" style="width: 85%"></span>
      <span class="sk-line" style="width: 70%"></span>
    </div>
    <div v-else-if="!cls" class="card muted">Класс не найден</div>
    <template v-else>
      <div class="split-title">
        <div>
          <div class="title-kicker">Карточка класса</div>
          <h1 class="page-title">{{ cls.name }}</h1>
          <div class="badges" style="margin-top: 10px">
            <span class="badge" :class="cls.type === 'open' ? 'badge-open' : 'badge-closed'">
              {{ cls.type === 'open' ? 'открытый' : 'закрытый' }}
            </span>
            <span v-if="cls.my_role" class="badge" :class="roleBadge(cls.my_role)">
              {{ roleLabel(cls.my_role) }}
            </span>
            <span
              v-if="cls.invite_code"
              class="badge invite-badge"
              :title="'Нажмите, чтобы скопировать код ' + cls.invite_code"
              @click="copyInvite"
            >код: {{ cls.invite_code }}</span>
            <button
              v-if="cls.invite_code && (isTeacher || isAdmin)"
              class="badge invite-refresh"
              type="button"
              :disabled="regenLoading"
              :title="'Сгенерировать новый код. Старый перестанет работать.'"
              @click="onRegenerateInvite"
            >{{ regenLoading ? '…' : '↻ обновить' }}</button>
          </div>
        </div>
        <div class="split-title-right">
          <RouterLink v-if="isTeacher" :to="`/classes/${cls.id}/grades`" class="btn-ghost">
            Сводная таблица
          </RouterLink>
          <button v-if="isTeacher" class="btn-ghost" @click="showRename = !showRename">
            Переименовать
          </button>
          <button
            v-if="cls.my_role === 'teacher_creator'"
            class="btn-danger"
            @click="onDelete"
          >
            Удалить класс
          </button>
        </div>
      </div>
      <div class="title-line"></div>

      <div v-if="showRename" class="card" style="margin-bottom: 16px">
        <div class="row" style="gap: 8px">
          <input v-model="renameValue" :placeholder="cls.name" />
          <button class="btn-primary" @click="onRename">Сохранить</button>
          <button class="btn-ghost" @click="showRename = false">Отмена</button>
        </div>
      </div>

      <div class="tabbar">
        <button
          v-for="t in tabs"
          :key="t.id"
          class="tab"
          :class="{ on: tab === t.id }"
          @click="tab = t.id"
        >{{ t.label }}</button>
      </div>

      <!-- Лента: объявления + задания -->
      <div v-if="tab === 'feed'" class="stack">
        <div v-if="isTeacher" class="row" style="margin-bottom: 4px">
          <button class="btn-primary" @click="showNewAnn = !showNewAnn">Новое объявление</button>
          <button class="btn-accent" @click="showNewAsn = !showNewAsn">Новое задание</button>
        </div>

        <NewAnnouncementForm
          v-if="showNewAnn"
          :class-id="cls.id"
          @created="onAnnouncementCreated"
          @cancel="showNewAnn = false"
        />

        <NewAssignmentForm
          v-if="showNewAsn"
          :class-id="cls.id"
          @created="onAssignmentCreated"
          @cancel="showNewAsn = false"
        />

        <div v-if="feedLoading" class="card sk-card">
          <span class="sk-line" style="width: 25%"></span>
          <span class="sk-line" style="width: 60%"></span>
        </div>
        <div v-else-if="feed.length === 0" class="card muted">Пока ничего не опубликовано</div>
        <div v-else class="stack">
          <FeedItem
            v-for="item in feed"
            :key="`${item.kind}-${item.id}`"
            :item="item"
            :is-teacher="isTeacher"
            :can-delete="isAdmin"
            @deleted="onFeedItemDeleted"
            @updated="onFeedItemUpdated"
          />
        </div>
      </div>

      <!-- Оценки -->
      <div v-else-if="tab === 'grades'" class="stack">
        <div v-if="gradesLoading" class="card sk-card">
          <span class="sk-line" style="width: 30%"></span>
          <span class="sk-line" style="width: 80%"></span>
          <span class="sk-line" style="width: 80%"></span>
        </div>

        <template v-else-if="grades && grades.assignments.length === 0">
          <div class="card muted" style="text-align: center; padding: 32px">
            Заданий в этом классе ещё нет — оценок тоже.
          </div>
        </template>

        <!-- Student view: my grades only -->
        <template v-else-if="grades && grades.viewer_role === 'student'">
          <div class="grades-summary">
            <div class="card stat">
              <div class="stat-label">Моя средняя</div>
              <div class="stat-value" style="color: var(--color-primary)">
                {{ grades.students[0]?.average ?? '—' }}
                <span v-if="grades.students[0]?.average" class="stat-sub-inline">из 100</span>
              </div>
              <div class="stat-sub">
                нормированное среднее по всем оценённым заданиям
              </div>
            </div>
          </div>

          <div class="card" style="padding: 0">
            <table class="cf-table">
              <thead>
                <tr>
                  <th>Задание</th>
                  <th>Шкала</th>
                  <th>Статус</th>
                  <th>Оценка</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="a in grades.assignments" :key="a.id">
                  <td class="td-strong">
                    <RouterLink :to="`/assignments/${a.id}`" class="link-quiet">
                      {{ a.name }}
                    </RouterLink>
                  </td>
                  <td class="muted">{{ a.grade_type }}</td>
                  <td>
                    <span
                      v-if="grades.students[0]?.grades[a.id]?.status"
                      class="badge"
                    >{{ gradeStatusLabel(grades.students[0].grades[a.id].status!) }}</span>
                    <span v-else class="muted">—</span>
                  </td>
                  <td class="td-grade">
                    {{ grades.students[0]?.grades[a.id]?.grade ?? '—' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>

        <!-- Teacher / admin view: full matrix -->
        <template v-else-if="grades && grades.viewer_role === 'teacher'">
          <div class="grades-summary">
            <div class="card stat">
              <div class="stat-label">Студентов</div>
              <div class="stat-value" style="color: var(--color-primary)">
                {{ visibleGradeStudents.length }}
              </div>
              <div class="stat-sub">учитываются в таблице</div>
            </div>
            <div class="card stat">
              <div class="stat-label">Средний балл по классу</div>
              <div class="stat-value">{{ grades.class_average ?? '—' }}</div>
              <div class="stat-sub">нормировано к шкале 0–100</div>
            </div>
          </div>

          <div class="grades-table-wrap card">
            <table class="cf-table grades-table">
              <thead>
                <tr>
                  <th class="col-student">Студент</th>
                  <th v-for="a in grades.assignments" :key="a.id" class="col-asn">
                    <RouterLink :to="`/assignments/${a.id}`" class="link-quiet">
                      {{ a.name }}
                    </RouterLink>
                    <div class="th-sub">{{ a.grade_type }}</div>
                  </th>
                  <th class="col-avg">Средняя</th>
                </tr>
              </thead>
              <tbody>
                <template v-for="s in visibleGradeStudents" :key="s.user_id">
                  <tr class="grades-row" @click="toggleStudentRow(s.user_id)">
                    <td class="td-strong col-student">
                      <span class="row-toggle">{{ gradesExpanded.has(s.user_id) ? '▾' : '▸' }}</span>
                      {{ s.username }}
                    </td>
                    <td
                      v-for="a in grades.assignments"
                      :key="a.id"
                      class="td-grade col-asn"
                    >
                      <span v-if="s.grades[a.id]?.grade">{{ s.grades[a.id].grade }}</span>
                      <span v-else class="muted">—</span>
                    </td>
                    <td class="td-grade td-avg col-avg">{{ s.average ?? '—' }}</td>
                  </tr>
                  <tr v-if="gradesExpanded.has(s.user_id)" class="grades-detail">
                    <td :colspan="grades.assignments.length + 2">
                      <div class="detail-grid">
                        <div
                          v-for="a in grades.assignments"
                          :key="a.id"
                          class="detail-cell"
                        >
                          <div class="detail-name">{{ a.name }}</div>
                          <div class="detail-meta">
                            <span class="muted">шкала {{ a.grade_type }}</span>
                            <span v-if="s.grades[a.id]?.status" class="badge">
                              {{ gradeStatusLabel(s.grades[a.id].status!) }}
                            </span>
                          </div>
                          <div class="detail-grade">
                            <RouterLink
                              v-if="s.grades[a.id]?.solution_id"
                              :to="`/solutions/${s.grades[a.id].solution_id}`"
                              class="link-quiet"
                            >Открыть решение →</RouterLink>
                            <span v-else class="muted">решение не создано</span>
                          </div>
                          <div class="detail-grade-value">
                            {{ s.grades[a.id]?.grade ?? '—' }}
                          </div>
                        </div>
                      </div>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
        </template>

        <div v-else class="card muted" style="text-align: center; padding: 32px">
          Не удалось загрузить оценки.
        </div>
      </div>

      <!-- Участники -->
      <div v-else-if="tab === 'members'">
        <div v-if="isTeacher" class="card invite-row" style="margin-bottom: 16px">
          <p class="muted" style="font-size: 14px; margin-bottom: 14px">
            Редактировать ленту, задания и материалы могут все преподаватели класса,
            а удалять класс может только преподаватель-создатель.
          </p>
          <div class="row" style="flex-wrap: wrap; gap: 10px">
            <input
              v-model="inviteEmail"
              placeholder="Email участника класса"
              style="max-width: 320px; flex: 1"
            />
            <button class="btn-primary" :disabled="inviteLoading" @click="onInvite">
              Пригласить преподавателем
            </button>
          </div>
          <div v-if="inviteError" class="error-text" style="margin-top: 10px">{{ inviteError }}</div>
          <div v-if="inviteSuccess" class="muted" style="margin-top: 10px; font-size: 14px">{{ inviteSuccess }}</div>
        </div>

        <div class="table-wrap">
          <table class="cf-table">
            <thead>
              <tr>
                <th>Пользователь</th>
                <th>Email</th>
                <th>Роль</th>
                <th>Присоединился</th>
                <th>Действие</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in members" :key="m.user_id">
                <td class="td-strong">{{ m.username }}</td>
                <td>{{ m.email }}</td>
                <td>
                  <span class="badge" :class="roleBadge(m.role)">{{ roleLabel(m.role) }}</span>
                </td>
                <td>{{ formatDate(m.joined_at) }}</td>
                <td>
                  <div class="row" style="gap: 6px; flex-wrap: wrap">
                    <button
                      v-if="canPromote(m)"
                      class="btn-soft"
                      style="font-size: 13px; padding: 7px 14px"
                      @click="onPromote(m)"
                    >Сделать преподом</button>
                    <button
                      v-if="canDemote(m)"
                      class="btn-soft"
                      style="font-size: 13px; padding: 7px 14px"
                      @click="onDemote(m)"
                    >Забрать преподство</button>
                    <button
                      v-if="canRemove(m)"
                      class="btn-soft"
                      style="font-size: 13px; padding: 7px 14px"
                      @click="onRemove(m)"
                    >Исключить</button>
                    <span v-if="!canPromote(m) && !canDemote(m) && !canRemove(m)" class="muted">—</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Материалы: учебные файлы и ссылки класса -->
      <div v-else-if="tab === 'materials'" class="stack">
        <div v-if="isTeacher" class="row" style="margin-bottom: 4px">
          <button class="btn-accent" @click="showNewMaterial = !showNewMaterial">
            Новый материал
          </button>
        </div>

        <NewMaterialForm
          v-if="showNewMaterial"
          :class-id="cls.id"
          @created="onMaterialCreated"
          @cancel="showNewMaterial = false"
        />

        <div v-if="materialsLoading" class="card sk-card">
          <span class="sk-line" style="width: 30%"></span>
          <span class="sk-line" style="width: 65%"></span>
        </div>
        <div v-else-if="materials.length === 0" class="card muted">
          Пока нет материалов. {{ isTeacher ? 'Добавьте файлы или ссылки для студентов.' : 'Преподаватель ещё не загрузил материалы.' }}
        </div>
        <div v-else class="stack">
          <MaterialCard
            v-for="m in materials"
            :key="m.id"
            :material="m"
            :is-teacher="isTeacher"
            :can-delete="isAdmin"
            @deleted="onMaterialDeleted"
            @updated="onMaterialUpdated"
          />
        </div>
      </div>

      <!-- Группы (для групповых заданий) -->
      <div v-else-if="tab === 'groups'" class="card muted">
        Группы появятся, когда создатель опубликует групповое задание.
      </div>
    </template>

    <!-- Modal: transfer ownership when admin demotes the class creator -->
    <div v-if="transferModal.open" class="modal-backdrop" @click.self="transferModal.open = false">
      <div class="modal-card">
        <div class="card-title">Передать класс</div>
        <p class="muted" style="font-size: 14px">
          Пользователь <b>{{ transferModal.target?.username }}</b> — создатель класса.
          Выберите, кто станет новым создателем. Студенты в списке не отображаются.
        </p>
        <div class="form-group" style="margin-top: 14px">
          <label>Новый создатель</label>
          <select v-model="transferModal.newCreatorId">
            <option value="">— выберите участника —</option>
            <option
              v-for="opt in transferCandidates"
              :key="opt.user_id"
              :value="opt.user_id"
            >{{ opt.username }} ({{ roleLabel(opt.role) }})</option>
          </select>
        </div>
        <div v-if="transferModal.error" class="error-text" style="margin-bottom: 12px">
          {{ transferModal.error }}
        </div>
        <div class="row" style="justify-content: flex-end; gap: 8px">
          <button class="btn-ghost" @click="transferModal.open = false">Отмена</button>
          <button
            class="btn-primary"
            :disabled="transferModal.loading || !transferModal.newCreatorId"
            @click="confirmTransfer"
          >{{ transferModal.loading ? 'Передаём…' : 'Передать и понизить' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  deleteClass,
  demoteMember,
  getClass,
  inviteTeacher,
  listMembers,
  promoteMember,
  regenerateInviteCode,
  removeMember,
  updateClass,
} from '@/shared/api/classes'
import { listAnnouncements } from '@/shared/api/announcements'
import { listAssignments } from '@/shared/api/assignments'
import { listMaterials } from '@/shared/api/materials'
import { extractError } from '@/shared/api/errors'
import { onNotification } from '@/shared/stores/notificationStore'
import { useAuthStore } from '@/shared/stores/authStore'
import { getClassGrades } from '@/shared/api/solutions'
import type {
  Announcement,
  Assignment,
  ClassDetail,
  ClassMember,
  GradesSummary,
  Material,
  MemberRole,
  SolutionStatus,
} from '@/shared/api/types'
import NewAnnouncementForm from '@/shared/ui/NewAnnouncementForm.vue'
import NewAssignmentForm from '@/shared/ui/NewAssignmentForm.vue'
import NewMaterialForm from '@/shared/ui/NewMaterialForm.vue'
import FeedItem from '@/shared/ui/FeedItem.vue'
import MaterialCard from '@/shared/ui/MaterialCard.vue'
import { useToast } from '@/shared/stores/toastStore'

const toast = useToast()

const FEED_EVENTS = new Set([
  'announcement_created', 'announcement_updated', 'announcement_deleted',
  'assignment_created', 'assignment_updated', 'assignment_deleted',
])
const MATERIAL_EVENTS = new Set([
  'material_created', 'material_updated', 'material_deleted',
])
const unsub = onNotification((n) => {
  const p = n.payload as Record<string, string>
  if (!cls.value) return
  if (p.class_id !== cls.value.id) return
  if (FEED_EVENTS.has(n.type)) {
    void loadFeed()
  } else if (MATERIAL_EVENTS.has(n.type)) {
    void loadMaterials()
  }
})
onBeforeUnmount(() => unsub())

interface FeedEntry {
  kind: 'announcement' | 'assignment'
  id: string
  created_at: string
  data: Announcement | Assignment
}

const route = useRoute()
const router = useRouter()

const cls = ref<ClassDetail | null>(null)
const loading = ref(true)
const tab = ref<'feed' | 'materials' | 'members' | 'groups' | 'grades'>('feed')

const baseTabs = [
  { id: 'feed' as const, label: 'Лента' },
  { id: 'materials' as const, label: 'Материалы' },
  { id: 'grades' as const, label: 'Оценки' },
  { id: 'members' as const, label: 'Участники' },
  { id: 'groups' as const, label: 'Группы' },
]
const tabs = computed(() =>
  baseTabs.filter((t) => t.id !== 'grades' || cls.value?.my_role === 'student'),
)

const announcements = ref<Announcement[]>([])
const assignments = ref<Assignment[]>([])
const feedLoading = ref(false)
const showNewAnn = ref(false)
const showNewAsn = ref(false)

const materials = ref<Material[]>([])
const materialsLoading = ref(false)
const materialsLoaded = ref(false)
const showNewMaterial = ref(false)

const grades = ref<GradesSummary | null>(null)
const gradesLoading = ref(false)
const gradesExpanded = ref<Set<string>>(new Set())

const members = ref<ClassMember[]>([])
const inviteEmail = ref('')
const inviteError = ref('')
const inviteSuccess = ref('')
const inviteLoading = ref(false)

const showRename = ref(false)
const renameValue = ref('')
const regenLoading = ref(false)

const isTeacher = computed(
  () => cls.value?.my_role === 'teacher_creator' || cls.value?.my_role === 'teacher',
)

const auth = useAuthStore()
const isAdmin = computed(() => auth.user?.is_admin === true)

const feed = computed<FeedEntry[]>(() => {
  const items: FeedEntry[] = [
    ...announcements.value.map((a) => ({
      kind: 'announcement' as const,
      id: a.id,
      created_at: a.created_at,
      data: a,
    })),
    ...assignments.value.map((a) => ({
      kind: 'assignment' as const,
      id: a.id,
      created_at: a.created_at,
      data: a,
    })),
  ]
  return items.sort((x, y) => y.created_at.localeCompare(x.created_at))
})

async function loadClass() {
  const id = String(route.params.id)
  loading.value = true
  try {
    cls.value = await getClass(id)
    renameValue.value = cls.value.name
  } catch {
    cls.value = null
  } finally {
    loading.value = false
  }
}

async function loadFeed() {
  if (!cls.value) return
  feedLoading.value = true
  try {
    const [ann, asn] = await Promise.all([
      listAnnouncements(cls.value.id),
      listAssignments(cls.value.id),
    ])
    announcements.value = ann
    assignments.value = asn
  } finally {
    feedLoading.value = false
  }
}

async function loadMembers() {
  if (!cls.value) return
  members.value = await listMembers(cls.value.id)
}

async function loadMaterials() {
  if (!cls.value) return
  materialsLoading.value = true
  try {
    materials.value = await listMaterials(cls.value.id)
    materialsLoaded.value = true
  } finally {
    materialsLoading.value = false
  }
}

async function loadGrades() {
  if (!cls.value) return
  gradesLoading.value = true
  try {
    grades.value = await getClassGrades(cls.value.id)
  } catch {
    grades.value = null
  } finally {
    gradesLoading.value = false
  }
}

/** Defense-in-depth: even if the API ever returned other students to a
 * student-role viewer, the UI still only shows the student's own row. */
const visibleGradeStudents = computed(() => {
  const all = grades.value?.students ?? []
  if (cls.value?.my_role === 'student') {
    return all.filter((s) => s.user_id === auth.user?.id)
  }
  return all
})

function toggleStudentRow(userId: string) {
  const next = new Set(gradesExpanded.value)
  if (next.has(userId)) {
    next.delete(userId)
  } else {
    next.add(userId)
  }
  gradesExpanded.value = next
}

function gradeStatusLabel(s: SolutionStatus): string {
  switch (s) {
    case 'created':
      return 'черновик'
    case 'submitted':
      return 'сдано'
    case 'returned':
      return 'возвращено'
    case 'pending_redistribution':
      return 'распределение'
    case 'graded':
      return 'оценено'
  }
}

watch(tab, (t) => {
  if (t === 'members') void loadMembers()
  if (t === 'materials' && !materialsLoaded.value) void loadMaterials()
  if (t === 'grades') void loadGrades()
})

// If the active tab disappears (e.g. teacher had Grades open before refresh),
// fall back to feed.
watch(tabs, (list) => {
  if (!list.some((t) => t.id === tab.value)) tab.value = 'feed'
})

function onAnnouncementCreated(a: Announcement) {
  announcements.value = [a, ...announcements.value]
  showNewAnn.value = false
}

function onAssignmentCreated(a: Assignment) {
  assignments.value = [a, ...assignments.value]
  showNewAsn.value = false
}

function onFeedItemDeleted(kind: 'announcement' | 'assignment', id: string) {
  if (kind === 'announcement') {
    announcements.value = announcements.value.filter((x) => x.id !== id)
  } else {
    assignments.value = assignments.value.filter((x) => x.id !== id)
  }
}

function onFeedItemUpdated(kind: 'announcement' | 'assignment', data: Announcement | Assignment) {
  if (kind === 'announcement') {
    const updated = data as Announcement
    announcements.value = announcements.value.map((x) => (x.id === updated.id ? updated : x))
  } else {
    const updated = data as Assignment
    assignments.value = assignments.value.map((x) => (x.id === updated.id ? updated : x))
  }
}

function onMaterialCreated(m: Material) {
  materials.value = [m, ...materials.value]
  showNewMaterial.value = false
}

function onMaterialDeleted(id: string) {
  materials.value = materials.value.filter((x) => x.id !== id)
}

function onMaterialUpdated(data: Material) {
  materials.value = materials.value.map((x) => (x.id === data.id ? data : x))
}

async function copyInvite() {
  if (!cls.value?.invite_code) return
  const code = cls.value.invite_code
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(code)
    } else {
      const ta = document.createElement('textarea')
      ta.value = code
      ta.style.position = 'fixed'
      ta.style.opacity = '0'
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
    }
    toast.success(`Код ${code} скопирован`)
  } catch {
    toast.error('Не удалось скопировать код')
  }
}

async function onRegenerateInvite() {
  if (!cls.value) return
  if (!confirm('Сгенерировать новый invite-код? Старый сразу перестанет работать.')) return
  regenLoading.value = true
  try {
    cls.value = await regenerateInviteCode(cls.value.id)
    toast.success(`Новый код: ${cls.value.invite_code ?? '—'}`)
  } catch (e) {
    toast.error(extractError(e))
  } finally {
    regenLoading.value = false
  }
}

async function onRename() {
  if (!cls.value) return
  const name = renameValue.value.trim()
  if (name.length < 2) return
  try {
    cls.value = await updateClass(cls.value.id, { name })
    showRename.value = false
  } catch (e) {
    toast.error(extractError(e))
  }
}

async function onDelete() {
  if (!cls.value) return
  if (!confirm('Удалить класс? Это действие нельзя отменить.')) return
  try {
    await deleteClass(cls.value.id)
    await router.push('/')
  } catch (e) {
    toast.error(extractError(e))
  }
}

async function onInvite() {
  if (!cls.value) return
  inviteError.value = ''
  inviteSuccess.value = ''
  inviteLoading.value = true
  try {
    const m = await inviteTeacher(cls.value.id, inviteEmail.value.trim())
    inviteSuccess.value = `${m.username} теперь преподаватель`
    inviteEmail.value = ''
    await loadMembers()
  } catch (e) {
    inviteError.value = extractError(e)
  } finally {
    inviteLoading.value = false
  }
}

function canRemove(m: ClassMember): boolean {
  if (!cls.value || m.role === 'teacher_creator') return false
  if (cls.value.my_role === 'teacher_creator') return true
  if (cls.value.my_role === 'teacher' && m.role === 'student') return true
  if (isAdmin.value) return true
  return false
}

/** "Make this member a teacher" — only for students, by creator or admin. */
function canPromote(m: ClassMember): boolean {
  if (!cls.value || m.role !== 'student') return false
  return cls.value.my_role === 'teacher_creator' || isAdmin.value
}

/** "Take teaching rights away from this member" — both teachers and the
 * creator (the creator case is admin-only and goes through transfer modal). */
function canDemote(m: ClassMember): boolean {
  if (!cls.value) return false
  if (m.role === 'teacher') {
    return cls.value.my_role === 'teacher_creator' || isAdmin.value
  }
  if (m.role === 'teacher_creator') {
    return isAdmin.value && m.user_id !== auth.user?.id
  }
  return false
}

const transferModal = ref<{
  open: boolean
  target: ClassMember | null
  newCreatorId: string
  loading: boolean
  error: string
}>({
  open: false,
  target: null,
  newCreatorId: '',
  loading: false,
  error: '',
})

const transferCandidates = computed<ClassMember[]>(() =>
  members.value.filter(
    (m) =>
      (m.role === 'teacher' || m.role === 'teacher_creator') &&
      m.user_id !== transferModal.value.target?.user_id,
  ),
)

async function onPromote(m: ClassMember) {
  if (!cls.value) return
  if (!confirm(`Сделать ${m.username} преподавателем класса?`)) return
  try {
    await promoteMember(cls.value.id, m.user_id)
    toast.success(`${m.username} теперь преподаватель`)
    await loadMembers()
  } catch (e) {
    toast.error(extractError(e))
  }
}

async function onDemote(m: ClassMember) {
  if (!cls.value) return
  if (m.role === 'teacher_creator') {
    transferModal.value = {
      open: true,
      target: m,
      newCreatorId: '',
      loading: false,
      error: '',
    }
    return
  }
  if (!confirm(`Забрать преподство у ${m.username}? Он станет студентом.`)) return
  try {
    await demoteMember(cls.value.id, m.user_id)
    toast.success(`${m.username} теперь студент`)
    await loadMembers()
  } catch (e) {
    toast.error(extractError(e))
  }
}

async function confirmTransfer() {
  if (!cls.value || !transferModal.value.target || !transferModal.value.newCreatorId) return
  transferModal.value.loading = true
  transferModal.value.error = ''
  try {
    await demoteMember(
      cls.value.id,
      transferModal.value.target.user_id,
      transferModal.value.newCreatorId,
    )
    toast.success('Класс передан, бывший создатель — студент')
    transferModal.value.open = false
    await Promise.all([loadClass(), loadMembers()])
  } catch (e) {
    transferModal.value.error = extractError(e)
  } finally {
    transferModal.value.loading = false
  }
}

async function onRemove(m: ClassMember) {
  if (!cls.value) return
  if (!confirm(`Исключить ${m.username} из класса?`)) return
  try {
    await removeMember(cls.value.id, m.user_id)
    await loadMembers()
  } catch (e) {
    toast.error(extractError(e))
  }
}

function roleLabel(r: MemberRole): string {
  if (r === 'teacher_creator') return 'создатель'
  if (r === 'teacher') return 'преподаватель'
  return 'студент'
}

function roleBadge(r: MemberRole): string {
  if (r === 'teacher_creator') return 'badge-creator'
  if (r === 'teacher') return 'badge-teacher'
  return 'badge-student'
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
  } catch {
    return iso
  }
}

onMounted(async () => {
  await loadClass()
  if (cls.value) await loadFeed()
})
</script>

<style scoped>
.td-strong { font-weight: 800; }
.invite-row p { color: var(--color-text-muted); }

.invite-badge {
  cursor: copy;
  user-select: all;
  transition: filter var(--dur-fast) var(--ease-out);
}
.invite-badge:hover { filter: brightness(0.95); }

.invite-refresh {
  cursor: pointer;
  background: transparent;
  border: 1px solid var(--color-border-strong);
  color: var(--color-text-muted);
  font-family: inherit;
  font-size: inherit;
  transition: background var(--dur-fast) var(--ease-out),
              color var(--dur-fast) var(--ease-out);
}
.invite-refresh:hover:not(:disabled) {
  background: var(--color-bg-2);
  color: var(--color-text);
}
.invite-refresh:disabled { opacity: 0.6; cursor: progress; }

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 16px;
}
.modal-card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: 24px;
  max-width: 480px;
  width: 100%;
  box-shadow: var(--shadow-lg);
}
.card-title {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin-bottom: 8px;
}

.grades-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 18px;
}
.stat-sub-inline {
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-muted);
  margin-left: 6px;
}
.th-sub {
  margin-top: 4px;
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: lowercase;
  color: var(--color-text-subtle);
}
.td-grade {
  text-align: center;
  font-weight: 800;
  font-family: var(--font-display);
}
.td-avg {
  background: var(--color-bg-2);
  color: var(--color-primary);
}

/* Horizontally scrollable matrix with sticky first/last column. */
.grades-table-wrap {
  padding: 0;
  overflow-x: auto;
  overflow-y: visible;
  max-width: 100%;
  -webkit-overflow-scrolling: touch;
}
.grades-table { min-width: 100%; border-collapse: separate; border-spacing: 0; }
.grades-table th,
.grades-table td { white-space: nowrap; }

.grades-table .col-student {
  position: sticky;
  left: 0;
  z-index: 2;
  background: var(--color-surface);
  min-width: 180px;
  box-shadow: 1px 0 0 var(--color-border);
}
.grades-table thead .col-student {
  background: var(--color-bg-2);
  z-index: 3;
}
.grades-table .col-asn { min-width: 120px; text-align: center; }
.grades-table .col-avg {
  position: sticky;
  right: 0;
  z-index: 2;
  background: var(--color-bg-2);
  min-width: 110px;
  box-shadow: -1px 0 0 var(--color-border);
}
.grades-table thead .col-avg { z-index: 3; }
.grades-row:hover .col-student,
.grades-row:hover .col-avg {
  background: var(--color-bg-2);
  filter: brightness(0.98);
}
.grades-row { cursor: pointer; transition: background var(--dur-fast) var(--ease-out); }
.grades-row:hover { background: var(--color-bg-2); }
.row-toggle {
  display: inline-block;
  width: 14px;
  color: var(--color-text-muted);
  font-weight: 700;
  margin-right: 4px;
}
.grades-detail td {
  background: var(--color-bg-2);
  padding: 16px 18px;
}
.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}
.detail-cell {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 12px 14px;
  display: grid;
  grid-template-rows: auto auto auto auto;
  gap: 4px;
}
.detail-name { font-weight: 800; font-size: 14px; }
.detail-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}
.detail-grade { font-size: 12px; }
.detail-grade-value {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 800;
  color: var(--color-primary);
  text-align: right;
}
.link-quiet { color: inherit; }
.link-quiet:hover { color: var(--color-primary); text-decoration: none; }
</style>
