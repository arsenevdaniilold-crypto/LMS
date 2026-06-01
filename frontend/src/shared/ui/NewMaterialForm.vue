<template>
  <div class="card create-form">
    <div class="form-head">
      <span class="badge badge-material">материал</span>
      <h3 class="form-title">Новый материал</h3>
      <p class="muted form-sub">Прикрепите учебные файлы и/или полезные ссылки для всего класса.</p>
    </div>
    <div class="stack">
      <div class="form-group" style="margin-bottom: 0">
        <label>Название</label>
        <input v-model="title" placeholder="Например: лекция 3 — нормализация БД" />
      </div>
      <div class="form-group" style="margin-bottom: 0">
        <label>Описание (необязательно)</label>
        <textarea v-model="description" rows="3" placeholder="Короткое пояснение для студентов" />
      </div>

      <FileInput v-model="files" multiple />

      <div>
        <label style="font-size: 13px; font-weight: 500; display: block; margin-bottom: 4px">
          Ссылки
        </label>
        <div class="stack" style="gap: 8px">
          <div v-for="(_, idx) in links" :key="idx" class="row" style="gap: 8px">
            <input
              v-model="links[idx]"
              placeholder="https://…"
              style="flex: 1"
            />
            <button class="btn-secondary" style="padding: 6px 10px" @click="removeLink(idx)">×</button>
          </div>
          <button class="btn-secondary" style="align-self: flex-start; font-size: 13px" @click="addLink">
            + Добавить ссылку
          </button>
        </div>
      </div>

      <div v-if="error" class="error-text">{{ error }}</div>
      <div class="row">
        <button class="btn-primary" :disabled="loading" @click="submit">
          {{ loading ? 'Сохраняем…' : 'Опубликовать' }}
        </button>
        <button class="btn-ghost" @click="$emit('cancel')">Отмена</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { createMaterial } from '@/shared/api/materials'
import { extractError } from '@/shared/api/errors'
import type { Material } from '@/shared/api/types'
import FileInput from './FileInput.vue'

const props = defineProps<{ classId: string }>()
const emit = defineEmits<{
  (e: 'created', m: Material): void
  (e: 'cancel'): void
}>()

const title = ref('')
const description = ref('')
const files = ref<File[]>([])
const links = ref<string[]>([])
const error = ref('')
const loading = ref(false)

function addLink() {
  links.value.push('')
}
function removeLink(idx: number) {
  links.value.splice(idx, 1)
}

async function submit() {
  error.value = ''
  if (title.value.trim().length === 0) {
    error.value = 'Название обязательно'
    return
  }
  const cleanLinks = links.value.map((l) => l.trim()).filter((l) => l.length > 0)
  for (const url of cleanLinks) {
    if (!/^https?:\/\//i.test(url)) {
      error.value = 'Ссылки должны начинаться с http:// или https://'
      return
    }
  }
  if (files.value.length === 0 && cleanLinks.length === 0) {
    error.value = 'Добавьте хотя бы один файл или ссылку'
    return
  }
  loading.value = true
  try {
    const m = await createMaterial(
      props.classId,
      title.value.trim(),
      description.value.trim(),
      files.value,
      cleanLinks,
    )
    emit('created', m)
    title.value = ''
    description.value = ''
    files.value = []
    links.value = []
  } catch (e) {
    error.value = extractError(e)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.form-head { margin-bottom: 18px; }
.form-title {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin-top: 10px;
}
.form-sub { font-size: 14px; max-width: 60ch; margin-top: 4px; }
</style>
