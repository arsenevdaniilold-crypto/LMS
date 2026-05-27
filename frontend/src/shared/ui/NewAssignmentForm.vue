<template>
  <div class="card create-form">
    <div class="form-head">
      <span class="badge badge-task">задание</span>
      <h3 class="form-title">Новое задание</h3>
      <p class="muted form-sub">Опишите задачу, выберите тип, шкалу оценивания и дедлайн.</p>
    </div>

    <div class="stack">
      <div class="form-group" style="margin-bottom: 0">
        <label>Название задания</label>
        <input v-model="name" placeholder="Лабораторная работа №2" />
      </div>
      <div class="form-group" style="margin-bottom: 0">
        <label>Краткое описание</label>
        <textarea v-model="description" rows="3" placeholder="Описание задачи и ожидаемый результат" />
      </div>

      <div class="row-3">
        <div class="form-group" style="margin-bottom: 0">
          <label>Тип задания</label>
          <select v-model="type">
            <option value="individual">Индивидуальное</option>
            <option value="group">Групповое</option>
          </select>
        </div>
        <div class="form-group" style="margin-bottom: 0">
          <label>Шкала оценок</label>
          <select v-model="gradeType">
            <option value="0-100">0–100</option>
            <option value="0-5">0–5</option>
            <option value="0-1">0–1 (зачёт / незачёт)</option>
          </select>
        </div>
        <div class="form-group" style="margin-bottom: 0">
          <label>Дедлайн</label>
          <input v-model="deadline" type="datetime-local" />
        </div>
      </div>

      <div v-if="type === 'group'" class="card group-settings">
        <div class="row-2">
          <div class="form-group" style="margin-bottom: 0">
            <label>Количество групп (N)</label>
            <input v-model.number="groupCount" type="number" min="1" max="100" placeholder="4" />
          </div>
          <div class="form-group" style="margin-bottom: 0">
            <label>Тип оценивания</label>
            <select v-model="gradingType">
              <option value="uniform">Единая оценка на команду</option>
              <option value="individual">Распределяется студентами</option>
            </select>
          </div>
        </div>
        <p class="muted" style="font-size: 13px; margin-top: 12px">
          Преподаватель распределяет студентов вручную либо система раскладывает их автоматически по N группам.
        </p>
      </div>

      <div class="stack" style="gap: 10px">
        <FileInput v-model="files" multiple />
        <div>
          <label style="font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.08em; color: var(--color-text-muted)">Ссылки на материалы</label>
          <div v-for="(_, idx) in links" :key="idx" class="row" style="margin-top: 8px; gap: 8px">
            <input v-model="links[idx]" placeholder="https://..." />
            <button class="btn-ghost" style="padding: 10px 14px" @click="links.splice(idx, 1)">×</button>
          </div>
          <button class="btn-ghost" style="margin-top: 10px" @click="links.push('')">
            + Добавить ссылку
          </button>
        </div>
      </div>

      <div v-if="error" class="error-text">{{ error }}</div>
      <div class="row">
        <button class="btn-accent" :disabled="loading" @click="submit">
          {{ loading ? 'Создаём…' : 'Создать задание' }}
        </button>
        <button class="btn-ghost" @click="$emit('cancel')">Отмена</button>
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
.row-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.group-settings {
  background: var(--color-surface-sunken);
  border-color: var(--color-border);
  box-shadow: none;
  padding: 18px 20px;
}
@media (max-width: 760px) {
  .row-3 { grid-template-columns: 1fr; }
  .row-2 { grid-template-columns: 1fr; }
}
</style>
