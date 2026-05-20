<template>
  <div class="container page">
    <div v-if="loading" class="card muted">Загрузка…</div>
    <div v-else-if="!assignment" class="card muted">Задание не найдено</div>
    <template v-else>
      <RouterLink :to="`/classes/${assignment.class_id}`" class="muted" style="font-size: 13px">
        ← К классу
      </RouterLink>
      <div class="row-between" style="margin-top: 8px; margin-bottom: 16px">
        <h1 class="page-title" style="margin: 0">{{ assignment.name }}</h1>
        <div class="row">
          <span class="tag" :class="assignment.type === 'group' ? 'tag-info' : ''">
            {{ assignment.type === 'group' ? 'групповое' : 'индивидуальное' }}
          </span>
          <span class="tag">шкала {{ assignment.grade_type }}</span>
          <span
            v-if="assignment.deadline"
            class="tag"
            :class="isOverdue ? 'tag-danger' : 'tag-warning'"
          >
            до {{ formatDate(assignment.deadline) }}
          </span>
        </div>
      </div>

      <div class="card" v-if="assignment.description" style="margin-bottom: 16px">
        <p style="white-space: pre-wrap">{{ assignment.description }}</p>
      </div>

      <div v-if="assignment.materials.length > 0" class="card" style="margin-bottom: 16px">
        <h3 class="section-title">Материалы</h3>
        <div class="stack" style="gap: 8px">
          <a
            v-for="m in assignment.materials"
            :key="m.id"
            :href="m.material_type === 'file' ? (m.download_url || '#') : (m.url || '#')"
            target="_blank"
          >
            {{ m.material_type === 'file' ? '📎' : '🔗' }} {{ m.file_name || m.url }}
          </a>
        </div>
      </div>

      <!-- Группы для group-assignment -->
      <div v-if="assignment.type === 'group'" class="card" style="margin-bottom: 16px">
        <div class="row-between">
          <h3 class="section-title" style="margin: 0">Группы</h3>
          <button v-if="!groupsLoading" class="btn-secondary" @click="loadGroups">Обновить</button>
        </div>
        <div v-if="groupsLoading" class="muted">Загрузка…</div>
        <div v-else-if="groups.length === 0" class="muted">Группы ещё не созданы</div>
        <div v-else class="stack" style="margin-top: 12px">
          <div v-for="g in groups" :key="g.id" class="group-row">
            <strong>{{ g.name }}:</strong>
            <span v-for="(m, idx) in g.members" :key="m.user_id">
              {{ m.username }}<span v-if="idx < g.members.length - 1">, </span>
            </span>
          </div>
        </div>
      </div>

      <!-- Список решений (teacher) или собственное решение (student) -->
      <h3 class="section-title" style="margin-top: 24px">
        {{ isTeacher ? 'Решения' : 'Моё решение' }}
      </h3>
      <div v-if="solutionsLoading" class="card muted">Загрузка…</div>
      <template v-else>
        <!-- Студент без решения: форма создания -->
        <SolutionDraftForm
          v-if="!isTeacher && solutions.length === 0"
          :assignment-id="assignment.id"
          @created="onSolutionCreated"
        />

        <!-- Студент с решением: показать карточку -->
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

        <!-- Teacher: все решения -->
        <div v-else-if="isTeacher && solutions.length === 0" class="card muted">
          Ещё нет решений
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
import { useRoute } from 'vue-router'
import { getAssignment, listGroups } from '@/shared/api/assignments'
import { listSolutions } from '@/shared/api/solutions'
import { getClass } from '@/shared/api/classes'
import { onNotification } from '@/shared/stores/notificationStore'
import type { Assignment, Group, Solution } from '@/shared/api/types'
import SolutionDraftForm from '@/shared/ui/SolutionDraftForm.vue'
import SolutionCard from '@/shared/ui/SolutionCard.vue'

const route = useRoute()
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
  if (
    p.assignment_id === assignment.value.id &&
    (n.type === 'solution_graded' ||
      n.type === 'solution_returned' ||
      n.type === 'solution_pending_redistribution')
  ) {
    void loadSolutions()
  }
})
onBeforeUnmount(() => unsub())

const isOverdue = computed(() =>
  assignment.value?.deadline ? new Date(assignment.value.deadline) < new Date() : false,
)

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

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
.group-row {
  padding: 8px 12px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: 14px;
}
</style>
