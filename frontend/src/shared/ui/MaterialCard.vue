<template>
  <div class="card material-card">
    <div class="feed-head">
      <div class="badges">
        <span class="badge badge-material">материал</span>
      </div>
      <span class="meta">{{ material.author.username }} · {{ formatDateTime(material.created_at) }}</span>
    </div>

    <!-- ===== View mode ===== -->
    <template v-if="!editing">
      <h3 class="feed-title">{{ material.title }}</h3>
      <p v-if="material.description" class="feed-text">{{ material.description }}</p>

      <div v-if="material.items.length > 0" class="chips">
        <a
          v-for="it in material.items"
          :key="it.id"
          :href="it.item_type === 'file' ? (it.download_url || '#') : (it.url || '#')"
          target="_blank"
          rel="noopener"
          class="file-chip"
        >
          {{ it.item_type === 'file' ? '📎' : '🔗' }}
          {{ it.item_type === 'file' ? it.file_name : it.url }}
        </a>
      </div>

      <div v-if="isTeacher || canDelete" class="feed-actions">
        <button v-if="isTeacher" class="btn-ghost feed-btn" @click="startEdit">Редактировать</button>
        <button class="btn-soft feed-btn" @click="onDelete">Удалить</button>
      </div>
    </template>

    <!-- ===== Edit mode ===== -->
    <form v-else class="edit-form" @submit.prevent="onSave">
      <div class="form-group">
        <label>Название</label>
        <input v-model="editTitle" maxlength="255" />
      </div>
      <div class="form-group" style="margin-bottom: 0">
        <label>Описание</label>
        <textarea v-model="editDescription" rows="3"></textarea>
      </div>
      <p class="muted" style="font-size: 13px; margin-top: 10px">
        Файлы и ссылки можно изменить, удалив материал и создав заново.
      </p>

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
import { ref } from 'vue'
import type { Material } from '@/shared/api/types'
import { deleteMaterial, updateMaterial } from '@/shared/api/materials'
import { extractError } from '@/shared/api/errors'
import { useToast } from '@/shared/stores/toastStore'
import { formatDateTime } from '@/shared/lib/dates'

const toast = useToast()

const props = withDefaults(
  defineProps<{ material: Material; isTeacher: boolean; canDelete?: boolean }>(),
  { canDelete: false },
)
const emit = defineEmits<{
  (e: 'deleted', id: string): void
  (e: 'updated', data: Material): void
}>()

const editing = ref(false)
const saving = ref(false)
const editError = ref('')
const editTitle = ref('')
const editDescription = ref('')

function startEdit() {
  editError.value = ''
  editTitle.value = props.material.title
  editDescription.value = props.material.description ?? ''
  editing.value = true
}

async function onSave() {
  editError.value = ''
  const title = editTitle.value.trim()
  if (title.length < 1) {
    editError.value = 'Введите название'
    return
  }
  saving.value = true
  try {
    const updated = await updateMaterial(props.material.id, {
      title,
      description: editDescription.value.trim(),
    })
    emit('updated', updated)
    editing.value = false
  } catch (e) {
    editError.value = extractError(e)
  } finally {
    saving.value = false
  }
}

async function onDelete() {
  if (!confirm('Удалить материал?')) return
  try {
    await deleteMaterial(props.material.id)
    emit('deleted', props.material.id)
  } catch (e) {
    toast.error(extractError(e))
  }
}
</script>

<style scoped>
.material-card {
  position: relative;
  transition: box-shadow var(--dur) var(--ease-out), transform var(--dur) var(--ease-out);
  overflow: hidden;
}
.material-card:hover { box-shadow: var(--shadow-lg); transform: translateY(-2px); }

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

.edit-form { margin-top: 14px; }
.file-chip { text-decoration: none; }
.file-chip:hover { background: var(--color-bg-3); text-decoration: none; }
</style>
