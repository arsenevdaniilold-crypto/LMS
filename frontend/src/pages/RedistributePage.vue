<template>
  <div class="container page">
    <div v-if="loading" class="card sk-card">
      <span class="sk-line" style="width: 40%"></span>
      <span class="sk-line" style="width: 80%"></span>
      <span class="sk-line" style="width: 65%"></span>
    </div>
    <div v-else-if="!solution || !assignment" class="card muted">Решение не найдено</div>
    <template v-else>
      <RouterLink :to="`/solutions/${solution.id}`" class="muted" style="font-size: 13px">
        ← К решению
      </RouterLink>
      <h1 class="page-title" style="margin-top: 8px">Распределение оценки</h1>

      <div class="card" style="margin-bottom: 16px">
        <div class="stack">
          <div>
            <span class="muted">Задание:</span> <strong>{{ assignment.name }}</strong>
          </div>
          <div>
            <span class="muted">Оценка команды:</span>
            <strong>{{ solution.grade }}</strong>
            <span class="muted"> · шкала {{ assignment.grade_type }}</span>
          </div>
          <div>
            <span class="muted">Группа:</span> <strong>{{ solution.group?.name }}</strong>
            ({{ solution.group?.members.length }} участников)
          </div>
        </div>
      </div>

      <div v-if="solution.status !== 'pending_redistribution'" class="notice-warning">
        Это решение больше не в состоянии перераспределения. Текущий статус: {{ solution.status }}.
      </div>

      <template v-else>
        <div class="card">
          <h3 class="section-title">Оценки участникам</h3>
          <div class="stack">
            <div v-for="m in solution.group?.members" :key="m.user_id" class="row" style="gap: 12px">
              <span style="flex: 1">{{ m.username }}</span>
              <input
                v-model.number="grades[m.user_id]"
                type="number"
                step="0.01"
                :min="0"
                :max="gradeMax"
                style="max-width: 120px"
              />
            </div>
          </div>

          <div class="stats">
            <div class="row" style="gap: 20px">
              <div>
                <div class="muted" style="font-size: 12px">Текущее среднее</div>
                <div class="big-number" :class="meanColorClass">{{ mean.toFixed(2) }}</div>
              </div>
              <div>
                <div class="muted" style="font-size: 12px">Должно быть</div>
                <div class="big-number">{{ solution.grade }}</div>
              </div>
              <div>
                <div class="muted" style="font-size: 12px">Разница</div>
                <div class="big-number" :class="meanColorClass">{{ diff.toFixed(3) }}</div>
              </div>
            </div>
          </div>

          <div v-if="rangeError" class="error-text" style="margin-top: 12px">{{ rangeError }}</div>
          <div v-if="submitError" class="error-text" style="margin-top: 12px">{{ submitError }}</div>

          <div class="row" style="margin-top: 16px">
            <button
              class="btn-primary"
              :disabled="!canSubmit || submitting"
              @click="onSubmit"
            >
              {{ submitting ? 'Сохраняем…' : 'Подтвердить распределение' }}
            </button>
            <span v-if="!canSubmit && !rangeError" class="muted" style="font-size: 13px">
              Среднее должно совпадать с оценкой команды (±0.005)
            </span>
          </div>
        </div>
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getSolution, redistributeSolution } from '@/shared/api/solutions'
import { getAssignment } from '@/shared/api/assignments'
import { extractError } from '@/shared/api/errors'
import type { Assignment, Solution } from '@/shared/api/types'
import {
  REDISTRIBUTION_TOLERANCE,
  allFilled as allFilledFn,
  canRedistribute,
  computeMean,
  gradeMaxFor,
  isInRange,
  meanDiff,
} from '@/shared/lib/redistribution'

const route = useRoute()
const router = useRouter()
const solution = ref<Solution | null>(null)
const assignment = ref<Assignment | null>(null)
const loading = ref(true)
const grades = reactive<Record<string, number>>({})
const submitting = ref(false)
const submitError = ref('')

const memberValues = computed(() =>
  (solution.value?.group?.members || []).map((m) => grades[m.user_id]),
)

const gradeMax = computed(() => gradeMaxFor(assignment.value?.grade_type))

const mean = computed(() => computeMean(memberValues.value))

const target = computed(() => Number(solution.value?.grade || 0))
const diff = computed(() => meanDiff(mean.value, target.value))

const rangeError = computed(() => {
  const members = solution.value?.group?.members || []
  for (const m of members) {
    const v = grades[m.user_id]
    if (typeof v !== 'number' || isNaN(v)) continue
    if (!isInRange(v, gradeMax.value)) {
      return `Оценка для ${m.username} вне диапазона 0–${gradeMax.value}`
    }
  }
  return ''
})

const allFilled = computed(() => allFilledFn(memberValues.value))

const canSubmit = computed(() =>
  canRedistribute(memberValues.value, target.value, gradeMax.value),
)

const meanColorClass = computed(() => {
  if (!allFilled.value) return ''
  return diff.value <= REDISTRIBUTION_TOLERANCE ? 'mean-ok' : 'mean-bad'
})

watch(
  () => solution.value?.group?.members,
  (members) => {
    if (!members) return
    for (const m of members) {
      if (!(m.user_id in grades)) {
        grades[m.user_id] = Number(solution.value?.grade || 0)
      }
    }
  },
)

async function onSubmit() {
  if (!solution.value) return
  submitError.value = ''
  submitting.value = true
  try {
    const entries = Object.entries(grades).map(([user_id, grade]) => ({ user_id, grade }))
    await redistributeSolution(solution.value.id, entries)
    await router.push(`/solutions/${solution.value.id}`)
  } catch (e) {
    submitError.value = extractError(e)
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  loading.value = true
  try {
    const id = String(route.params.id)
    solution.value = await getSolution(id)
    assignment.value = await getAssignment(solution.value.assignment_id)
  } catch {
    solution.value = null
    assignment.value = null
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.notice-warning {
  padding: 14px 16px;
  background: var(--color-warning-soft);
  color: var(--color-warning);
  border-radius: var(--radius);
  font-size: 14px;
  margin-bottom: 16px;
}
.stats {
  margin-top: 22px;
  padding-top: 20px;
  border-top: 1px solid var(--color-border);
}
.stats .row { gap: 14px !important; }
.stats .row > div {
  flex: 1;
  padding: 14px 16px;
  background: var(--color-surface-sunken);
  border-radius: var(--radius);
}
.big-number {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--color-text);
  margin-top: 4px;
}
.big-number.mean-ok { color: var(--color-success); }
.big-number.mean-bad { color: var(--color-danger); }
</style>
