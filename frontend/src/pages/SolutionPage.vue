<template>
  <div class="container page">
    <div v-if="loading" class="card sk-card">
      <span class="sk-line" style="width: 40%"></span>
      <span class="sk-line" style="width: 80%"></span>
      <span class="sk-line" style="width: 65%"></span>
    </div>
    <div v-else-if="!solution || !assignment" class="card muted">Решение не найдено</div>

    <template v-else>
      <RouterLink :to="`/assignments/${assignment.id}`" class="back-link">
        ← К заданию «{{ assignment.name }}»
      </RouterLink>

      <div class="split-title">
        <div>
          <div class="title-kicker">Работа с решениями</div>
          <h1 class="page-title">Моё решение</h1>
        </div>
        <div class="badges">
          <span class="badge" :class="statusBadgeClass">{{ statusLabel }}</span>
          <span v-if="solution.grade" class="badge badge-graded">оценка {{ solution.grade }}</span>
        </div>
      </div>
      <div class="title-line"></div>

      <!-- Timeline -->
      <div class="card timeline-card">
        <StatusTimeline :steps="timelineSteps" />
      </div>

      <!-- Existing solution card with all logic preserved -->
      <SolutionCard
        :solution="solution"
        :assignment="assignment"
        :is-teacher="isTeacher"
        @updated="onUpdated"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getSolution } from '@/shared/api/solutions'
import { getAssignment } from '@/shared/api/assignments'
import { getClass } from '@/shared/api/classes'
import { onNotification } from '@/shared/stores/notificationStore'
import type { Assignment, Solution, SolutionStatus } from '@/shared/api/types'
import SolutionCard from '@/shared/ui/SolutionCard.vue'
import StatusTimeline, { type TimelineStep } from '@/shared/ui/StatusTimeline.vue'

const route = useRoute()
const solution = ref<Solution | null>(null)
const assignment = ref<Assignment | null>(null)
const isTeacher = ref(false)
const loading = ref(true)

function onUpdated(s: Solution) {
  solution.value = s
}

async function reloadSolution() {
  if (!solution.value) return
  try {
    solution.value = await getSolution(solution.value.id)
  } catch {
    /* ignore */
  }
}

const unsub = onNotification((n) => {
  const p = n.payload as Record<string, string>
  if (
    solution.value &&
    p.solution_id === solution.value.id &&
    (n.type === 'solution_graded' ||
      n.type === 'solution_returned' ||
      n.type === 'solution_pending_redistribution')
  ) {
    void reloadSolution()
  }
})
onBeforeUnmount(() => unsub())

/* ---- status helpers ---- */
const statusLabel = computed(() => {
  if (!solution.value) return ''
  switch (solution.value.status) {
    case 'created': return 'черновик'
    case 'submitted': return 'сдано'
    case 'returned': return 'возвращено'
    case 'pending_redistribution': return 'распределение оценки'
    case 'graded': return 'оценено'
  }
})
const statusBadgeClass = computed(() => {
  if (!solution.value) return 'badge-draft'
  switch (solution.value.status) {
    case 'submitted': return 'badge-submitted'
    case 'returned': return 'badge-returned'
    case 'pending_redistribution': return 'badge-redist'
    case 'graded': return 'badge-graded'
    default: return 'badge-draft'
  }
})

/**
 * Build a friendly progress: Создано → Сдано → Проверка → Оценено
 * (extra "Распределение" appears only for group assignments with pending_redistribution).
 */
const timelineSteps = computed<TimelineStep[]>(() => {
  const sol = solution.value
  if (!sol) return []
  const status: SolutionStatus = sol.status
  const isGroup = !!sol.group

  const stateOf = (target: SolutionStatus, fallback: 'done' | 'active' | 'upcoming') => {
    return statePos(status, target, fallback, isGroup)
  }

  const steps: TimelineStep[] = [
    { id: 'created', label: 'Создано', state: 'done', sub: dateOf(sol.created_at) },
    {
      id: 'submitted',
      label: status === 'returned' ? 'Возвращено' : 'Сдано',
      state: status === 'returned' ? 'failed' : stateOf('submitted', 'upcoming'),
      sub: sol.submitted_at ? dateOf(sol.submitted_at) : undefined,
    },
  ]

  if (isGroup) {
    steps.push({
      id: 'redist',
      label: 'Распределение',
      state: status === 'pending_redistribution' ? 'active'
            : (status === 'graded' ? 'done' : 'upcoming'),
    })
  }

  steps.push({
    id: 'graded',
    label: 'Оценено',
    state: status === 'graded' ? 'done'
          : (status === 'pending_redistribution' ? 'upcoming' : 'upcoming'),
    sub: sol.graded_at ? dateOf(sol.graded_at) : undefined,
  })

  // Make the latest non-done step "active" if nothing else is active yet.
  ensureActive(steps)
  return steps
})

function statePos(
  current: SolutionStatus,
  target: SolutionStatus,
  fallback: 'done' | 'active' | 'upcoming',
  _isGroup: boolean,
): 'done' | 'active' | 'upcoming' {
  // Linear order used for "is this step past the current status?"
  const order: SolutionStatus[] = ['created', 'submitted', 'pending_redistribution', 'graded']
  // 'returned' is handled specially by caller.
  const cur = order.indexOf(current === 'returned' ? 'created' : current)
  const tgt = order.indexOf(target)
  if (cur < 0 || tgt < 0) return fallback
  if (tgt < cur) return 'done'
  if (tgt === cur) return current === target ? (current === 'graded' ? 'done' : 'active') : 'active'
  return 'upcoming'
}

function ensureActive(steps: TimelineStep[]) {
  const hasActiveOrFailed = steps.some((s) => s.state === 'active' || s.state === 'failed')
  if (hasActiveOrFailed) return
  // Promote first upcoming → active.
  const idx = steps.findIndex((s) => s.state === 'upcoming')
  if (idx > 0) steps[idx].state = 'active'
}

function dateOf(iso: string | null): string | undefined {
  if (!iso) return undefined
  try {
    return new Date(iso).toLocaleString('ru-RU', {
      day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return undefined
  }
}

onMounted(async () => {
  loading.value = true
  try {
    const id = String(route.params.id)
    solution.value = await getSolution(id)
    assignment.value = await getAssignment(solution.value.assignment_id)
    const cls = await getClass(assignment.value.class_id)
    isTeacher.value = cls.my_role === 'teacher_creator' || cls.my_role === 'teacher'
  } catch {
    solution.value = null
    assignment.value = null
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.back-link {
  font-size: 13px;
  color: var(--color-text-muted);
  display: inline-block;
  margin-bottom: 14px;
}
.timeline-card {
  padding: 22px 30px;
  margin-bottom: 18px;
}
</style>
