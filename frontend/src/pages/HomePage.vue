<template>
  <div class="container page">
    <!-- Split title with right-side actions -->
    <div class="split-title reveal">
      <div>
        <div class="title-kicker">Обзор</div>
        <h1 class="page-title">Добро пожаловать{{ greetName }}</h1>
      </div>
      <div class="split-title-right">
        <button
          class="btn-ghost"
          :class="{ active: showJoin }"
          @click="showJoin = !showJoin; showCreate = false"
        >
          Вступить по коду
        </button>
        <button
          class="btn-primary"
          :class="{ active: showCreate }"
          @click="showCreate = !showCreate; showJoin = false"
        >
          + Создать класс
        </button>
      </div>
    </div>
    <div class="title-line"></div>

    <!-- Dashboard stats -->
    <div class="stat-grid reveal" style="animation-delay: 80ms">
      <div class="stat">
        <div class="stat-label">Классов</div>
        <div class="stat-value" style="color: var(--color-primary)">{{ items.length }}</div>
        <div class="stat-sub">
          <template v-if="teacherCount > 0 && studentCount > 0">
            {{ teacherCount }} как преподаватель · {{ studentCount }} как студент
          </template>
          <template v-else-if="teacherCount > 0">
            всё как преподаватель
          </template>
          <template v-else-if="studentCount > 0">
            всё как студент
          </template>
          <template v-else>
            вступайте в открытые классы из каталога
          </template>
        </div>
      </div>
      <div class="stat">
        <div class="stat-label">Преподавательских</div>
        <div class="stat-value" style="color: var(--color-accent-hover)">{{ teacherCount }}</div>
        <div class="stat-sub">создатель или преподаватель</div>
      </div>
      <div class="stat">
        <div class="stat-label">Новых уведомлений</div>
        <div class="stat-value">{{ notifications.unreadCount }}</div>
        <div class="stat-sub">за последнее время</div>
      </div>
    </div>

    <h2 class="section-title" style="margin-top: 10px">Мои классы</h2>

    <!-- Join panel -->
    <Transition name="panel">
      <div v-if="showJoin" class="card action-panel">
        <div class="card-title">Присоединиться по коду</div>
        <p class="muted" style="margin-bottom: 14px; font-size: 14px">
          Для закрытого класса необходимо ввести код доступа из 8 символов.
        </p>
        <div class="form-group">
          <label>Invite-код</label>
          <input v-model="joinCode" maxlength="8" placeholder="A1B2C3D4" class="code-input" />
        </div>
        <div v-if="joinError" class="error-text" style="margin-bottom: 12px">{{ joinError }}</div>
        <div class="row">
          <button class="btn-primary" :disabled="joinLoading" @click="onJoin">
            {{ joinLoading ? 'Вступаем…' : 'Вступить' }}
          </button>
          <button class="btn-ghost" @click="showJoin = false">Отмена</button>
        </div>
      </div>
    </Transition>

    <!-- Create panel -->
    <Transition name="panel">
      <div v-if="showCreate" class="card action-panel">
        <div class="card-title">Создать класс</div>
        <p class="muted" style="margin-bottom: 14px; font-size: 14px">
          Любой пользователь может создать класс и стать преподавателем-создателем.
        </p>
        <div class="form-group">
          <label>Название класса</label>
          <input v-model="createName" placeholder="Например: ИВТ41" />
        </div>
        <div class="form-group">
          <label>Тип класса</label>
          <select v-model="createType">
            <option value="open">Открытый (виден в каталоге)</option>
            <option value="closed">Закрытый (только по коду)</option>
          </select>
        </div>
        <div v-if="createError" class="error-text" style="margin-bottom: 12px">{{ createError }}</div>
        <div class="row">
          <button class="btn-primary" :disabled="createLoading" @click="onCreate">
            {{ createLoading ? 'Создаём…' : 'Создать' }}
          </button>
          <button class="btn-ghost" @click="showCreate = false">Отмена</button>
        </div>
      </div>
    </Transition>

    <!-- Skeleton -->
    <div v-if="loading" class="catalog">
      <div v-for="n in 3" :key="n" class="card catalog-card skeleton-card" aria-hidden="true">
        <div class="sk sk-line" style="width: 60%"></div>
        <div class="sk sk-line" style="width: 40%; margin-top: 16px"></div>
        <div class="sk sk-line" style="width: 50%; margin-top: 8px"></div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else-if="items.length === 0" class="empty-state reveal">
      <div class="empty-glyph">✦</div>
      <h3 class="empty-title">Здесь пока пусто</h3>
      <p class="muted">Создайте свой первый класс или вступите в существующий по коду.</p>
      <div class="row" style="justify-content: center; margin-top: 20px">
        <button class="btn-primary" @click="showCreate = true">+ Создать класс</button>
        <button class="btn-ghost" @click="showJoin = true">Вступить по коду</button>
      </div>
    </div>

    <!-- Class grid -->
    <div v-else class="catalog">
      <RouterLink
        v-for="(cls, i) in items"
        :key="cls.id"
        :to="`/classes/${cls.id}`"
        class="card catalog-card reveal"
        :style="{ animationDelay: 60 + i * 55 + 'ms' }"
      >
        <div class="badges">
          <span class="badge" :class="cls.type === 'open' ? 'badge-open' : 'badge-closed'">
            {{ cls.type === 'open' ? 'открытый' : 'закрытый' }}
          </span>
          <span v-if="cls.my_role" class="badge" :class="roleBadgeClass(cls.my_role)">
            {{ roleLabel(cls.my_role) }}
          </span>
        </div>
        <div class="catalog-name">{{ cls.name }}</div>
        <div class="catalog-meta">
          {{ cls.member_count }} {{ pluralMembers(cls.member_count) }} ·
          создал {{ cls.creator?.username || '—' }}
        </div>
        <div class="card-arrow" aria-hidden="true">→</div>
      </RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listMyClasses, createClass, joinByCode } from '@/shared/api/classes'
import type { ClassResponse, ClassType, MemberRole } from '@/shared/api/types'
import { extractError } from '@/shared/api/errors'
import { useAuthStore } from '@/shared/stores/authStore'
import { useNotificationStore } from '@/shared/stores/notificationStore'

const router = useRouter()
const auth = useAuthStore()
const notifications = useNotificationStore()
const items = ref<ClassResponse[]>([])
const loading = ref(false)

const greetName = computed(() => {
  const name = auth.user?.username?.trim()
  return name ? `, ${name}` : ''
})
const teacherCount = computed(() =>
  items.value.filter((c) => c.my_role === 'teacher_creator' || c.my_role === 'teacher').length,
)
const studentCount = computed(() =>
  items.value.filter((c) => c.my_role === 'student').length,
)

const showJoin = ref(false)
const joinCode = ref('')
const joinError = ref('')
const joinLoading = ref(false)

const showCreate = ref(false)
const createName = ref('')
const createType = ref<ClassType>('open')
const createError = ref('')
const createLoading = ref(false)

function pluralMembers(n: number): string {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return 'участник'
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return 'участника'
  return 'участников'
}

function roleLabel(role: MemberRole): string {
  if (role === 'teacher_creator') return 'создатель'
  if (role === 'teacher') return 'преподаватель'
  return 'студент'
}
function roleBadgeClass(role: MemberRole): string {
  if (role === 'teacher_creator') return 'badge-creator'
  if (role === 'teacher') return 'badge-teacher'
  return 'badge-student'
}

async function load() {
  loading.value = true
  try {
    items.value = await listMyClasses()
  } finally {
    loading.value = false
  }
}

async function onJoin() {
  joinError.value = ''
  const code = joinCode.value.trim().toUpperCase()
  if (code.length !== 8) {
    joinError.value = 'Код должен содержать 8 символов'
    return
  }
  joinLoading.value = true
  try {
    const cls = await joinByCode(code)
    showJoin.value = false
    joinCode.value = ''
    await router.push(`/classes/${cls.id}`)
  } catch (e) {
    joinError.value = extractError(e)
  } finally {
    joinLoading.value = false
  }
}

async function onCreate() {
  createError.value = ''
  if (createName.value.trim().length < 2) {
    createError.value = 'Название должно содержать минимум 2 символа'
    return
  }
  createLoading.value = true
  try {
    const cls = await createClass({ name: createName.value.trim(), type: createType.value })
    showCreate.value = false
    createName.value = ''
    await router.push(`/classes/${cls.id}`)
  } catch (e) {
    createError.value = extractError(e)
  } finally {
    createLoading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.hero-sub {
  font-size: 15px;
  margin-top: -16px;
  margin-bottom: 24px;
}

.split-title-right button.active { box-shadow: 0 0 0 3px var(--color-primary-ring); }

/* ---------- Action panels ---------- */
.action-panel { margin-bottom: 24px; }
.card-title {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin-bottom: 6px;
}
.code-input {
  font-family: var(--font-display);
  letter-spacing: 0.3em;
  text-transform: uppercase;
  font-size: 22px;
  font-weight: 800;
  text-align: center;
}
.panel-enter-active { transition: all var(--dur) var(--ease-out); }
.panel-leave-active { transition: all var(--dur-fast) var(--ease-out); }
.panel-enter-from,
.panel-leave-to { opacity: 0; transform: translateY(-8px); }

/* ---------- Catalog grid ---------- */
.catalog {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 18px;
}
.catalog-card {
  position: relative;
  cursor: pointer;
  text-decoration: none;
  color: var(--color-text);
  padding: 24px;
  transition: transform var(--dur) var(--ease-out), box-shadow var(--dur) var(--ease-out);
  overflow: hidden;
}
.catalog-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
  text-decoration: none;
}
.catalog-name {
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 800;
  letter-spacing: -0.025em;
  margin: 12px 0 10px;
  line-height: 1.15;
}
.catalog-meta {
  font-size: 15px;
  color: var(--color-text-muted);
}

.card-arrow {
  position: absolute;
  right: 22px;
  bottom: 18px;
  color: var(--color-primary);
  font-size: 22px;
  transition: transform var(--dur) var(--ease-spring);
}
.catalog-card:hover .card-arrow { transform: translateX(6px); }

/* ---------- Skeleton ---------- */
.skeleton-card { pointer-events: none; }
.sk { border-radius: 6px; background: var(--color-bg-2); height: 14px; animation: sk-pulse 1.4s ease-in-out infinite; }
@keyframes sk-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

/* ---------- Empty state ---------- */
.empty-state {
  text-align: center;
  padding: 72px 24px;
  border: 1px dashed var(--color-border-strong);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}
.empty-glyph {
  font-size: 32px;
  color: var(--color-primary);
  margin-bottom: 16px;
}
.empty-title {
  font-family: var(--font-display);
  font-size: 22px;
  margin-bottom: 8px;
  font-weight: 800;
}

@media (max-width: 640px) {
  .split-title { flex-direction: column; align-items: stretch; }
  .split-title-right { flex-wrap: wrap; }
  .split-title-right button { flex: 1; }
}
</style>
