<template>
  <div class="container page">
    <!-- Hero header -->
    <header class="home-hero reveal">
      <div class="hero-text">
        <p class="hero-eyebrow">Рабочее пространство</p>
        <h1 class="page-title">Мои классы</h1>
        <p class="hero-sub muted" v-if="!loading">
          {{ items.length }} {{ pluralClasses(items.length) }} · всё в одном месте
        </p>
      </div>
      <div class="hero-actions">
        <button class="btn-secondary" :class="{ active: showJoin }" @click="showJoin = !showJoin; showCreate = false">
          Вступить по коду
        </button>
        <button class="btn-primary" :class="{ active: showCreate }" @click="showCreate = !showCreate; showJoin = false">
          + Создать класс
        </button>
      </div>
    </header>

    <!-- Join panel -->
    <Transition name="panel">
      <div v-if="showJoin" class="card action-panel">
        <div class="stack">
          <div class="form-group" style="margin-bottom: 0">
            <label>Invite-код</label>
            <input v-model="joinCode" maxlength="8" placeholder="ABCDEFGH" class="code-input" />
          </div>
          <div v-if="joinError" class="error-text">{{ joinError }}</div>
          <div class="row">
            <button class="btn-primary" :disabled="joinLoading" @click="onJoin">
              {{ joinLoading ? 'Вступаем…' : 'Вступить' }}
            </button>
            <button class="btn-ghost" @click="showJoin = false">Отмена</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Create panel -->
    <Transition name="panel">
      <div v-if="showCreate" class="card action-panel">
        <div class="stack">
          <div class="form-group" style="margin-bottom: 0">
            <label>Название</label>
            <input v-model="createName" placeholder="Например: Математика 10-А" />
          </div>
          <div class="form-group" style="margin-bottom: 0">
            <label>Тип</label>
            <select v-model="createType">
              <option value="open">Открытый (виден в каталоге)</option>
              <option value="closed">Закрытый (только по коду)</option>
            </select>
          </div>
          <div v-if="createError" class="error-text">{{ createError }}</div>
          <div class="row">
            <button class="btn-primary" :disabled="createLoading" @click="onCreate">
              {{ createLoading ? 'Создаём…' : 'Создать' }}
            </button>
            <button class="btn-ghost" @click="showCreate = false">Отмена</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Skeleton while loading -->
    <div v-if="loading" class="classes-grid">
      <div v-for="n in 3" :key="n" class="class-card skeleton-card" aria-hidden="true">
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
        <button class="btn-secondary" @click="showJoin = true">Вступить по коду</button>
      </div>
    </div>

    <!-- Class grid -->
    <div v-else class="classes-grid">
      <RouterLink
        v-for="(cls, i) in items"
        :key="cls.id"
        :to="`/classes/${cls.id}`"
        class="class-card reveal"
        :style="{ animationDelay: 60 + i * 55 + 'ms' }"
      >
        <span class="card-accent" :class="cls.type === 'open' ? 'accent-open' : 'accent-closed'"></span>
        <div class="row-between card-top">
          <h3>{{ cls.name }}</h3>
          <span class="tag" :class="cls.type === 'open' ? 'tag-info' : 'tag-warning'">
            {{ cls.type === 'open' ? 'открытый' : 'закрытый' }}
          </span>
        </div>
        <div class="card-meta">
          <span class="meta-avatar">{{ (cls.creator?.username || '—').charAt(0).toUpperCase() }}</span>
          <span class="muted">{{ cls.creator?.username || '—' }}</span>
        </div>
        <div class="card-foot">
          <span class="member-count">{{ cls.member_count }}</span>
          <span class="muted">{{ pluralMembers(cls.member_count) }}</span>
          <span class="card-arrow" aria-hidden="true">→</span>
        </div>
      </RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listMyClasses, createClass, joinByCode } from '@/shared/api/classes'
import type { ClassResponse, ClassType } from '@/shared/api/types'
import { extractError } from '@/shared/api/errors'

const router = useRouter()
const items = ref<ClassResponse[]>([])
const loading = ref(false)

const showJoin = ref(false)
const joinCode = ref('')
const joinError = ref('')
const joinLoading = ref(false)

const showCreate = ref(false)
const createName = ref('')
const createType = ref<ClassType>('open')
const createError = ref('')
const createLoading = ref(false)

function pluralClasses(n: number): string {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return 'класс'
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return 'класса'
  return 'классов'
}

function pluralMembers(n: number): string {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return 'участник'
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return 'участника'
  return 'участников'
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
/* ---------- Hero ---------- */
.home-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 20px;
  margin-bottom: 32px;
  padding-bottom: 28px;
  border-bottom: 1px solid var(--color-border);
}
.hero-eyebrow {
  font-size: 12.5px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-primary);
  margin-bottom: 8px;
}
.hero-sub { font-size: 14.5px; margin-top: 8px; }
.hero-actions { display: flex; gap: 12px; flex-shrink: 0; }
.hero-actions .btn-primary.active,
.hero-actions .btn-secondary.active { box-shadow: 0 0 0 3px var(--color-primary-ring); }

/* ---------- Action panels ---------- */
.action-panel { margin-bottom: 24px; box-shadow: var(--shadow); }
.code-input {
  font-family: var(--font-display);
  letter-spacing: 0.3em;
  text-transform: uppercase;
  font-size: 17px;
}
.panel-enter-active { transition: all var(--dur) var(--ease-out); }
.panel-leave-active { transition: all var(--dur-fast) var(--ease-out); }
.panel-enter-from,
.panel-leave-to { opacity: 0; transform: translateY(-8px); }

/* ---------- Class grid ---------- */
.classes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 20px;
}
.class-card {
  position: relative;
  overflow: hidden;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 22px 22px 18px;
  color: var(--color-text);
  text-decoration: none;
  box-shadow: var(--shadow-sm);
  transition:
    transform var(--dur) var(--ease-out),
    box-shadow var(--dur) var(--ease-out),
    border-color var(--dur) var(--ease-out);
}
.class-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--color-border-strong);
  text-decoration: none;
}
/* accent rail along the top edge */
.card-accent {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  transform: scaleX(0);
  transform-origin: left;
  transition: transform var(--dur-slow) var(--ease-out);
}
.accent-open { background: linear-gradient(90deg, var(--color-primary), #3f8e72); }
.accent-closed { background: linear-gradient(90deg, var(--color-warning), #c79143); }
.class-card:hover .card-accent { transform: scaleX(1); }

.card-top { align-items: flex-start; margin-bottom: 16px; }
.class-card h3 {
  font-family: var(--font-display);
  font-size: 19px;
  font-weight: 600;
  line-height: 1.25;
  letter-spacing: -0.01em;
}
.card-meta {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 13.5px;
  margin-bottom: 18px;
}
.meta-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.card-foot {
  display: flex;
  align-items: baseline;
  gap: 6px;
  padding-top: 14px;
  border-top: 1px solid var(--color-border);
  font-size: 13.5px;
}
.member-count {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
}
.card-arrow {
  margin-left: auto;
  color: var(--color-primary);
  font-size: 16px;
  transition: transform var(--dur) var(--ease-spring);
}
.class-card:hover .card-arrow { transform: translateX(5px); }

/* ---------- Skeleton ---------- */
.skeleton-card { pointer-events: none; }
.sk { border-radius: 6px; background: var(--color-surface-sunken); }
.sk-line { height: 14px; }
.skeleton-card .sk { animation: sk-pulse 1.4s ease-in-out infinite; }
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
}

@media (max-width: 640px) {
  .home-hero { flex-direction: column; align-items: stretch; }
  .hero-actions { flex-wrap: wrap; }
  .hero-actions button { flex: 1; }
}
</style>
