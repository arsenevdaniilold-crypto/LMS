<template>
  <div class="container page">
    <div v-if="loading" class="card muted">Загрузка…</div>
    <div v-else-if="!solution || !assignment" class="card muted">Решение не найдено</div>
    <template v-else>
      <RouterLink :to="`/assignments/${assignment.id}`" class="muted" style="font-size: 13px">
        ← К заданию «{{ assignment.name }}»
      </RouterLink>
      <h1 class="page-title" style="margin-top: 8px">Решение</h1>

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
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getSolution } from '@/shared/api/solutions'
import { getAssignment } from '@/shared/api/assignments'
import { getClass } from '@/shared/api/classes'
import { onNotification } from '@/shared/stores/notificationStore'
import type { Assignment, Solution } from '@/shared/api/types'
import SolutionCard from '@/shared/ui/SolutionCard.vue'

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
