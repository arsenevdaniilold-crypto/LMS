<template>
  <div class="container page">
    <div class="row-between" style="margin-bottom: 16px">
      <h1 class="page-title">Мои классы</h1>
      <div class="row">
        <button class="btn-secondary" @click="showJoin = !showJoin">Вступить по коду</button>
        <button class="btn-primary" @click="showCreate = !showCreate">Создать класс</button>
      </div>
    </div>

    <div v-if="showJoin" class="card" style="margin-bottom: 16px">
      <div class="stack">
        <div class="form-group" style="margin-bottom: 0">
          <label>Invite-код</label>
          <input v-model="joinCode" maxlength="8" placeholder="ABCDEFGH" />
        </div>
        <div v-if="joinError" class="error-text">{{ joinError }}</div>
        <div class="row">
          <button class="btn-primary" :disabled="joinLoading" @click="onJoin">
            {{ joinLoading ? 'Вступаем…' : 'Вступить' }}
          </button>
          <button class="btn-secondary" @click="showJoin = false">Отмена</button>
        </div>
      </div>
    </div>

    <div v-if="showCreate" class="card" style="margin-bottom: 16px">
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
          <button class="btn-secondary" @click="showCreate = false">Отмена</button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="card muted">Загрузка…</div>
    <div v-else-if="items.length === 0" class="card muted">
      Вы ещё ни в одном классе. Создайте свой или вступите по коду.
    </div>
    <div v-else class="classes-grid">
      <RouterLink v-for="cls in items" :key="cls.id" :to="`/classes/${cls.id}`" class="class-card">
        <div class="row-between">
          <h3>{{ cls.name }}</h3>
          <span class="tag" :class="cls.type === 'open' ? 'tag-info' : 'tag-warning'">
            {{ cls.type === 'open' ? 'открытый' : 'закрытый' }}
          </span>
        </div>
        <div class="muted" style="font-size: 13px; margin-top: 8px">
          Создатель: {{ cls.creator?.username || '—' }}
        </div>
        <div class="muted" style="font-size: 13px">
          Участников: {{ cls.member_count }}
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
  color: var(--color-text);
  text-decoration: none;
  transition: border-color 0.15s, background 0.15s;
}
.class-card:hover {
  border-color: var(--color-primary);
  text-decoration: none;
}
.class-card h3 {
  font-size: 16px;
  margin: 0;
}
</style>
