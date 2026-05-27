<template>
  <div class="card feed-item" :class="kindClass">
    <span class="feed-stripe" aria-hidden="true"></span>
    <div class="feed-head">
      <div class="badges">
        <span class="badge" :class="item.kind === 'announcement' ? 'badge-ann' : 'badge-task'">
          {{ item.kind === 'announcement' ? 'объявление' : 'задание' }}
        </span>
        <span
          v-if="item.kind === 'assignment' && deadlineInfo"
          class="deadline-chip"
          :class="`deadline-${deadlineInfo.severity}`"
        >
          <span class="deadline-dot" aria-hidden="true"></span>
          {{ deadlineInfo.label }}
        </span>
      </div>
      <span class="meta">
        {{ author.username }} · {{ formatDateTime(item.created_at) }}
      </span>
    </div>

    <!-- ===== View mode ===== -->
    <template v-if="!editing">
      <h3 class="feed-title">
        <RouterLink v-if="item.kind === 'assignment'" :to="`/assignments/${item.id}`">
          {{ assignment.name }}
        </RouterLink>
        <span v-else>{{ announcement.title }}</span>
      </h3>

      <p v-if="item.kind === 'announcement'" class="feed-text">{{ announcement.text }}</p>
      <p v-else-if="assignment.description" class="feed-text muted">{{ assignment.description }}</p>

      <div v-if="item.kind === 'announcement' && announcement.files.length > 0" class="chips">
        <a v-for="f in announcement.files" :key="f.id" :href="f.download_url" target="_blank" class="file-chip">
          📎 {{ f.file_name }}
        </a>
      </div>
      <div v-else-if="item.kind === 'assignment' && assignment.materials.length > 0" class="chips">
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

      <div v-if="isTeacher || canDelete" class="feed-actions">
        <RouterLink
          v-if="item.kind === 'assignment'"
          :to="`/assignments/${item.id}`"
          class="btn-ghost feed-btn"
        >Открыть задание</RouterLink>
        <button v-if="isTeacher" class="btn-ghost feed-btn" @click="startEdit">Редактировать</button>
        <button class="btn-soft feed-btn" @click="onDelete">Удалить</button>
      </div>
    </template>

    <!-- ===== Edit mode ===== -->
    <form v-else class="edit-form" @submit.prevent="onSave">
      <template v-if="item.kind === 'announcement'">
        <div class="form-group">
          <label>Заголовок</label>
          <input v-model="editTitle" maxlength="255" />
        </div>
        <div class="form-group" style="margin-bottom: 0">
          <label>Текст</label>
          <textarea v-model="editText" rows="4"></textarea>
        </div>
      </template>
      <template v-else>
        <div class="form-group">
          <label>Название</label>
          <input v-model="editName" maxlength="255" />
        </div>
        <div class="form-group">
          <label>Описание</label>
          <textarea v-model="editDescription" rows="3"></textarea>
        </div>
        <div class="form-group" style="margin-bottom: 0">
          <label>Дедлайн</label>
          <input v-model="editDeadline" type="datetime-local" />
        </div>
      </template>

      <div v-if="editError" class="error-text" style="margin-top: 10px">{{ editError }}</div>

      <div class="row feed-actions">
        <button type="submit" class="btn-primary feed-btn" :disabled="saving">
          {{ saving ? 'Сохраняем…' : 'Сохранить' }}
        </button>
        <button type="button" class="btn-ghost feed-btn" @click="editing = false">Отмена</button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Announcement, Assignment } from '@/shared/api/types'
import { deleteAnnouncement, updateAnnouncement } from '@/shared/api/announcements'
import { deleteAssignment, updateAssignment } from '@/shared/api/assignments'
import { extractError } from '@/shared/api/errors'
import { useToast } from '@/shared/stores/toastStore'
import { describeDeadline, formatDateTime } from '@/shared/lib/dates'

const toast = useToast()

interface FeedEntry {
  kind: 'announcement' | 'assignment'
  id: string
  created_at: string
  data: Announcement | Assignment
}

const props = withDefaults(
  defineProps<{ item: FeedEntry; isTeacher: boolean; canDelete?: boolean }>(),
  { canDelete: false },
)
const emit = defineEmits<{
  (e: 'deleted', kind: 'announcement' | 'assignment', id: string): void
  (e: 'updated', kind: 'announcement' | 'assignment', data: Announcement | Assignment): void
}>()

const announcement = computed(() => props.item.data as Announcement)
const assignment = computed(() => props.item.data as Assignment)
const author = computed(() =>
  props.item.kind === 'announcement' ? announcement.value.author : assignment.value.author,
)
const deadline = computed(() =>
  props.item.kind === 'assignment' ? assignment.value.deadline : null,
)
const deadlineInfo = computed(() => describeDeadline(deadline.value))
const kindClass = computed(() =>
  props.item.kind === 'assignment' ? 'feed-item-task' : 'feed-item-ann',
)

// ----- Edit state -----
const editing = ref(false)
const saving = ref(false)
const editError = ref('')

const editTitle = ref('')
const editText = ref('')
const editName = ref('')
const editDescription = ref('')
const editDeadline = ref('')

/** ISO → value for <input type="datetime-local"> (local, no seconds). */
function isoToLocalInput(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function startEdit() {
  editError.value = ''
  if (props.item.kind === 'announcement') {
    editTitle.value = announcement.value.title
    editText.value = announcement.value.text
  } else {
    editName.value = assignment.value.name
    editDescription.value = assignment.value.description ?? ''
    editDeadline.value = isoToLocalInput(assignment.value.deadline)
  }
  editing.value = true
}

async function onSave() {
  editError.value = ''
  saving.value = true
  try {
    if (props.item.kind === 'announcement') {
      const title = editTitle.value.trim()
      const text = editText.value.trim()
      if (title.length < 1) { editError.value = 'Введите заголовок'; saving.value = false; return }
      if (text.length < 1) { editError.value = 'Введите текст'; saving.value = false; return }
      const updated = await updateAnnouncement(props.item.id, { title, text })
      emit('updated', 'announcement', updated)
    } else {
      const name = editName.value.trim()
      if (name.length < 2) { editError.value = 'Название минимум 2 символа'; saving.value = false; return }
      const updated = await updateAssignment(props.item.id, {
        name,
        description: editDescription.value.trim(),
        deadline: editDeadline.value ? new Date(editDeadline.value).toISOString() : null,
      })
      emit('updated', 'assignment', updated)
    }
    editing.value = false
  } catch (e) {
    editError.value = extractError(e)
  } finally {
    saving.value = false
  }
}

async function onDelete() {
  if (!confirm('Удалить?')) return
  try {
    if (props.item.kind === 'announcement') {
      await deleteAnnouncement(props.item.id)
    } else {
      await deleteAssignment(props.item.id)
    }
    emit('deleted', props.item.kind, props.item.id)
  } catch (e) {
    toast.error(extractError(e))
  }
}
</script>

<style scoped>
.feed-item {
  position: relative;
  padding-left: 30px;
  transition: box-shadow var(--dur) var(--ease-out), transform var(--dur) var(--ease-out);
  overflow: hidden;
}
.feed-item:hover { box-shadow: var(--shadow-lg); transform: translateY(-2px); }

.feed-stripe {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 5px;
  border-radius: var(--radius-lg) 0 0 var(--radius-lg);
  background: var(--color-border);
}
.feed-item-task .feed-stripe {
  background: linear-gradient(180deg, var(--color-primary), #3f8e72);
}
.feed-item-ann .feed-stripe {
  background: linear-gradient(180deg, #5e6bd6, #3e4ab9);
}

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
.deadline-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}
.deadline-safe    { background: var(--color-success-soft); color: var(--color-success); }
.deadline-soon    { background: var(--color-warning-soft); color: var(--color-warning); }
.deadline-today   { background: var(--color-accent-soft);  color: var(--color-warning); animation: deadline-pulse 1.8s ease-in-out infinite; }
.deadline-overdue { background: var(--color-danger-soft);  color: var(--color-danger); }

@keyframes deadline-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(138, 79, 0, 0.35); }
  50%      { box-shadow: 0 0 0 6px rgba(138, 79, 0, 0); }
}

.feed-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.meta { font-size: 13px; color: var(--color-text-muted); }

.feed-title {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.15;
  margin: 4px 0 10px;
}
.feed-title a { color: var(--color-text); }
.feed-title a:hover { color: var(--color-primary); text-decoration: none; }

.feed-text {
  font-size: 16px;
  line-height: 1.5;
  white-space: pre-wrap;
  max-width: 72ch;
}

.feed-actions {
  display: flex;
  flex-wrap: wrap;
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px solid var(--color-border);
  gap: 10px;
}
.feed-btn { font-size: 13px; padding: 8px 14px; }
a.feed-btn { text-decoration: none; }

.edit-form { margin-top: 14px; }
.file-chip { text-decoration: none; }
.file-chip:hover { background: var(--color-bg-3); text-decoration: none; }
</style>
