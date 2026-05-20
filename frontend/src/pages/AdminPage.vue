<template>
  <div class="container page">
    <h1 class="page-title">Администрирование</h1>

    <div class="tabs">
      <button
        v-for="t in tabs"
        :key="t.id"
        class="tab"
        :class="{ active: tab === t.id }"
        @click="tab = t.id"
      >{{ t.label }}</button>
    </div>

    <!-- USERS -->
    <div v-if="tab === 'users'">
      <div class="card" style="margin-bottom: 12px">
        <div class="row">
          <input v-model="userSearch" placeholder="Поиск (email или username)" @keyup.enter="loadUsers" />
          <label class="row" style="gap: 6px; font-size: 13px">
            <input type="checkbox" v-model="includeDeletedUsers" style="width: auto" @change="loadUsers" />
            Включая заблокированных
          </label>
          <button class="btn-primary" @click="loadUsers">Найти</button>
        </div>
      </div>
      <div v-if="usersLoading" class="card muted">Загрузка…</div>
      <div v-else class="card" style="padding: 0">
        <table class="data-table">
          <thead>
            <tr>
              <th>Имя</th>
              <th>Email</th>
              <th>Статус</th>
              <th>Создан</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td>
                <strong>{{ u.username }}</strong>
                <span v-if="u.is_admin" class="tag tag-info" style="margin-left: 6px">admin</span>
              </td>
              <td>{{ u.email }}</td>
              <td>
                <span v-if="u.deleted_at" class="tag tag-danger">заблокирован</span>
                <span v-else class="tag tag-success">активен</span>
              </td>
              <td>{{ formatDate(u.created_at) }}</td>
              <td>
                <button
                  v-if="!u.deleted_at"
                  class="btn-secondary"
                  style="font-size: 12px; padding: 4px 8px"
                  @click="onBlock(u)"
                >Заблокировать</button>
                <button
                  v-else
                  class="btn-secondary"
                  style="font-size: 12px; padding: 4px 8px"
                  @click="onUnblock(u)"
                >Разблокировать</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- CLASSES -->
    <div v-else-if="tab === 'classes'">
      <div class="card" style="margin-bottom: 12px">
        <div class="row">
          <input v-model="classSearch" placeholder="Поиск по названию" @keyup.enter="loadClasses" />
          <label class="row" style="gap: 6px; font-size: 13px">
            <input type="checkbox" v-model="includeDeletedClasses" style="width: auto" @change="loadClasses" />
            Включая удалённые
          </label>
          <button class="btn-primary" @click="loadClasses">Найти</button>
        </div>
      </div>
      <div v-if="classesLoading" class="card muted">Загрузка…</div>
      <div v-else class="card" style="padding: 0">
        <table class="data-table">
          <thead>
            <tr>
              <th>Название</th>
              <th>Тип</th>
              <th>Создатель</th>
              <th>Участников</th>
              <th>Статус</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in classes" :key="c.id">
              <td>{{ c.name }}</td>
              <td>{{ c.type }}</td>
              <td>{{ c.creator_username }}</td>
              <td>{{ c.member_count }}</td>
              <td>
                <span v-if="c.deleted_at" class="tag tag-danger">удалён</span>
                <span v-else class="tag tag-success">активен</span>
              </td>
              <td>
                <button
                  v-if="!c.deleted_at"
                  class="btn-danger"
                  style="font-size: 12px; padding: 4px 8px"
                  @click="onDeleteClass(c)"
                >Удалить</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- STATS -->
    <div v-else-if="tab === 'stats'">
      <div v-if="statsLoading" class="card muted">Загрузка…</div>
      <div v-else-if="stats" class="stats-grid">
        <div class="card stat-card">
          <div class="stat-label">Пользователи</div>
          <div class="stat-value">{{ stats.users_active }}</div>
          <div class="muted" style="font-size: 12px">всего {{ stats.users_total }}</div>
        </div>
        <div class="card stat-card">
          <div class="stat-label">Классы</div>
          <div class="stat-value">{{ stats.classes_active }}</div>
          <div class="muted" style="font-size: 12px">всего {{ stats.classes_total }}</div>
        </div>
        <div class="card stat-card">
          <div class="stat-label">Решения</div>
          <div class="stat-value">{{ stats.solutions_total }}</div>
        </div>
        <div class="card stat-card">
          <div class="stat-label">Файлы</div>
          <div class="stat-value">{{ formatBytes(stats.file_bytes) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import * as adminApi from '@/shared/api/admin'
import type { AdminClass, AdminStats, AdminUser } from '@/shared/api/types'
import { extractError } from '@/shared/api/errors'

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
    alert(extractError(e))
  }
}

async function onUnblock(u: AdminUser) {
  try {
    await adminApi.unblockUser(u.id)
    await loadUsers()
  } catch (e) {
    alert(extractError(e))
  }
}

async function onDeleteClass(c: AdminClass) {
  if (!confirm(`Удалить класс «${c.name}»?`)) return
  try {
    await adminApi.deleteClass(c.id)
    await loadClasses()
  } catch (e) {
    alert(extractError(e))
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
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}
.stat-card {
  text-align: center;
}
.stat-label {
  color: var(--color-text-muted);
  font-size: 13px;
  margin-bottom: 6px;
}
.stat-value {
  font-size: 28px;
  font-weight: 600;
}
</style>
