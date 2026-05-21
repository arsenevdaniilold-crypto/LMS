<template>
  <div class="container page">
    <header class="catalog-hero reveal">
      <p class="hero-eyebrow">Каталог</p>
      <h1 class="page-title">Открытые классы</h1>
      <p class="hero-sub muted">Найдите класс и вступите в один клик</p>
    </header>

    <div class="card filters reveal" style="margin-bottom: 24px; animation-delay: 60ms">
      <div class="filters-row">
        <input v-model="search" placeholder="Поиск по названию" @keyup.enter="load" />
        <input v-model="teacher" placeholder="Преподаватель" @keyup.enter="load" />
        <select v-model="sort">
          <option value="created_desc">Сначала новые</option>
          <option value="created_asc">Сначала старые</option>
          <option value="name_asc">По имени</option>
        </select>
        <button class="btn-primary" @click="load">Найти</button>
      </div>
    </div>

    <div v-if="loading" class="classes-grid">
      <div v-for="n in 3" :key="n" class="class-card skeleton-card" aria-hidden="true">
        <div class="sk sk-line" style="width: 60%"></div>
        <div class="sk sk-line" style="width: 45%; margin-top: 16px"></div>
      </div>
    </div>
    <div v-else-if="items.length === 0" class="empty-state reveal">
      <div class="empty-glyph">✦</div>
      <h3 class="empty-title">Ничего не найдено</h3>
      <p class="muted">Попробуйте изменить запрос или фильтры.</p>
    </div>
    <div v-else class="classes-grid">
      <div
        v-for="(cls, i) in items"
        :key="cls.id"
        class="class-card reveal"
        :style="{ animationDelay: 60 + i * 50 + 'ms' }"
      >
        <span class="card-accent"></span>
        <RouterLink :to="`/classes/${cls.id}`" class="class-card-link">
          <h3>{{ cls.name }}</h3>
          <div class="card-meta">
            <span class="meta-avatar">{{ (cls.creator?.username || '—').charAt(0).toUpperCase() }}</span>
            <span class="muted">{{ cls.creator?.username || '—' }}</span>
          </div>
        </RouterLink>
        <div class="class-card-foot">
          <span class="foot-count"><span class="member-count">{{ cls.member_count }}</span> уч.</span>
          <RouterLink v-if="cls.my_role" :to="`/classes/${cls.id}`" class="tag tag-success">
            Уже в классе
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

    <div v-if="errorMsg" class="error-text" style="margin-top: 12px">{{ errorMsg }}</div>
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
.catalog-hero {
  margin-bottom: 28px;
  padding-bottom: 24px;
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

.filters-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr auto;
  gap: 12px;
}
@media (max-width: 768px) {
  .filters-row { grid-template-columns: 1fr; }
}

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
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: var(--shadow-sm);
  transition: transform var(--dur) var(--ease-out), box-shadow var(--dur) var(--ease-out), border-color var(--dur) var(--ease-out);
}
.class-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--color-border-strong);
}
.card-accent {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--color-primary), #3f8e72);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform var(--dur-slow) var(--ease-out);
}
.class-card:hover .card-accent { transform: scaleX(1); }

.class-card-link { color: var(--color-text); text-decoration: none; }
.class-card-link:hover { text-decoration: none; }
.class-card h3 {
  font-family: var(--font-display);
  font-size: 19px;
  font-weight: 600;
  line-height: 1.25;
}
.card-meta {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 13.5px;
  margin-top: 14px;
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
.class-card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding-top: 14px;
  border-top: 1px solid var(--color-border);
}
.foot-count { font-size: 13.5px; color: var(--color-text-muted); }
.member-count {
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 600;
  color: var(--color-text);
}
.join-btn { font-size: 13px; padding: 7px 16px; }

/* skeleton + empty (shared language) */
.skeleton-card { pointer-events: none; }
.sk { border-radius: 6px; background: var(--color-surface-sunken); height: 14px; animation: sk-pulse 1.4s ease-in-out infinite; }
@keyframes sk-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
.empty-state {
  text-align: center;
  padding: 64px 24px;
  border: 1px dashed var(--color-border-strong);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}
.empty-glyph { font-size: 32px; color: var(--color-primary); margin-bottom: 14px; }
.empty-title { font-family: var(--font-display); font-size: 22px; margin-bottom: 8px; }
</style>
