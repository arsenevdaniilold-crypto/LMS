<template>
  <div class="container page">
    <h1 class="page-title">Профиль</h1>

    <div v-if="!auth.user" class="card muted">Загрузка…</div>
    <div v-else class="card" style="max-width: 600px">
      <div class="stack">
        <div class="form-group" style="margin-bottom: 0">
          <label>Email</label>
          <input :value="auth.user.email" disabled />
        </div>
        <div class="form-group" style="margin-bottom: 0">
          <label>Имя пользователя</label>
          <input v-model="username" :class="{ 'has-error': usernameError }" />
          <div v-if="usernameError" class="error-text">{{ usernameError }}</div>
        </div>
        <div class="form-group" style="margin-bottom: 0">
          <label>URL аватара (необязательно)</label>
          <input v-model="avatarUrl" placeholder="https://..." />
        </div>
        <div v-if="auth.user.is_admin">
          <span class="tag tag-info">Администратор</span>
        </div>
        <div v-if="error" class="error-text">{{ error }}</div>
        <div v-if="success" class="muted">{{ success }}</div>
        <div class="row">
          <button class="btn-primary" :disabled="saving" @click="onSave">
            {{ saving ? 'Сохраняем…' : 'Сохранить' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useAuthStore } from '@/shared/stores/authStore'
import { updateMe } from '@/shared/api/users'
import { extractError } from '@/shared/api/errors'

const auth = useAuthStore()
const username = ref('')
const avatarUrl = ref('')
const usernameError = ref('')
const error = ref('')
const success = ref('')
const saving = ref(false)

watch(
  () => auth.user,
  (u) => {
    if (u) {
      username.value = u.username
      avatarUrl.value = u.avatar_url || ''
    }
  },
  { immediate: true },
)

async function onSave() {
  error.value = ''
  success.value = ''
  usernameError.value = ''
  const name = username.value.trim()
  if (name.length < 2 || name.length > 100) {
    usernameError.value = 'От 2 до 100 символов'
    return
  }
  saving.value = true
  try {
    await updateMe({ username: name, avatar_url: avatarUrl.value.trim() || null })
    await auth.fetchMe()
    success.value = 'Сохранено'
  } catch (e) {
    error.value = extractError(e)
  } finally {
    saving.value = false
  }
}
</script>
