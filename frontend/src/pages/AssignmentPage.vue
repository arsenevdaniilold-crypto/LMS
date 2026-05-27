<template>
  <div class="container page">
    <div v-if="loading" class="card sk-card">
      <span class="sk-line" style="width: 40%"></span>
      <span class="sk-line" style="width: 75%"></span>
      <span class="sk-line" style="width: 60%"></span>
    </div>
    <div v-else-if="!assignment" class="card muted">Задание не найдено</div>
    <template v-else>
      <RouterLink :to="`/classes/${assignment.class_id}`" class="back-link">
        ← К классу
      </RouterLink>

      <div class="split-title">
        <div>
          <div class="title-kicker">Просмотр задания</div>
          <h1 class="page-title">{{ assignment.name }}</h1>
          <div class="badges" style="margin-top: 10px">
            <span class="badge" :class="assignment.type === 'group' ? 'badge-task' : 'badge-student'">
              {{ assignment.type === 'group' ? 'групповое' : 'индивидуальное' }}
            </span>
            <span class="badge badge-graded">шкала {{ assignment.grade_type }}</span>
            <span
              v-if="deadlineInfo"
              class="deadline-chip"
              :class="`deadline-${deadlineInfo.severity}`"
            >
              <span class="deadline-dot" aria-hidden="true"></span>
              {{ deadlineInfo.label }}
            </span>
          </div>
        </div>
      </div>
      <div class="title-line"></div>

      <div class="card" v-if="assignment.description" style="margin-bottom: 18px">
        <p class="assignment-desc">{{ assignment.description }}</p>
      </div>

      <div v-if="assignment.materials.length > 0" class="card" style="margin-bottom: 18px">
        <h3 class="section-title">Материалы</h3>
        <div class="chips">
          <a
            v-for="m in assignment.materials"
            :key="m.id"
            :href="m.material_type === 'file' ? (m.download_url || '#') : (m.url || '#')"
            target="_blank"
            class="file-chip"
          >
            {{ m.material_type === 'file' ? '📎' : '🔗' }} {{ m.file_name || m.url }}
          </a>
        </div>
      </div>

      <!-- Группы для group-assignment -->
      <div v-if="assignment.type === 'group'" class="card" style="margin-bottom: 18px">
        <div class="row-between" style="margin-bottom: 14px">
          <h3 class="section-title" style="margin: 0">Группы</h3>
          <button v-if="!groupsLoading" class="btn-ghost" @click="loadGroups">Обновить</button>
        </div>
        <div v-if="groupsLoading" class="muted">Загрузка…</div>
        <div v-else-if="groups.length === 0" class="muted">Группы ещё не созданы</div>
        <div v-else class="catalog">
          <div v-for="(g, gi) in groups" :key="g.id" class="card group-card">
            <div class="badges">
              <span class="badge badge-task">группа {{ gi + 1 }}</span>
            </div>
            <div class="group-name">{{ g.name }}</div>
            <div class="group-members">
              <span v-for="(m, idx) in g.members" :key="m.user_id">
                {{ m.username }}<span v-if="idx < g.members.length - 1">, </span>
              </span>
            </div>
          </div>
        </div>
      </div>

      <h3 class="section-title" style="margin-top: 26px">
        {{ isTeacher ? 'Решения' : 'Моё решение' }}
      </h3>
      <div v-if="solutionsLoading" class="card sk-card">
        <span class="sk-line" style="width: 40%"></span>
        <span class="sk-line" style="width: 75%"></span>
        <span class="sk-line" style="width: 60%"></span>
      </div>
      <template v-else>
        <SolutionDraftForm
          v-if="!isTeacher && solutions.length === 0"
          :assignment-id="assignment.id"
          @created="onSolutionCreated"
        />

        <div v-else-if="!isTeacher && solutions.length > 0" class="stack">
          <SolutionCard
            v-for="s in solutions"
            :key="s.id"
            :solution="s"
            :assignment="assignment"
            :is-teacher="false"
            @updated="onSolutionUpdated"
          />
        </div>

        <div v-else-if="isTeacher && solutions.length === 0" class="empty-state">
          <div class="empty-glyph">✦</div>
          <h3 class="empty-title">Ещё нет решений</h3>
          <p class="muted">Карточки появятся, как только студенты сдадут работу.</p>
        </div>
        <div v-else class="stack">
          <SolutionCard
            v-for="s in solutions"
            :key="s.id"
            :solution="s"
            :assignment="assignment"
            :is-teacher="true"
            @updated="onSolutionUpdated"
          />
        </div>
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getAssignment, listGroups } from '@/shared/api/assignments'
import { listSolutions } from '@/shared/api/solutions'
import { getClass } from '@/shared/api/classes'
import { onNotification } from '@/shared/stores/notificationStore'
import type { Assignment, Group, Solution } from '@/shared/api/types'
import SolutionDraftForm from '@/shared/ui/SolutionDraftForm.vue'
import SolutionCard from '@/shared/ui/SolutionCard.vue'
import { describeDeadline } from '@/shared/lib/dates'

const route = useRoute()
const router = useRouter()
const assignment = ref<Assignment | null>(null)
const groups = ref<Group[]>([])
const solutions = ref<Solution[]>([])
const loading = ref(true)
const groupsLoading = ref(false)
const solutionsLoading = ref(false)
const isTeacher = ref(false)

const unsub = onNotification((n) => {
  const p = n.payload as Record<string, string>
  if (!assignment.value) return
  if (p.assignment_id !== assignment.value.id) return

  if (
    n.type === 'solution_graded' ||
    n.type === 'solution_returned' ||
    n.type === 'solution_pending_redistribution'
  ) {
    void loadSolutions()
  } else if (n.type === 'assignment_updated') {
    void reloadAssignment()
  } else if (n.type === 'assignment_deleted') {
    // The assignment is gone — leave the page.
    const classId = assignment.value.class_id
    void router.push(`/classes/${classId}`)
  }
})
onBeforeUnmount(() => unsub())

async function reloadAssignment() {
  if (!assignment.value) return
  try {
    assignment.value = await getAssignment(assignment.value.id)
  } catch {
    /* keep current view if reload fails */
  }
}

const deadlineInfo = computed(() => describeDeadline(assignment.value?.deadline ?? null))

async function loadGroups() {
  if (!assignment.value) return
  groupsLoading.value = true
  try {
    groups.value = await listGroups(assignment.value.id)
  } finally {
    groupsLoading.value = false
  }
}

async function loadSolutions() {
  if (!assignment.value) return
  solutionsLoading.value = true
  try {
    solutions.value = await listSolutions(assignment.value.id)
  } finally {
    solutionsLoading.value = false
  }
}

function onSolutionCreated(s: Solution) {
  solutions.value = [s, ...solutions.value]
}

function onSolutionUpdated(s: Solution) {
  solutions.value = solutions.value.map((x) => (x.id === s.id ? s : x))
}

onMounted(async () => {
  loading.value = true
  try {
    const id = String(route.params.id)
    assignment.value = await getAssignment(id)
    const cls = await getClass(assignment.value.class_id)
    isTeacher.value = cls.my_role === 'teacher_creator' || cls.my_role === 'teacher'
    if (assignment.value.type === 'group') {
      await loadGroups()
    }
    await loadSolutions()
  } catch {
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
.assignment-desc {
  font-size: 17px;
  line-height: 1.55;
  white-space: pre-wrap;
}

.catalog {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px;
}
.group-card {
  padding: 18px 20px;
  transition: transform var(--dur) var(--ease-out), box-shadow var(--dur) var(--ease-out);
}
.group-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg); }
.group-name {
  font-family: var(--font-display);
  font-size: 19px;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin: 10px 0 6px;
}
.group-members {
  font-size: 14px;
  color: var(--color-text-muted);
  line-height: 1.5;
}

.empty-state {
  text-align: center;
  padding: 48px 24px;
  border: 1px dashed var(--color-border-strong);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}
.empty-glyph { font-size: 28px; color: var(--color-primary); margin-bottom: 10px; }
.empty-title { font-family: var(--font-display); font-size: 20px; font-weight: 800; margin-bottom: 6px; }

/* Deadline chip styles (same look as FeedItem) */
.deadline-chip {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 6px 12px 6px 10px;
  border-radius: var(--radius-pill);
  font-size: 12.5px;
  font-weight: 800;
  background: var(--color-bg-2);
  color: var(--color-text-muted);
  border: 1px solid transparent;
}
.deadline-dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
.deadline-safe    { background: var(--color-success-soft); color: var(--color-success); }
.deadline-soon    { background: var(--color-warning-soft); color: var(--color-warning); }
.deadline-today   { background: var(--color-accent-soft);  color: var(--color-warning); }
.deadline-overdue { background: var(--color-danger-soft);  color: var(--color-danger); }
</style>
