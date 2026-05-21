<template>
  <div class="container page">
    <div v-if="loading" class="card muted">Загрузка…</div>
    <div v-else-if="!cls" class="card muted">Класс не найден</div>
    <template v-else>
      <div class="row-between" style="margin-bottom: 16px">
        <div>
          <h1 class="page-title" style="margin: 0">{{ cls.name }}</h1>
          <div class="row" style="margin-top: 4px">
            <span class="tag" :class="cls.type === 'open' ? 'tag-info' : 'tag-warning'">
              {{ cls.type === 'open' ? 'открытый' : 'закрытый' }}
            </span>
            <span v-if="cls.my_role" class="tag tag-success">{{ roleLabel(cls.my_role) }}</span>
            <span v-if="cls.invite_code" class="tag">код: {{ cls.invite_code }}</span>
          </div>
        </div>
        <div class="row">
          <RouterLink v-if="isTeacher" :to="`/classes/${cls.id}/grades`" class="btn-secondary">
            Оценки
          </RouterLink>
          <button v-if="isTeacher" class="btn-secondary" @click="showRename = !showRename">
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

      <div v-if="showRename" class="card" style="margin-bottom: 16px">
        <div class="row" style="gap: 8px">
          <input v-model="renameValue" :placeholder="cls.name" />
          <button class="btn-primary" @click="onRename">Сохранить</button>
          <button class="btn-secondary" @click="showRename = false">Отмена</button>
        </div>
      </div>

      <div class="tabs">
        <button
          v-for="t in tabs"
          :key="t.id"
          class="tab"
          :class="{ active: tab === t.id }"
          @click="tab = t.id"
        >{{ t.label }}</button>
      </div>

      <!-- Лента: объявления + задания -->
      <div v-if="tab === 'feed'" class="stack">
        <div v-if="isTeacher" class="row" style="margin-bottom: 8px">
          <button class="btn-primary" @click="showNewAnn = !showNewAnn">+ Объявление</button>
          <button class="btn-primary" @click="showNewAsn = !showNewAsn">+ Задание</button>
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

        <div v-if="feedLoading" class="card muted">Загрузка…</div>
        <div v-else-if="feed.length === 0" class="card muted">Пока ничего не опубликовано</div>
        <div v-else class="stack">
          <FeedItem
            v-for="item in feed"
            :key="`${item.kind}-${item.id}`"
            :item="item"
            :is-teacher="isTeacher"
            @deleted="onFeedItemDeleted"
            @updated="onFeedItemUpdated"
          />
        </div>
      </div>

      <!-- Участники -->
      <div v-else-if="tab === 'members'" class="card">
        <div v-if="isTeacher" class="row" style="margin-bottom: 12px">
          <input
            v-model="inviteEmail"
            placeholder="Email участника класса"
            style="max-width: 320px"
          />
          <button class="btn-primary" :disabled="inviteLoading" @click="onInvite">
            Назначить преподавателем
          </button>
          <span v-if="inviteError" class="error-text">{{ inviteError }}</span>
          <span v-if="inviteSuccess" class="muted">{{ inviteSuccess }}</span>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>Имя</th>
              <th>Email</th>
              <th>Роль</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in members" :key="m.user_id">
              <td>{{ m.username }}</td>
              <td>{{ m.email }}</td>
              <td>
                <span class="tag" :class="roleTag(m.role)">{{ roleLabel(m.role) }}</span>
              </td>
              <td>
                <button
                  v-if="canRemove(m)"
                  class="btn-secondary"
                  style="font-size: 12px; padding: 4px 8px"
                  @click="onRemove(m)"
                >Исключить</button>
              </td>
            </tr>
          </tbody>
        </table>
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
import { extractError } from '@/shared/api/errors'
import { onNotification } from '@/shared/stores/notificationStore'
import type {
  Announcement,
  Assignment,
  ClassDetail,
  ClassMember,
  MemberRole,
} from '@/shared/api/types'
import NewAnnouncementForm from '@/shared/ui/NewAnnouncementForm.vue'
import NewAssignmentForm from '@/shared/ui/NewAssignmentForm.vue'
import FeedItem from '@/shared/ui/FeedItem.vue'

const FEED_EVENTS = new Set([
  'announcement_created', 'announcement_updated', 'announcement_deleted',
  'assignment_created', 'assignment_updated', 'assignment_deleted',
])
const unsub = onNotification((n) => {
  const p = n.payload as Record<string, string>
  if (!cls.value) return
  if (p.class_id === cls.value.id && FEED_EVENTS.has(n.type)) {
    void loadFeed()
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
const tab = ref<'feed' | 'members'>('feed')

const tabs = [
  { id: 'feed' as const, label: 'Лента' },
  { id: 'members' as const, label: 'Участники' },
]

const announcements = ref<Announcement[]>([])
const assignments = ref<Assignment[]>([])
const feedLoading = ref(false)
const showNewAnn = ref(false)
const showNewAsn = ref(false)

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

watch(tab, (t) => {
  if (t === 'members') void loadMembers()
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

async function onRename() {
  if (!cls.value) return
  const name = renameValue.value.trim()
  if (name.length < 2) return
  try {
    cls.value = await updateClass(cls.value.id, { name })
    showRename.value = false
  } catch (e) {
    alert(extractError(e))
  }
}

async function onDelete() {
  if (!cls.value) return
  if (!confirm('Удалить класс? Это действие нельзя отменить.')) return
  try {
    await deleteClass(cls.value.id)
    await router.push('/')
  } catch (e) {
    alert(extractError(e))
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
    alert(extractError(e))
  }
}

function roleLabel(r: MemberRole): string {
  if (r === 'teacher_creator') return 'создатель'
  if (r === 'teacher') return 'преподаватель'
  return 'студент'
}

function roleTag(r: MemberRole): string {
  if (r === 'teacher_creator') return 'tag-success'
  if (r === 'teacher') return 'tag-info'
  return ''
}

onMounted(async () => {
  await loadClass()
  if (cls.value) await loadFeed()
})
</script>

<style scoped>
.tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: 16px;
}
.tab {
  background: transparent;
  border: none;
  padding: 10px 16px;
  color: var(--color-text-muted);
  font-size: 14px;
  border-bottom: 2px solid transparent;
  border-radius: 0;
}
.tab.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}
</style>
