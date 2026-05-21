<template>
  <div class="card feed-item">
    <div class="row-between">
      <div class="row" style="gap: 8px">
        <span class="tag" :class="item.kind === 'announcement' ? 'tag-info' : 'tag-success'">
          {{ item.kind === 'announcement' ? 'Объявление' : 'Задание' }}
        </span>
        <span v-if="item.kind === 'assignment' && deadline" class="tag" :class="deadlineTag">
          до {{ formatDate(deadline) }}
        </span>
      </div>
      <span class="muted" style="font-size: 12px">
        {{ author.username }} · {{ formatDate(item.created_at) }}
      </span>
    </div>

    <!-- ===== View mode ===== -->
    <template v-if="!editing">
      <h3 style="margin-top: 8px; font-size: 16px">
        <RouterLink v-if="item.kind === 'assignment'" :to="`/assignments/${item.id}`">
          {{ assignment.name }}
        </RouterLink>
        <span v-else>{{ announcement.title }}</span>
      </h3>

      <p v-if="item.kind === 'announcement'" style="margin-top: 8px; white-space: pre-wrap">
        {{ announcement.text }}
      </p>
      <p
        v-else-if="assignment.description"
        style="margin-top: 8px; white-space: pre-wrap; color: var(--color-text-muted)"
      >{{ assignment.description }}</p>

      <div v-if="item.kind === 'announcement' && announcement.files.length > 0" class="files">
        <a v-for="f in announcement.files" :key="f.id" :href="f.download_url" target="_blank">
          📎 {{ f.file_name }}
        </a>
      </div>
      <div v-else-if="item.kind === 'assignment' && assignment.materials.length > 0" class="files">
        <a
          v-for="m in assignment.materials"
          :key="m.id"
          :href="m.material_type === 'file' ? (m.download_url || '#') : (m.url || '#')"
          target="_blank"
        >
          {{ m.material_type === 'file' ? '📎' : '🔗' }} {{ m.file_name || m.url }}
        </a>
      </div>

      <div v-if="isTeacher" class="row feed-actions">
        <button class="btn-ghost feed-btn" @click="startEdit">Редактировать</button>
        <button class="btn-ghost feed-btn feed-btn-danger" @click="onDelete">Удалить</button>
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

interface FeedEntry {
  kind: 'announcement' | 'assignment'
  id: string
  created_at: string
  data: Announcement | Assignment
}

const props = defineProps<{ item: FeedEntry; isTeacher: boolean }>()
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
const deadlineTag = computed(() => {
  if (!deadline.value) return ''
  return new Date(deadline.value) < new Date() ? 'tag-danger' : 'tag-warning'
})

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

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
    alert(extractError(e))
  }
}
</script>

<style scoped>
.feed-item {
  transition: box-shadow var(--dur) var(--ease-out), border-color var(--dur) var(--ease-out);
}
.feed-item:hover { box-shadow: var(--shadow); }
.feed-item h3 {
  font-family: var(--font-display);
  font-weight: 600;
}
.feed-item h3 a { color: var(--color-text); }
.feed-item h3 a:hover { color: var(--color-primary); }
.files {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 12px;
}
.files a {
  font-size: 13px;
  padding: 5px 11px;
  background: var(--color-surface-sunken);
  border-radius: var(--radius-pill);
  transition: background var(--dur-fast) var(--ease-out);
}
.files a:hover { background: var(--color-primary-soft); text-decoration: none; }

.feed-actions {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
  gap: 8px;
}
.feed-btn { font-size: 13px; padding: 6px 12px; }
.feed-btn-danger { color: var(--color-danger); }
.feed-btn-danger:hover { background: var(--color-danger-soft); color: var(--color-danger); }

.edit-form { margin-top: 14px; }
</style>
