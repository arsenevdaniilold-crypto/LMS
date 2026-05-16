<template>
  <div class="auth-page">
    <div class="auth-card">
      <h1>Регистрация</h1>

      <div v-if="formError" class="form-error">{{ formError }}</div>

      <form @submit.prevent="onSubmit" novalidate>
        <div class="form-group">
          <label for="username">Имя</label>
          <input
            id="username"
            v-model="username"
            type="text"
            autocomplete="name"
            :disabled="loading"
            :class="{ 'has-error': fieldErrors.username }"
            required
          />
          <span v-if="fieldErrors.username" class="error-text">{{ fieldErrors.username }}</span>
        </div>

        <div class="form-group">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="email"
            type="email"
            autocomplete="email"
            :disabled="loading"
            :class="{ 'has-error': fieldErrors.email }"
            required
          />
          <span v-if="fieldErrors.email" class="error-text">{{ fieldErrors.email }}</span>
        </div>

        <div class="form-group">
          <label for="password">Пароль</label>
          <input
            id="password"
            v-model="password"
            type="password"
            autocomplete="new-password"
            :disabled="loading"
            :class="{ 'has-error': fieldErrors.password }"
            required
          />
          <span v-if="fieldErrors.password" class="error-text">{{ fieldErrors.password }}</span>
          <span v-else class="error-text" style="color: var(--color-text-muted)">
            Минимум 8 символов
          </span>
        </div>

        <button type="submit" class="btn-primary submit-btn" :disabled="loading">
          {{ loading ? 'Создаём…' : 'Зарегистрироваться' }}
        </button>
      </form>

      <p class="auth-footer">
        Уже есть аккаунт? <RouterLink to="/login">Войти</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { AxiosError } from 'axios'
import { useAuthStore } from '@/shared/stores/authStore'

const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const username = ref('')
const password = ref('')
const loading = ref(false)
const formError = ref<string | null>(null)
const fieldErrors = reactive<{ email?: string; username?: string; password?: string }>({})

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function validate(): boolean {
  fieldErrors.email = undefined
  fieldErrors.username = undefined
  fieldErrors.password = undefined
  let ok = true

  const trimmedUsername = username.value.trim()
  if (trimmedUsername.length < 2 || trimmedUsername.length > 100) {
    fieldErrors.username = 'Имя должно быть от 2 до 100 символов'
    ok = false
  }

  const trimmedEmail = email.value.trim()
  if (!EMAIL_RE.test(trimmedEmail)) {
    fieldErrors.email = 'Введите корректный email'
    ok = false
  }

  if (password.value.length < 8) {
    fieldErrors.password = 'Пароль должен быть не менее 8 символов'
    ok = false
  }

  return ok
}

async function onSubmit() {
  formError.value = null
  if (!validate()) return

  loading.value = true
  try {
    await auth.register({
      email: email.value.trim(),
      username: username.value.trim(),
      password: password.value,
    })
    await router.push('/')
  } catch (err) {
    const ax = err as AxiosError<{ detail?: { code?: string; message?: string } | string | Array<{ msg: string }> }>
    const status = ax.response?.status
    const detail = ax.response?.data?.detail

    if (status === 409) {
      fieldErrors.email = 'Email уже зарегистрирован'
    } else if (status === 422 && Array.isArray(detail)) {
      formError.value = detail[0]?.msg ?? 'Проверьте введённые данные'
    } else if (status === 429) {
      formError.value = 'Слишком много попыток. Попробуйте через минуту.'
    } else if (typeof detail === 'object' && !Array.isArray(detail) && detail?.message) {
      formError.value = detail.message
    } else {
      formError.value = 'Не удалось зарегистрироваться. Попробуйте позже.'
    }
  } finally {
    loading.value = false
  }
}
</script>
