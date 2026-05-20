<template>
  <div class="card">
    <h3 class="section-title">Новое объявление</h3>
    <div class="stack">
      <div class="form-group" style="margin-bottom: 0">
        <label>Заголовок</label>
        <input v-model="title" placeholder="Тема объявления" />
      </div>
      <div class="form-group" style="margin-bottom: 0">
        <label>Текст</label>
        <textarea v-model="text" rows="4" placeholder="Содержимое" />
      </div>
      <FileInput v-model="files" multiple />
      <div v-if="error" class="error-text">{{ error }}</div>
      <div class="row">
        <button class="btn-primary" :disabled="loading" @click="submit">
          {{ loading ? 'Публикуем…' : 'Опубликовать' }}
        </button>
        <button class="btn-secondary" @click="$emit('cancel')">Отмена</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { createAnnouncement } from '@/shared/api/announcements'
import { extractError } from '@/shared/api/errors'
import type { Announcement } from '@/shared/api/types'
import FileInput from './FileInput.vue'

const props = defineProps<{ classId: string }>()
const emit = defineEmits<{
  (e: 'created', a: Announcement): void
  (e: 'cancel'): void
}>()

const title = ref('')
const text = ref('')
const files = ref<File[]>([])
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  if (title.value.trim().length === 0) {
    error.value = 'Заголовок обязателен'
    return
  }
  if (text.value.trim().length === 0) {
    error.value = 'Текст обязателен'
    return
  }
  loading.value = true
  try {
    const a = await createAnnouncement(props.classId, title.value.trim(), text.value.trim(), files.value)
    emit('created', a)
    title.value = ''
    text.value = ''
    files.value = []
  } catch (e) {
    error.value = extractError(e)
  } finally {
    loading.value = false
  }
}
</script>
