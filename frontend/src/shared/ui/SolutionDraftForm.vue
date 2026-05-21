<template>
  <div class="card">
    <h4 style="margin-bottom: 12px">Создать решение</h4>
    <div class="stack">
      <div class="form-group" style="margin-bottom: 0">
        <label>Текст решения</label>
        <textarea v-model="text" rows="5" placeholder="Ваше решение" />
      </div>
      <FileInput v-model="files" multiple />
      <div v-if="error" class="error-text">{{ error }}</div>
      <div class="row">
        <button class="btn-primary" :disabled="loading" @click="submit">
          {{ loading ? 'Сохраняем…' : 'Сохранить черновик' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { createSolution } from '@/shared/api/solutions'
import { extractError } from '@/shared/api/errors'
import type { Solution } from '@/shared/api/types'
import FileInput from './FileInput.vue'

const props = defineProps<{ assignmentId: string }>()
const emit = defineEmits<{ (e: 'created', s: Solution): void }>()

const text = ref('')
const files = ref<File[]>([])
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  if (text.value.trim().length === 0 && files.value.length === 0) {
    error.value = 'Добавьте текст или файлы'
    return
  }
  loading.value = true
  try {
    const s = await createSolution(props.assignmentId, text.value, files.value)
    emit('created', s)
    text.value = ''
    files.value = []
  } catch (e) {
    error.value = extractError(e)
  } finally {
    loading.value = false
  }
}
</script>
