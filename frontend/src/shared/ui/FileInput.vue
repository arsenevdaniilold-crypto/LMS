<template>
  <div>
    <label style="font-size: 13px; font-weight: 500; display: block; margin-bottom: 4px">
      Файлы
    </label>
    <input
      ref="inputRef"
      type="file"
      :multiple="multiple"
      :accept="accept"
      style="display: none"
      @change="onChange"
    />
    <div class="row">
      <button class="btn-secondary" @click="inputRef?.click()">
        Выбрать файл{{ multiple ? 'ы' : '' }}
      </button>
      <span v-if="modelValue.length === 0" class="muted" style="font-size: 13px">
        не выбран{{ multiple ? 'ы' : '' }}
      </span>
    </div>
    <div v-if="modelValue.length > 0" class="stack" style="margin-top: 8px; gap: 4px">
      <div v-for="(f, idx) in modelValue" :key="idx" class="row" style="gap: 8px">
        <span class="muted" style="font-size: 13px">{{ f.name }} ({{ formatSize(f.size) }})</span>
        <button class="btn-secondary" style="font-size: 12px; padding: 2px 6px" @click="remove(idx)">×</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = withDefaults(
  defineProps<{ modelValue: File[]; multiple?: boolean; accept?: string }>(),
  {
    multiple: false,
    accept: '.docx,.pptx,.jpg,.jpeg,.png,.xlsx',
  },
)
const emit = defineEmits<{ (e: 'update:modelValue', files: File[]): void }>()

const inputRef = ref<HTMLInputElement | null>(null)

function onChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files) return
  const newFiles = Array.from(input.files)
  emit('update:modelValue', props.multiple ? [...props.modelValue, ...newFiles] : newFiles)
  input.value = ''
}

function remove(idx: number) {
  const copy = [...props.modelValue]
  copy.splice(idx, 1)
  emit('update:modelValue', copy)
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
</script>
