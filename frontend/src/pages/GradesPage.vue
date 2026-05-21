<template>
  <div class="container page">
    <RouterLink :to="`/classes/${classId}`" class="back-link">
      ← К классу
    </RouterLink>
    <header class="grades-hero reveal">
      <p class="hero-eyebrow">Успеваемость</p>
      <h1 class="page-title">Сводная оценок</h1>
    </header>

    <div v-if="loading" class="card muted">Загрузка…</div>
    <div v-else-if="!data || data.assignments.length === 0" class="empty-state reveal">
      <div class="empty-glyph">✦</div>
      <h3 class="empty-title">Ещё нет заданий</h3>
      <p class="muted">Оценки появятся, когда в классе будут задания и решения.</p>
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
.back-link { font-size: 13px; color: var(--color-text-muted); }
.grades-hero {
  margin: 10px 0 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--color-border);
}
.hero-eyebrow {
  font-size: 12.5px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-primary);
  margin-bottom: 8px;
}
.table-wrap { overflow-x: auto; }
.sticky-col {
  position: sticky;
  left: 0;
  background: var(--color-surface);
  z-index: 1;
}
thead .sticky-col { background: var(--color-surface-sunken); }
.empty-state {
  text-align: center;
  padding: 64px 24px;
  border: 1px dashed var(--color-border-strong);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}
.empty-glyph { font-size: 32px; color: var(--color-primary); margin-bottom: 14px; }
.empty-title { font-family: var(--font-display); font-size: 22px; margin-bottom: 8px; }
</style>
