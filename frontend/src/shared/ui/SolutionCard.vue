<template>
  <div class="card">
    <div class="row-between">
      <div class="row">
        <span class="tag" :class="statusTag">{{ statusLabel }}</span>
        <span v-if="solution.grade" class="tag tag-success">Оценка: {{ solution.grade }}</span>
        <span v-if="solution.group" class="tag tag-info">Группа: {{ solution.group.name }}</span>
      </div>
      <span class="muted" style="font-size: 12px">
        {{ solution.creator_username }} · {{ formatDate(solution.updated_at) }}
      </span>
    </div>

    <div style="margin-top: 12px">
      <RouterLink :to="`/solutions/${solution.id}`" style="font-size: 14px; font-weight: 500">
        Открыть решение →
      </RouterLink>
    </div>

    <p v-if="solution.text" style="white-space: pre-wrap; margin-top: 12px">{{ solution.text }}</p>
    <div v-if="solution.files.length > 0" class="files">
      <a v-for="f in solution.files" :key="f.id" :href="f.download_url" target="_blank">
        📎 {{ f.file_name }}
      </a>
    </div>

    <!-- Действия студента -->
    <div v-if="!isTeacher && canEdit" class="row" style="margin-top: 12px">
      <button class="btn-secondary" @click="showEdit = !showEdit">
        {{ showEdit ? 'Скрыть редактирование' : 'Редактировать' }}
      </button>
      <button class="btn-primary" :disabled="actionLoading" @click="onSubmit">
        {{ solution.status === 'returned' ? 'Сдать заново' : 'Сдать' }}
      </button>
    </div>

    <div v-if="showEdit" class="card" style="margin-top: 12px; background: var(--color-surface-sunken)">
      <div class="stack">
        <div class="form-group" style="margin-bottom: 0">
          <label>Текст решения</label>
          <textarea v-model="editText" rows="5" />
        </div>
        <FileInput v-model="editFiles" multiple />
        <div class="row">
          <button class="btn-primary" :disabled="actionLoading" @click="onSaveEdit">
            Сохранить
          </button>
        </div>
        <div class="muted" style="font-size: 12px">
          При сохранении файлы заменяются на новый набор. Чтобы оставить старые, перевыберите их.
        </div>
      </div>
    </div>

    <!-- Перераспределение для group+individual: ссылка -->
    <div v-if="solution.status === 'pending_redistribution'" class="row" style="margin-top: 12px">
      <RouterLink :to="`/solutions/${solution.id}/redistribute`" class="btn-primary">
        Распределить оценки
      </RouterLink>
    </div>

    <!-- Действия преподавателя -->
    <div v-if="isTeacher && solution.status === 'submitted'" class="card" style="margin-top: 12px; background: var(--color-surface-sunken)">
      <div class="stack">
        <div class="row" style="gap: 8px">
          <input
            v-model.number="gradeInput"
            type="number"
            step="0.01"
            :min="0"
            :max="gradeMax"
            placeholder="Оценка"
            style="max-width: 120px"
          />
          <button class="btn-primary" :disabled="actionLoading" @click="onGrade">
            Поставить оценку
          </button>
          <button class="btn-secondary" :disabled="actionLoading" @click="onReturn">
            Вернуть на доработку
          </button>
        </div>
        <div class="muted" style="font-size: 12px">
          Шкала: {{ assignment.grade_type }}
          <span v-if="assignment.type === 'group' && assignment.grading_type === 'individual'">
            · после оценки студенты распределяют её между собой
          </span>
        </div>
        <div v-if="actionError" class="error-text">{{ actionError }}</div>
      </div>
    </div>

    <!-- Финальное распределение (если есть) -->
    <div v-if="solution.redistribution && solution.redistribution.length > 0" style="margin-top: 12px">
      <div class="muted" style="font-size: 13px; margin-bottom: 6px">Финальное распределение:</div>
      <div class="row" style="gap: 12px; flex-wrap: wrap">
        <span v-for="r in solution.redistribution" :key="r.user_id" class="tag tag-success">
          {{ r.username }}: {{ r.grade }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  gradeSolution,
  returnSolution,
  submitSolution,
  updateSolution,
} from '@/shared/api/solutions'
import { extractError } from '@/shared/api/errors'
import { useToast } from '@/shared/stores/toastStore'

const toast = useToast()
import type { Assignment, Solution } from '@/shared/api/types'
import FileInput from './FileInput.vue'

const props = defineProps<{ solution: Solution; assignment: Assignment; isTeacher: boolean }>()
const emit = defineEmits<{ (e: 'updated', s: Solution): void }>()

const showEdit = ref(false)
const editText = ref(props.solution.text || '')
const editFiles = ref<File[]>([])
const gradeInput = ref<number | null>(null)
const actionLoading = ref(false)
const actionError = ref('')

const canEdit = computed(
  () => props.solution.status === 'created' || props.solution.status === 'returned',
)

const statusLabel = computed(() => {
  switch (props.solution.status) {
    case 'created':
      return 'черновик'
    case 'submitted':
      return 'сдано'
    case 'returned':
      return 'возвращено'
    case 'graded':
      return 'оценено'
    case 'pending_redistribution':
      return 'ожидает распределения'
    default:
      return props.solution.status
  }
})

const statusTag = computed(() => {
  switch (props.solution.status) {
    case 'graded':
      return 'tag-success'
    case 'submitted':
      return 'tag-info'
    case 'returned':
      return 'tag-warning'
    case 'pending_redistribution':
      return 'tag-warning'
    default:
      return ''
  }
})

const gradeMax = computed(() => {
  if (props.assignment.grade_type === '0-5') return 5
  if (props.assignment.grade_type === '0-1') return 1
  return 100
})

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function onSaveEdit() {
  actionLoading.value = true
  try {
    const s = await updateSolution(props.solution.id, editText.value, editFiles.value)
    emit('updated', s)
    showEdit.value = false
    editFiles.value = []
  } catch (e) {
    toast.error(extractError(e))
  } finally {
    actionLoading.value = false
  }
}

async function onSubmit() {
  actionLoading.value = true
  try {
    const s = await submitSolution(props.solution.id)
    emit('updated', s)
  } catch (e) {
    toast.error(extractError(e))
  } finally {
    actionLoading.value = false
  }
}

async function onGrade() {
  actionError.value = ''
  if (gradeInput.value == null) {
    actionError.value = 'Введите оценку'
    return
  }
  actionLoading.value = true
  try {
    const s = await gradeSolution(props.solution.id, gradeInput.value)
    emit('updated', s)
  } catch (e) {
    actionError.value = extractError(e)
  } finally {
    actionLoading.value = false
  }
}

async function onReturn() {
  actionLoading.value = true
  try {
    const s = await returnSolution(props.solution.id)
    emit('updated', s)
  } catch (e) {
    toast.error(extractError(e))
  } finally {
    actionLoading.value = false
  }
}
</script>

<style scoped>
.card { box-shadow: var(--shadow-sm); }
.files {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 10px;
}
.files a {
  font-size: 13px;
  padding: 5px 11px;
  background: var(--color-surface-sunken);
  border-radius: var(--radius-pill);
}
.files a:hover { background: var(--color-primary-soft); text-decoration: none; }
</style>
