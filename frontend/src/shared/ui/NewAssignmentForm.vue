<template>
  <div class="card">
    <h3 class="section-title">Новое задание</h3>
    <div class="stack">
      <div class="form-group" style="margin-bottom: 0">
        <label>Название</label>
        <input v-model="name" placeholder="Тема задания" />
      </div>
      <div class="form-group" style="margin-bottom: 0">
        <label>Описание</label>
        <textarea v-model="description" rows="3" placeholder="Описание (необязательно)" />
      </div>
      <div class="row" style="gap: 12px; flex-wrap: wrap">
        <div class="form-group" style="margin-bottom: 0; max-width: 180px">
          <label>Тип</label>
          <select v-model="type">
            <option value="individual">Индивидуальное</option>
            <option value="group">Групповое</option>
          </select>
        </div>
        <div class="form-group" style="margin-bottom: 0; max-width: 180px">
          <label>Шкала оценок</label>
          <select v-model="gradeType">
            <option value="0-5">0–5</option>
            <option value="0-100">0–100</option>
            <option value="0-1">0–1</option>
          </select>
        </div>
        <div v-if="type === 'group'" class="form-group" style="margin-bottom: 0; max-width: 240px">
          <label>Тип оценивания</label>
          <select v-model="gradingType">
            <option value="uniform">Единая оценка</option>
            <option value="individual">Распределяется студентами</option>
          </select>
        </div>
        <div v-if="type === 'group'" class="form-group" style="margin-bottom: 0; max-width: 140px">
          <label>Кол-во групп</label>
          <input v-model.number="groupCount" type="number" min="1" max="100" />
        </div>
      </div>
      <div class="form-group" style="margin-bottom: 0; max-width: 280px">
        <label>Дедлайн (необязательно)</label>
        <input v-model="deadline" type="datetime-local" />
      </div>
      <div class="stack">
        <FileInput v-model="files" multiple />
        <div>
          <label style="font-size: 13px; font-weight: 500">Ссылки</label>
          <div v-for="(_, idx) in links" :key="idx" class="row" style="margin-top: 6px">
            <input v-model="links[idx]" placeholder="https://..." />
            <button class="btn-secondary" @click="links.splice(idx, 1)">×</button>
          </div>
          <button class="btn-secondary" style="margin-top: 6px" @click="links.push('')">
            + Добавить ссылку
          </button>
        </div>
      </div>
      <div v-if="error" class="error-text">{{ error }}</div>
      <div class="row">
        <button class="btn-primary" :disabled="loading" @click="submit">
          {{ loading ? 'Создаём…' : 'Создать задание' }}
        </button>
        <button class="btn-secondary" @click="$emit('cancel')">Отмена</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { createAssignment } from '@/shared/api/assignments'
import { extractError } from '@/shared/api/errors'
import type { Assignment, AssignmentType, GradeType, GradingType } from '@/shared/api/types'
import FileInput from './FileInput.vue'

const props = defineProps<{ classId: string }>()
const emit = defineEmits<{
  (e: 'created', a: Assignment): void
  (e: 'cancel'): void
}>()

const name = ref('')
const description = ref('')
const type = ref<AssignmentType>('individual')
const gradeType = ref<GradeType>('0-100')
const gradingType = ref<GradingType>('uniform')
const groupCount = ref<number>(2)
const deadline = ref<string>('')
const files = ref<File[]>([])
const links = ref<string[]>([])
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  if (name.value.trim().length < 2) {
    error.value = 'Название должно содержать минимум 2 символа'
    return
  }
  loading.value = true
  try {
    const a = await createAssignment(props.classId, {
      name: name.value.trim(),
      description: description.value.trim() || undefined,
      type: type.value,
      grade_type: gradeType.value,
      grading_type: type.value === 'group' ? gradingType.value : null,
      group_count: type.value === 'group' ? groupCount.value : null,
      deadline: deadline.value ? new Date(deadline.value).toISOString() : null,
      files: files.value,
      links: links.value.filter((l) => l.trim()),
    })
    emit('created', a)
  } catch (e) {
    error.value = extractError(e)
  } finally {
    loading.value = false
  }
}
</script>
