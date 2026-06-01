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
            <span v-if="cls.invite_code" class="badge">код: {{ cls.invite_code }}</span>
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
                  <button
                    v-if="canRemove(m)"
                    class="btn-soft"
                    style="font-size: 13px; padding: 7px 14px"
                    @click="onRemove(m)"
                  >Исключить</button>
                  <span v-else class="muted">—</span>
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
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  deleteClass,
  getClass,
  inviteTeacher,
  listMembers,
  removeMember,
  updateClass,
} from '@/shared/api/classes'
import { listAnnouncements } from '@/shared/api/announcements'
import { listAssignments } from '@/shared/api/assignments'
import { listMaterials } from '@/shared/api/materials'
import { extractError } from '@/shared/api/errors'
import { onNotification } from '@/shared/stores/notificationStore'
import { useAuthStore } from '@/shared/stores/authStore'
import type {
  Announcement,
  Assignment,
  ClassDetail,
  ClassMember,
  Material,
  MemberRole,
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
const tab = ref<'feed' | 'materials' | 'members' | 'groups'>('feed')

const tabs = [
  { id: 'feed' as const, label: 'Лента' },
  { id: 'materials' as const, label: 'Материалы' },
  { id: 'members' as const, label: 'Участники' },
  { id: 'groups' as const, label: 'Группы' },
]

const announcements = ref<Announcement[]>([])
const assignments = ref<Assignment[]>([])
const feedLoading = ref(false)
const showNewAnn = ref(false)
const showNewAsn = ref(false)

const materials = ref<Material[]>([])
const materialsLoading = ref(false)
const materialsLoaded = ref(false)
const showNewMaterial = ref(false)

const members = ref<ClassMember[]>([])
const inviteEmail = ref('')
const inviteError = ref('')
const inviteSuccess = ref('')
const inviteLoading = ref(false)

const showRename = ref(false)
const renameValue = ref('')

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

watch(tab, (t) => {
  if (t === 'members') void loadMembers()
  if (t === 'materials' && !materialsLoaded.value) void loadMaterials()
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
  return false
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
</style>
