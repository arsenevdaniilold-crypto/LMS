<template>
  <div class="container page">
    <div class="title-kicker">Присоединение к классам</div>
    <h1 class="page-title">Каталог классов</h1>
    <div class="title-line"></div>

    <!-- Search row -->
    <div class="search-row reveal">
      <input
        v-model="search"
        class="search-input"
        placeholder="Поиск по названию класса"
        @keyup.enter="load"
      />
      <input
        v-model="teacher"
        class="teacher-input"
        placeholder="Преподаватель"
        @keyup.enter="load"
      />
      <select v-model="sort" class="sort-input">
        <option value="created_desc">Сначала новые</option>
        <option value="created_asc">Сначала старые</option>
        <option value="name_asc">По имени</option>
      </select>
      <button class="btn-primary" @click="load">Найти</button>
    </div>

    <!-- Skeleton -->
    <div v-if="loading" class="catalog">
      <div v-for="n in 3" :key="n" class="card catalog-card skeleton-card" aria-hidden="true">
        <div class="sk sk-line" style="width: 60%"></div>
        <div class="sk sk-line" style="width: 45%; margin-top: 16px"></div>
      </div>
    </div>

    <!-- Empty -->
    <div v-else-if="items.length === 0" class="empty-state reveal">
      <div class="empty-glyph">✦</div>
      <h3 class="empty-title">Ничего не найдено</h3>
      <p class="muted">Попробуйте изменить запрос или фильтры.</p>
    </div>

    <!-- Catalog grid -->
    <div v-else class="catalog">
      <div
        v-for="(cls, i) in items"
        :key="cls.id"
        class="card catalog-card reveal"
        :style="{ animationDelay: 60 + i * 50 + 'ms' }"
      >
        <RouterLink :to="`/classes/${cls.id}`" class="catalog-link">
          <div class="badges">
            <span class="badge badge-open">открытый</span>
          </div>
          <div class="catalog-name">{{ cls.name }}</div>
          <div class="catalog-meta">
            создал {{ cls.creator?.username || '—' }} ·
            {{ cls.member_count }} {{ pluralMembers(cls.member_count) }}
          </div>
        </RouterLink>

        <div class="catalog-foot">
          <RouterLink
            v-if="cls.my_role"
            :to="`/classes/${cls.id}`"
            class="badge badge-active"
          >
            уже в классе
          </RouterLink>
          <button
            v-else
            class="btn-primary join-btn"
            :disabled="joining === cls.id"
            @click="onJoin(cls.id)"
          >
            {{ joining === cls.id ? 'Вступаем…' : 'Вступить' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="errorMsg" class="error-text" style="margin-top: 14px">{{ errorMsg }}</div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { joinOpenClass, listOpenClasses } from '@/shared/api/classes'
import { extractError } from '@/shared/api/errors'
import type { ClassResponse } from '@/shared/api/types'

const router = useRouter()
const search = ref('')
const teacher = ref('')
const sort = ref<'created_desc' | 'created_asc' | 'name_asc'>('created_desc')
const items = ref<ClassResponse[]>([])
const loading = ref(false)
const joining = ref<string | null>(null)
const errorMsg = ref('')

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
    const res = await listOpenClasses({
      search: search.value || undefined,
      teacher: teacher.value || undefined,
      sort: sort.value,
      page: 1,
      page_size: 50,
    })
    items.value = res.items
  } finally {
    loading.value = false
  }
}

async function onJoin(id: string) {
  errorMsg.value = ''
  joining.value = id
  try {
    await joinOpenClass(id)
    await router.push(`/classes/${id}`)
  } catch (e) {
    errorMsg.value = extractError(e)
  } finally {
    joining.value = null
  }
}

onMounted(load)
</script>

<style scoped>
.search-row {
  display: grid;
  grid-template-columns: 2fr 1.2fr 1fr auto;
  gap: 12px;
  margin-bottom: 28px;
}
.search-input,
.teacher-input,
.sort-input {
  width: 100%;
}

/* ---------- Catalog ---------- */
.catalog {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 18px;
}
.catalog-card {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: transform var(--dur) var(--ease-out), box-shadow var(--dur) var(--ease-out);
}
.catalog-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
}
.catalog-link {
  color: var(--color-text);
  text-decoration: none;
  display: block;
}
.catalog-link:hover { text-decoration: none; }

.catalog-name {
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 800;
  letter-spacing: -0.025em;
  line-height: 1.15;
  margin: 12px 0 10px;
}
.catalog-meta {
  font-size: 15px;
  color: var(--color-text-muted);
}

.catalog-foot {
  padding-top: 14px;
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
}
.join-btn { font-size: 14px; padding: 10px 18px; }
.badge-active { padding: 7px 14px; }

/* ---------- Skeleton / empty ---------- */
.skeleton-card { pointer-events: none; }
.sk { border-radius: 6px; background: var(--color-bg-2); height: 14px; animation: sk-pulse 1.4s ease-in-out infinite; }
@keyframes sk-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

.empty-state {
  text-align: center;
  padding: 72px 24px;
  border: 1px dashed var(--color-border-strong);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}
.empty-glyph { font-size: 32px; color: var(--color-primary); margin-bottom: 16px; }
.empty-title { font-family: var(--font-display); font-size: 22px; font-weight: 800; margin-bottom: 8px; }

@media (max-width: 768px) {
  .search-row { grid-template-columns: 1fr; }
}
</style>
