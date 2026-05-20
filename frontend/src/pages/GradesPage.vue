<template>
  <div class="container page">
    <RouterLink :to="`/classes/${classId}`" class="muted" style="font-size: 13px">
      ← К классу
    </RouterLink>
    <h1 class="page-title" style="margin-top: 8px">Сводная оценок</h1>

    <div v-if="loading" class="card muted">Загрузка…</div>
    <div v-else-if="!data || data.assignments.length === 0" class="card muted">
      Ещё нет заданий
    </div>
    <div v-else class="table-wrap card" style="padding: 0">
      <table class="data-table">
        <thead>
          <tr>
            <th class="sticky-col">Студент</th>
            <th v-for="a in data.assignments" :key="a.id">
              <RouterLink :to="`/assignments/${a.id}`" style="color: inherit; font-weight: inherit">
                {{ a.name }}
              </RouterLink>
              <div class="muted" style="font-size: 11px; font-weight: 400">{{ a.grade_type }}</div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in data.students" :key="s.user_id">
            <td class="sticky-col"><strong>{{ s.username }}</strong></td>
            <td v-for="a in data.assignments" :key="a.id">
              <span v-if="s.grades[a.id]?.grade" class="tag tag-success">
                {{ s.grades[a.id].grade }}
              </span>
              <span v-else-if="s.grades[a.id]?.status" class="tag" :class="statusTag(s.grades[a.id].status!)">
                {{ statusLabel(s.grades[a.id].status!) }}
              </span>
              <span v-else class="muted">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getClassGrades } from '@/shared/api/solutions'
import type { GradesSummary, SolutionStatus } from '@/shared/api/types'

const route = useRoute()
const data = ref<GradesSummary | null>(null)
const loading = ref(true)

const classId = computed(() => String(route.params.id))

function statusLabel(s: SolutionStatus): string {
  switch (s) {
    case 'created':
      return 'черновик'
    case 'submitted':
      return 'сдано'
    case 'returned':
      return 'возвращено'
    case 'pending_redistribution':
      return 'распределение'
    case 'graded':
      return 'оценено'
  }
}

function statusTag(s: SolutionStatus): string {
  switch (s) {
    case 'submitted':
      return 'tag-info'
    case 'returned':
    case 'pending_redistribution':
      return 'tag-warning'
    default:
      return ''
  }
}

onMounted(async () => {
  loading.value = true
  try {
    data.value = await getClassGrades(classId.value)
  } catch {
    data.value = null
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.table-wrap {
  overflow-x: auto;
}
.sticky-col {
  position: sticky;
  left: 0;
  background: var(--color-surface);
}
</style>
