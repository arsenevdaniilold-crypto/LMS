<template>
  <div class="container page">
    <RouterLink :to="`/classes/${classId}`" class="back-link">
      ← К классу
    </RouterLink>

    <div class="title-kicker">Успеваемость</div>
    <h1 class="page-title">Сводная оценок</h1>
    <div class="title-line"></div>

    <div v-if="loading" class="card sk-card">
      <span class="sk-line" style="width: 30%"></span>
      <span class="sk-line" style="width: 90%"></span>
      <span class="sk-line" style="width: 90%"></span>
      <span class="sk-line" style="width: 90%"></span>
    </div>

    <div v-else-if="!data || data.assignments.length === 0" class="empty-state reveal">
      <div class="empty-glyph">✦</div>
      <h3 class="empty-title">Ещё нет заданий</h3>
      <p class="muted">Оценки появятся, когда в классе будут задания и решения.</p>
    </div>

    <template v-else>
      <!-- Summary stats -->
      <div class="stat-grid">
        <div class="stat">
          <div class="stat-label">Студентов</div>
          <div class="stat-value" style="color: var(--color-primary)">{{ data.students.length }}</div>
          <div class="stat-sub">учитываются в таблице</div>
        </div>
        <div class="stat">
          <div class="stat-label">Проверенных решений</div>
          <div class="stat-value" style="color: var(--color-accent-hover)">{{ gradedCount }}</div>
          <div class="stat-sub">из {{ totalAttempts }} отправленных</div>
        </div>
        <div class="stat">
          <div class="stat-label">Средний балл</div>
          <div class="stat-value">{{ averageDisplay }}</div>
          <div class="stat-sub">по нормированной шкале 0–100</div>
        </div>
      </div>

      <div class="table-wrap card" style="padding: 0">
        <table class="cf-table">
          <thead>
            <tr>
              <th class="sticky-col">Студент</th>
              <th v-for="a in data.assignments" :key="a.id">
                <RouterLink :to="`/assignments/${a.id}`" class="th-link">
                  {{ a.name }}
                </RouterLink>
                <div class="th-sub">шкала {{ a.grade_type }}</div>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in data.students" :key="s.user_id">
              <td class="sticky-col td-strong">{{ s.username }}</td>
              <td
                v-for="a in data.assignments"
                :key="a.id"
                class="heat-cell"
                :style="heatStyle(s.grades[a.id]?.grade, a.grade_type)"
              >
                <span v-if="s.grades[a.id]?.grade" class="heat-grade">
                  {{ s.grades[a.id].grade }}
                </span>
                <span
                  v-else-if="s.grades[a.id]?.status"
                  class="badge"
                  :class="statusBadgeClass(s.grades[a.id].status!)"
                >
                  {{ statusLabel(s.grades[a.id].status!) }}
                </span>
                <span v-else class="muted">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Heatmap legend -->
      <div class="heat-legend">
        <span class="legend-label">Низкая</span>
        <span class="legend-gradient"></span>
        <span class="legend-label">Средняя</span>
        <span class="legend-gradient legend-gradient-2"></span>
        <span class="legend-label">Высокая</span>
      </div>
    </template>
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

function statusBadgeClass(s: SolutionStatus): string {
  switch (s) {
    case 'submitted':
      return 'badge-submitted'
    case 'returned':
      return 'badge-returned'
    case 'pending_redistribution':
      return 'badge-redist'
    case 'graded':
      return 'badge-graded'
    default:
      return 'badge-draft'
  }
}

/** Normalize grade to 0..1 ratio depending on grade_type scale. */
function gradeRatio(rawGrade: string | null | undefined, scale: string): number | null {
  if (!rawGrade) return null
  const num = parseFloat(rawGrade.replace(',', '.'))
  if (Number.isNaN(num)) return null
  if (scale === '0-1') return Math.max(0, Math.min(1, num))
  if (scale === '0-5') return Math.max(0, Math.min(1, num / 5))
  // default 0-100
  return Math.max(0, Math.min(1, num / 100))
}

/** Heatmap background by grade: red→amber→emerald, transparent on no grade. */
function heatStyle(rawGrade: string | null | undefined, scale: string): Record<string, string> {
  const r = gradeRatio(rawGrade, scale)
  if (r === null) return {}
  // Color stops:
  //   0.00 → #b63a2b (danger)
  //   0.50 → #c79143 (amber)
  //   1.00 → #2c6b52 (emerald)
  let bg: string
  if (r < 0.5) {
    const t = r / 0.5 // 0..1 from danger → amber
    bg = mix('#b63a2b', '#c79143', t)
  } else {
    const t = (r - 0.5) / 0.5 // 0..1 from amber → emerald
    bg = mix('#c79143', '#2c6b52', t)
  }
  // Soften: use 20–55% alpha mixed onto paper background.
  const alpha = 0.22 + r * 0.34 // 0.22..0.56
  return {
    background: hexToRgba(bg, alpha),
    color: r > 0.55 ? 'var(--color-text)' : 'var(--color-text)',
  }
}

/* ---- color helpers (pure, dependency-free) ---- */
function mix(a: string, b: string, t: number): string {
  const ca = parseHex(a)
  const cb = parseHex(b)
  const r = Math.round(ca[0] + (cb[0] - ca[0]) * t)
  const g = Math.round(ca[1] + (cb[1] - ca[1]) * t)
  const bl = Math.round(ca[2] + (cb[2] - ca[2]) * t)
  return `#${[r, g, bl].map((n) => n.toString(16).padStart(2, '0')).join('')}`
}
function parseHex(hex: string): [number, number, number] {
  const h = hex.replace('#', '')
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]
}
function hexToRgba(hex: string, alpha: number): string {
  const [r, g, b] = parseHex(hex)
  return `rgba(${r}, ${g}, ${b}, ${alpha.toFixed(3)})`
}

/* ---- summary stats ---- */
const gradedCount = computed(() => {
  if (!data.value) return 0
  let n = 0
  for (const s of data.value.students) {
    for (const a of data.value.assignments) {
      if (s.grades[a.id]?.grade) n++
    }
  }
  return n
})
const totalAttempts = computed(() => {
  if (!data.value) return 0
  let n = 0
  for (const s of data.value.students) {
    for (const a of data.value.assignments) {
      const cell = s.grades[a.id]
      if (cell?.grade || cell?.status) n++
    }
  }
  return n
})
const averageDisplay = computed(() => {
  if (!data.value) return '—'
  const ratios: number[] = []
  for (const s of data.value.students) {
    for (const a of data.value.assignments) {
      const r = gradeRatio(s.grades[a.id]?.grade, a.grade_type)
      if (r !== null) ratios.push(r)
    }
  }
  if (ratios.length === 0) return '—'
  const avg = ratios.reduce((acc, x) => acc + x, 0) / ratios.length
  return (avg * 100).toFixed(1)
})

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
.back-link {
  font-size: 13px;
  color: var(--color-text-muted);
  display: inline-block;
  margin-bottom: 14px;
}

.th-link { color: inherit; font-weight: 800; }
.th-link:hover { color: var(--color-primary); text-decoration: none; }
.th-sub {
  margin-top: 4px;
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: lowercase;
  color: var(--color-text-subtle);
}

.sticky-col {
  position: sticky;
  left: 0;
  background: var(--color-surface);
  z-index: 1;
}
thead .sticky-col { background: var(--color-bg-2); }

.heat-cell {
  text-align: center;
  font-weight: 800;
  transition: filter var(--dur-fast) var(--ease-out);
}
.heat-cell:hover { filter: brightness(0.97); }
.heat-grade {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 800;
  letter-spacing: -0.01em;
}

/* legend */
.heat-legend {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin-top: 20px;
  padding: 10px 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  font-size: 12.5px;
  font-weight: 700;
  color: var(--color-text-muted);
  letter-spacing: 0.04em;
}
.legend-label { text-transform: uppercase; }
.legend-gradient {
  width: 70px;
  height: 10px;
  border-radius: 5px;
  background: linear-gradient(90deg, rgba(182, 58, 43, 0.5), rgba(199, 145, 67, 0.5));
}
.legend-gradient-2 {
  background: linear-gradient(90deg, rgba(199, 145, 67, 0.5), rgba(44, 107, 82, 0.55));
}

/* empty */
.empty-state {
  text-align: center;
  padding: 64px 24px;
  border: 1px dashed var(--color-border-strong);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}
.empty-glyph { font-size: 32px; color: var(--color-primary); margin-bottom: 14px; }
.empty-title { font-family: var(--font-display); font-size: 22px; font-weight: 800; margin-bottom: 8px; }
</style>
