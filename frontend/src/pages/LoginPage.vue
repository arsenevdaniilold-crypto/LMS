<template>
  <div class="auth-page">
    <div class="auth-card">
      <h1>Вход</h1>

      <div v-if="formError" class="form-error">{{ formError }}</div>

      <form @submit.prevent="onSubmit" novalidate>
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
            autocomplete="current-password"
            :disabled="loading"
            :class="{ 'has-error': fieldErrors.password }"
            required
          />
          <span v-if="fieldErrors.password" class="error-text">{{ fieldErrors.password }}</span>
        </div>

        <button type="submit" class="btn-primary submit-btn" :disabled="loading">
          {{ loading ? 'Входим…' : 'Войти' }}
        </button>
      </form>

      <p class="auth-footer">
        Нет аккаунта? <RouterLink to="/register">Зарегистрироваться</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { AxiosError } from 'axios'
import { useAuthStore } from '@/shared/stores/authStore'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const email = ref('')
const password = ref('')
const loading = ref(false)
const formError = ref<string | null>(null)
const fieldErrors = reactive<{ email?: string; password?: string }>({})

function validate(): boolean {
  fieldErrors.email = undefined
  fieldErrors.password = undefined
  let ok = true
  if (!email.value.trim()) {
    fieldErrors.email = 'Введите email'
    ok = false
  }
  if (!password.value) {
    fieldErrors.password = 'Введите пароль'
    ok = false
  }
  return ok
}

async function onSubmit() {
  formError.value = null
  if (!validate()) return

  loading.value = true
  try {
    await auth.login({ email: email.value.trim(), password: password.value })
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    await router.push(redirect)
  } catch (err) {
    const ax = err as AxiosError<{ detail?: { code?: string; message?: string } | string }>
    const detail = ax.response?.data?.detail
    if (ax.response?.status === 401) {
      formError.value = 'Неверный email или пароль'
    } else if (ax.response?.status === 429) {
      formError.value = 'Слишком много попыток. Попробуйте через минуту.'
    } else if (typeof detail === 'object' && detail?.message) {
      formError.value = detail.message
    } else {
      formError.value = 'Не удалось войти. Попробуйте позже.'
    }
  } finally {
    loading.value = false
  }
}
</script>
