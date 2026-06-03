<template>
  <div class="container page">
    <div class="title-kicker">Администрирование</div>
    <h1 class="page-title">Управление платформой</h1>
    <div class="title-line"></div>

    <div class="tabbar">
      <button
        v-for="t in tabs"
        :key="t.id"
        class="tab"
        :class="{ on: tab === t.id }"
        @click="tab = t.id"
      >{{ t.label }}</button>
    </div>

    <!-- USERS -->
    <div v-if="tab === 'users'">
      <div class="card filter-card">
        <input
          v-model="userSearch"
          class="filter-search"
          placeholder="Поиск по email или username"
          @keyup.enter="loadUsers"
        />
        <label class="check">
          <input type="checkbox" v-model="includeDeletedUsers" @change="loadUsers" />
          включая заблокированных
        </label>
        <button class="btn-primary" @click="loadUsers">Найти</button>
      </div>

      <div v-if="usersLoading" class="card sk-card">
        <span class="sk-line" style="width: 70%"></span>
        <span class="sk-line" style="width: 70%"></span>
        <span class="sk-line" style="width: 70%"></span>
      </div>
      <div v-else class="table-wrap">
        <table class="cf-table">
          <thead>
            <tr>
              <th>Пользователь</th>
              <th>Email</th>
              <th>Статус</th>
              <th>Создан</th>
              <th>Действие</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td class="td-strong">
                {{ u.username }}
                <span v-if="u.is_admin" class="badge badge-admin" style="margin-left: 6px">admin</span>
              </td>
              <td>{{ u.email }}</td>
              <td>
                <span v-if="u.deleted_at" class="badge badge-block">заблокирован</span>
                <span v-else class="badge badge-active">активен</span>
              </td>
              <td>{{ formatDate(u.created_at) }}</td>
              <td>
                <div class="row-actions">
                  <button
                    v-if="!u.deleted_at"
                    class="btn-soft action-btn"
                    @click="onBlock(u)"
                  >Заблокировать</button>
                  <button
                    v-else
                    class="btn-primary action-btn"
                    @click="onUnblock(u)"
                  >Разблокировать</button>
                  <button
                    v-if="canDelete(u)"
                    class="btn-danger action-btn"
                    @click="onDeleteUser(u)"
                  >Удалить</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- CLASSES -->
    <div v-else-if="tab === 'classes'">
      <div class="card filter-card">
        <input
          v-model="classSearch"
          class="filter-search"
          placeholder="Поиск по названию класса"
          @keyup.enter="loadClasses"
        />
        <label class="check">
          <input type="checkbox" v-model="includeDeletedClasses" @change="loadClasses" />
          включая удалённые
        </label>
        <button class="btn-primary" @click="loadClasses">Найти</button>
      </div>

      <div v-if="classesLoading" class="card sk-card">
        <span class="sk-line" style="width: 70%"></span>
        <span class="sk-line" style="width: 70%"></span>
      </div>
      <div v-else class="table-wrap">
        <table class="cf-table">
          <thead>
            <tr>
              <th>Название</th>
              <th>Тип</th>
              <th>Создатель</th>
              <th>Участников</th>
              <th>Статус</th>
              <th>Действие</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in classes" :key="c.id">
              <td class="td-strong">{{ c.name }}</td>
              <td>
                <span class="badge" :class="c.type === 'open' ? 'badge-open' : 'badge-closed'">
                  {{ c.type === 'open' ? 'открытый' : 'закрытый' }}
                </span>
              </td>
              <td>{{ c.creator_username }}</td>
              <td>{{ c.member_count }}</td>
              <td>
                <span v-if="c.deleted_at" class="badge badge-block">удалён</span>
                <span v-else class="badge badge-active">активен</span>
              </td>
              <td>
                <button
                  v-if="!c.deleted_at"
                  class="btn-soft"
                  style="font-size: 13px; padding: 7px 14px"
                  @click="onDeleteClass(c)"
                >Удалить</button>
                <span v-else class="muted">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- STATS -->
    <div v-else-if="tab === 'stats'">
      <div v-if="statsLoading" class="card sk-card">
        <span class="sk-line" style="width: 70%"></span>
        <span class="sk-line" style="width: 70%"></span>
      </div>
      <div v-else-if="stats" class="stat-grid stat-grid-4">
        <div class="stat">
          <div class="stat-label">Пользователи</div>
          <div class="stat-value" style="color: var(--color-primary)">{{ stats.users_active }}</div>
          <div class="stat-sub">всего {{ stats.users_total }}</div>
        </div>
        <div class="stat">
          <div class="stat-label">Классы</div>
          <div class="stat-value" style="color: var(--color-accent-hover)">{{ stats.classes_active }}</div>
          <div class="stat-sub">всего {{ stats.classes_total }}</div>
        </div>
        <div class="stat">
          <div class="stat-label">Решения</div>
          <div class="stat-value">{{ stats.solutions_total }}</div>
          <div class="stat-sub">отправлено за всё время</div>
        </div>
        <div class="stat">
          <div class="stat-label">Файлы</div>
          <div class="stat-value">{{ formatBytes(stats.file_bytes) }}</div>
          <div class="stat-sub">занято в хранилище</div>
        </div>
      </div>
    </div>

    <!-- Transfer-classes modal: triggered when DELETE returns 409 USER_HAS_CONTENT -->
    <Teleport to="body">
      <div v-if="transferModal" class="overlay" @click.self="closeTransferModal">
        <div class="modal">
          <div class="modal-title">Удаление пользователя</div>
          <p class="modal-sub">
            <template v-if="transferModal.classes.length > 0">
              У пользователя <strong>{{ transferModal.user.username }}</strong>
              ещё есть {{ transferModal.classes.length }} {{ pluralClasses(transferModal.classes.length) }} как создатель.
              Передайте каждый другому пользователю или удалите — после этого аккаунт будет удалён.
            </template>
            <template v-else>
              У пользователя <strong>{{ transferModal.user.username }}</strong>
              нет классов как создатель, но числится контент. Удалите его, чтобы стереть аккаунт.
            </template>
          </p>

          <!-- «Назначить все одному» — массовое заполнение -->
          <div v-if="transferModal.classes.length > 1" class="bulk-row">
            <span class="bulk-label">Назначить все классы одному:</span>
            <select v-model="bulkTarget" class="transfer-select">
              <option value="">— выбрать получателя —</option>
              <option
                v-for="u in transferCandidates"
                :key="u.id"
                :value="u.id"
              >{{ u.username }} ({{ u.email }})</option>
            </select>
            <button class="btn-ghost bulk-apply" :disabled="!bulkTarget" @click="applyBulkTarget">
              Применить ко всем
            </button>
          </div>

          <div v-if="transferModal.classes.length > 0" class="transfer-list">
            <div
              v-for="cls in transferModal.classes"
              :key="cls.id"
              class="transfer-row"
              :class="{ 'will-delete': transferModal.choices[cls.id] === DELETE_CHOICE }"
            >
              <div class="transfer-class-name">{{ cls.name }}</div>
              <select v-model="transferModal.choices[cls.id]" class="transfer-select">
                <option value="">— выберите действие —</option>
                <optgroup label="Передать преподавателю">
                  <option
                    v-for="u in transferCandidates"
                    :key="u.id"
                    :value="u.id"
                  >{{ u.username }} ({{ u.email }})</option>
                </optgroup>
                <option :value="DELETE_CHOICE">🗑  Удалить класс</option>
              </select>
            </div>
          </div>

          <!-- Контент (объявления/задания/решения), который transfer не покрывает -->
          <div v-if="transferModal.extra" class="extra-warning">
            <div style="margin-bottom: 10px">
              Также числится контент: {{ transferModal.extra }}. Передача классов его не затрагивает.
            </div>
            <label class="force-check">
              <input type="checkbox" v-model="forceWipe" />
              удалить весь контент пользователя
            </label>
          </div>

          <div class="row" style="margin-top: 20px; justify-content: flex-end; gap: 10px">
            <button class="btn-ghost" :disabled="transferBusy" @click="closeTransferModal">Отмена</button>
            <button
              class="btn-danger"
              :disabled="!canConfirm || transferBusy"
              @click="onConfirmTransferAndDelete"
            >
              {{ transferBusy ? 'Выполняем…' : confirmLabel }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { AxiosError } from 'axios'
import * as adminApi from '@/shared/api/admin'
import type { AdminClass, AdminStats, AdminUser } from '@/shared/api/types'
import { extractError } from '@/shared/api/errors'
import { useToast } from '@/shared/stores/toastStore'
import { useAuthStore } from '@/shared/stores/authStore'

const toast = useToast()
const auth = useAuthStore()

/** Sentinel value in the per-class dropdown meaning "delete this class
 *  instead of transferring it". */
const DELETE_CHOICE = '__delete__'

interface TransferModalState {
  user: AdminUser
  classes: { id: string; name: string }[]
  choices: Record<string, string>  // class_id -> new_creator_id OR DELETE_CHOICE
  extra: string | null  // "3 заданий, 5 решений" if non-class content exists
}
const transferModal = ref<TransferModalState | null>(null)
const transferBusy = ref(false)
const bulkTarget = ref('')   // chosen recipient for "assign all classes to one"
const forceWipe = ref(false) // wipe non-class content (announcements/assignments/solutions)

/** All non-admin, non-blocked users except the target — eligible to receive a class. */
const transferCandidates = computed(() => {
  const target = transferModal.value?.user.id
  return users.value.filter(
    (u) => u.id !== target && !u.deleted_at && !u.is_admin,
  )
})

/** Fill every class choice with the bulk-selected recipient. */
function applyBulkTarget() {
  const m = transferModal.value
  if (!m || !bulkTarget.value) return
  for (const c of m.classes) m.choices[c.id] = bulkTarget.value
}

const canConfirm = computed(() => {
  const m = transferModal.value
  if (!m) return false
  // Every class must have a chosen action.
  const classesReady = m.classes.every((c) => !!m.choices[c.id])
  // If extra content exists, the admin must tick the wipe checkbox.
  const contentReady = !m.extra || forceWipe.value
  return classesReady && contentReady
})

/** Button label adapts to the selected actions. */
const confirmLabel = computed(() => {
  const m = transferModal.value
  if (!m) return 'Удалить'
  if (m.classes.length === 0) return 'Удалить контент и пользователя'
  const all = m.classes.map((c) => m.choices[c.id])
  if (all.every((v) => v === DELETE_CHOICE)) return 'Удалить классы и пользователя'
  if (all.every((v) => v && v !== DELETE_CHOICE)) return 'Передать все и удалить'
  return 'Применить и удалить'
})

function pluralClasses(n: number): string {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return 'класс'
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return 'класса'
  return 'классов'
}

function canDelete(u: AdminUser): boolean {
  if (u.is_admin) return false
  if (u.id === auth.user?.id) return false
  return true
}

function closeTransferModal() {
  if (transferBusy.value) return
  transferModal.value = null
}

const tab = ref<'users' | 'classes' | 'stats'>('users')
const tabs = [
  { id: 'users' as const, label: 'Пользователи' },
  { id: 'classes' as const, label: 'Классы' },
  { id: 'stats' as const, label: 'Статистика' },
]

const users = ref<AdminUser[]>([])
const usersLoading = ref(false)
const userSearch = ref('')
const includeDeletedUsers = ref(true)

const classes = ref<AdminClass[]>([])
const classesLoading = ref(false)
const classSearch = ref('')
const includeDeletedClasses = ref(true)

const stats = ref<AdminStats | null>(null)
const statsLoading = ref(false)

async function loadUsers() {
  usersLoading.value = true
  try {
    const res = await adminApi.listUsers({
      search: userSearch.value || undefined,
      include_deleted: includeDeletedUsers.value,
      page: 1,
      page_size: 100,
    })
    users.value = res.items
  } finally {
    usersLoading.value = false
  }
}

async function loadClasses() {
  classesLoading.value = true
  try {
    const res = await adminApi.listClasses({
      search: classSearch.value || undefined,
      include_deleted: includeDeletedClasses.value,
      page: 1,
      page_size: 100,
    })
    classes.value = res.items
  } finally {
    classesLoading.value = false
  }
}

async function loadStats() {
  statsLoading.value = true
  try {
    stats.value = await adminApi.getStats()
  } finally {
    statsLoading.value = false
  }
}

async function onBlock(u: AdminUser) {
  if (!confirm(`Заблокировать ${u.username}?`)) return
  try {
    await adminApi.blockUser(u.id)
    await loadUsers()
  } catch (e) {
    toast.error(extractError(e))
  }
}

async function onUnblock(u: AdminUser) {
  try {
    await adminApi.unblockUser(u.id)
    await loadUsers()
  } catch (e) {
    toast.error(extractError(e))
  }
}

async function onDeleteClass(c: AdminClass) {
  if (!confirm(`Удалить класс «${c.name}»?`)) return
  try {
    await adminApi.deleteClass(c.id)
    await loadClasses()
  } catch (e) {
    toast.error(extractError(e))
  }
}

async function onDeleteUser(u: AdminUser) {
  if (!confirm(`Удалить пользователя ${u.username} безвозвратно?`)) return
  try {
    await adminApi.deleteUser(u.id)
    toast.success(`Пользователь ${u.username} удалён`)
    await loadUsers()
  } catch (e) {
    // 409 with classes_owned — open the transfer modal.
    if (e instanceof AxiosError && e.response?.status === 409) {
      const detail = e.response.data?.detail
      const d = detail?.details
      if (d && Array.isArray(d.classes_owned)) {
        const choices: Record<string, string> = {}
        for (const c of d.classes_owned) choices[c.id] = ''
        const extras: string[] = []
        if (d.announcements > 0) extras.push(`${d.announcements} объявлений`)
        if (d.assignments > 0) extras.push(`${d.assignments} заданий`)
        if (d.solutions > 0) extras.push(`${d.solutions} решений`)
        bulkTarget.value = ''
        forceWipe.value = false
        transferModal.value = {
          user: u,
          classes: d.classes_owned,
          choices,
          extra: extras.length > 0 ? extras.join(', ') : null,
        }
        return
      }
    }
    toast.error(extractError(e))
  }
}

async function onConfirmTransferAndDelete() {
  const m = transferModal.value
  if (!m || !canConfirm.value) return
  transferBusy.value = true
  try {
    // Per-class: either transfer to a chosen user, or delete the class.
    for (const cls of m.classes) {
      const choice = m.choices[cls.id]
      if (choice === DELETE_CHOICE) {
        await adminApi.deleteClass(cls.id)
      } else {
        await adminApi.transferClass(cls.id, choice)
      }
    }
    // force=true wipes leftover non-class content (announcements/assignments/
    // solutions) the admin opted to remove.
    await adminApi.deleteUser(m.user.id, forceWipe.value)
    toast.success(`Пользователь ${m.user.username} удалён`)
    transferModal.value = null
    await loadUsers()
  } catch (e) {
    toast.error(extractError(e))
  } finally {
    transferBusy.value = false
  }
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

function formatBytes(b: number): string {
  if (b < 1024) return `${b} B`
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`
  if (b < 1024 * 1024 * 1024) return `${(b / 1024 / 1024).toFixed(1)} MB`
  return `${(b / 1024 / 1024 / 1024).toFixed(1)} GB`
}

watch(tab, async (t) => {
  if (t === 'users' && users.value.length === 0) await loadUsers()
  if (t === 'classes' && classes.value.length === 0) await loadClasses()
  if (t === 'stats' && !stats.value) await loadStats()
})

onMounted(loadUsers)
</script>

<style scoped>
.filter-card {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  align-items: center;
  margin-bottom: 18px;
}
.filter-search { flex: 1; min-width: 260px; }
.check {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-muted);
  cursor: pointer;
}
.check input { width: 18px; height: 18px; }
.td-strong { font-weight: 800; }

.stat-grid-4 { grid-template-columns: repeat(4, 1fr); }
@media (max-width: 1100px) { .stat-grid-4 { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 640px)  { .stat-grid-4 { grid-template-columns: 1fr; } }

/* ---------- Action buttons stack ---------- */
.row-actions {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 8px;
}
.action-btn {
  font-size: 13px;
  padding: 7px 14px;
}
</style>

<style>
/* ---------- Modal (global to overlap entire page; teleported to body) ---------- */
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(20, 14, 8, 0.42);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  z-index: 1000;
  backdrop-filter: blur(2px);
}
.modal {
  width: min(580px, 100%);
  max-height: 90vh;
  overflow-y: auto;
  background: var(--color-surface);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: 24px;
  padding: 28px 30px;
  box-shadow: 0 30px 80px rgba(20, 14, 8, 0.35);
}
.modal-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin-bottom: 10px;
}
.modal-sub {
  font-size: 14.5px;
  color: var(--color-text-muted);
  line-height: 1.5;
  margin-bottom: 18px;
}
.extra-warning {
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--color-warning-soft);
  color: var(--color-warning);
  font-size: 13px;
  margin-top: 16px;
}
.force-check {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  font-weight: 800;
  cursor: pointer;
}
.force-check input { width: 17px; height: 17px; }

/* «Assign all classes to one» bulk row */
.bulk-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 12px 14px;
  margin-bottom: 14px;
  border-radius: 12px;
  background: var(--color-primary-soft);
  border: 1px solid color-mix(in srgb, var(--color-primary) 22%, transparent);
}
.bulk-label { font-size: 13.5px; font-weight: 800; color: var(--color-text); }
.bulk-row .transfer-select { flex: 1; min-width: 200px; }
.bulk-apply { font-size: 13px; padding: 9px 16px; white-space: nowrap; }

.transfer-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.transfer-row {
  display: grid;
  grid-template-columns: 1fr 1.4fr;
  gap: 12px;
  align-items: center;
  padding: 10px 12px;
  border-radius: 12px;
  background: var(--color-bg-2);
  border: 1px solid transparent;
  transition: background var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out);
}
.transfer-row.will-delete {
  background: var(--color-danger-soft);
  border-color: var(--color-danger-soft);
}
.transfer-row.will-delete .transfer-class-name {
  text-decoration: line-through;
  color: var(--color-danger);
}
.transfer-class-name {
  font-weight: 800;
  font-size: 14px;
}
.transfer-select { font-size: 13.5px; }
@media (max-width: 540px) {
  .transfer-row { grid-template-columns: 1fr; }
}
</style>
