<template>
  <div class="container page">
    <h1 class="page-title">Каталог открытых классов</h1>

    <div class="card filters" style="margin-bottom: 16px">
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

    <div v-if="loading" class="card muted">Загрузка…</div>
    <div v-else-if="items.length === 0" class="card muted">Ничего не найдено</div>
    <div v-else class="classes-grid">
      <div v-for="cls in items" :key="cls.id" class="class-card">
        <RouterLink :to="`/classes/${cls.id}`" class="class-card-link">
          <h3>{{ cls.name }}</h3>
          <div class="muted" style="font-size: 13px; margin-top: 8px">
            Преподаватель: {{ cls.creator?.username || '—' }}
          </div>
          <div class="muted" style="font-size: 13px">
            Участников: {{ cls.member_count }}
          </div>
        </RouterLink>
        <div class="class-card-actions">
          <RouterLink v-if="cls.my_role" :to="`/classes/${cls.id}`" class="btn-secondary tag-success-link">
            Уже в классе
          </RouterLink>
          <button
            v-else
            class="btn-primary"
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
.filters-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr auto;
  gap: 12px;
}
@media (max-width: 768px) {
  .filters-row {
    grid-template-columns: 1fr;
  }
}
.classes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.class-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 16px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 12px;
}
.class-card:hover {
  border-color: var(--color-primary);
}
.class-card-link {
  color: var(--color-text);
  text-decoration: none;
}
.class-card-link:hover {
  text-decoration: none;
}
.class-card h3 {
  font-size: 16px;
}
.class-card-actions {
  display: flex;
  justify-content: flex-end;
}
.class-card-actions button {
  font-size: 13px;
  padding: 6px 12px;
}
</style>
