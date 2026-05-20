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

    <div v-if="isTeacher" class="row" style="margin-top: 10px">
      <button class="btn-secondary" style="font-size: 12px; padding: 4px 8px" @click="onDelete">
        Удалить
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Announcement, Assignment } from '@/shared/api/types'
import { deleteAnnouncement } from '@/shared/api/announcements'
import { deleteAssignment } from '@/shared/api/assignments'
import { extractError } from '@/shared/api/errors'

interface FeedEntry {
  kind: 'announcement' | 'assignment'
  id: string
  created_at: string
  data: Announcement | Assignment
}

const props = defineProps<{ item: FeedEntry; isTeacher: boolean }>()
const emit = defineEmits<{ (e: 'deleted', kind: 'announcement' | 'assignment', id: string): void }>()

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
.feed-item h3 {
  font-weight: 600;
}
.feed-item h3 a {
  color: var(--color-text);
}
.feed-item h3 a:hover {
  color: var(--color-primary);
}
.files {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 10px;
}
.files a {
  font-size: 13px;
}
</style>
