<template>
  <div class="login-split">
    <!-- Left: editorial brand panel -->
    <aside class="brand-panel">
      <div class="brand-noise" aria-hidden="true"></div>
      <div class="brand-inner">
        <div class="brand-mark reveal" style="animation-delay: 40ms">
          <span class="brand-dot"></span> LMS
        </div>
        <h1 class="brand-headline reveal" style="animation-delay: 120ms">
          Начните<br />свой путь<br /><em>сегодня.</em>
        </h1>
        <p class="brand-sub reveal" style="animation-delay: 220ms">
          Создайте аккаунт, чтобы вести классы, публиковать задания
          и отслеживать прогресс — всё в одном месте.
        </p>
        <div class="brand-meta reveal" style="animation-delay: 320ms">
          <span class="brand-meta-item">Бесплатно</span>
          <span class="brand-meta-sep">·</span>
          <span class="brand-meta-item">Без карты</span>
          <span class="brand-meta-sep">·</span>
          <span class="brand-meta-item">2 минуты</span>
        </div>
      </div>
    </aside>

    <!-- Right: form -->
    <main class="form-panel">
      <div class="form-shell">
        <header class="form-head reveal" style="animation-delay: 80ms">
          <p class="form-eyebrow">Регистрация</p>
          <h2 class="form-title">Создать аккаунт</h2>
        </header>

        <div v-if="formError" class="form-error reveal">{{ formError }}</div>

        <form @submit.prevent="onSubmit" novalidate>
          <div class="form-group reveal" style="animation-delay: 140ms">
            <label for="username">Имя</label>
            <input
              id="username"
              v-model="username"
              type="text"
              autocomplete="name"
              placeholder="Иван Петров"
              :disabled="loading"
              :class="{ 'has-error': fieldErrors.username }"
              required
            />
            <span v-if="fieldErrors.username" class="error-text">{{ fieldErrors.username }}</span>
          </div>

          <div class="form-group reveal" style="animation-delay: 200ms">
            <label for="email">Email</label>
            <input
              id="email"
              v-model="email"
              type="email"
              autocomplete="email"
              placeholder="you@example.com"
              :disabled="loading"
              :class="{ 'has-error': fieldErrors.email }"
              required
            />
            <span v-if="fieldErrors.email" class="error-text">{{ fieldErrors.email }}</span>
          </div>

          <div class="form-group reveal" style="animation-delay: 260ms">
            <label for="password">Пароль</label>
            <input
              id="password"
              v-model="password"
              type="password"
              autocomplete="new-password"
              placeholder="Минимум 8 символов"
              :disabled="loading"
              :class="{ 'has-error': fieldErrors.password }"
              required
            />
            <span v-if="fieldErrors.password" class="error-text">{{ fieldErrors.password }}</span>
          </div>

          <button type="submit" class="btn-primary submit-btn reveal" style="animation-delay: 320ms" :disabled="loading">
            <span>{{ loading ? 'Создаём…' : 'Зарегистрироваться' }}</span>
            <svg v-if="!loading" class="submit-arrow" width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </form>

        <p class="auth-footer reveal" style="animation-delay: 380ms">
          Уже есть аккаунт? <RouterLink to="/login">Войти</RouterLink>
        </p>
      </div>
    </main>
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

<style scoped>
.login-split {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1.05fr 1fr;
}

/* ---------- Left brand panel ---------- */
.brand-panel {
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(120% 90% at 0% 0%, #235e4b 0%, var(--color-primary) 45%, #133227 100%);
  color: #eef4f0;
  display: flex;
  align-items: center;
  padding: 64px clamp(40px, 6vw, 96px);
}
.brand-noise {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image: radial-gradient(rgba(255, 255, 255, 0.06) 1px, transparent 1.4px);
  background-size: 22px 22px;
  -webkit-mask-image: radial-gradient(120% 100% at 0% 0%, #000 30%, transparent 78%);
  mask-image: radial-gradient(120% 100% at 0% 0%, #000 30%, transparent 78%);
  opacity: 0.7;
}
.brand-inner { position: relative; max-width: 460px; }
.brand-mark {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-family: var(--font-body);
  font-weight: 700;
  font-size: 15px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #cfe2d9;
  margin-bottom: 56px;
}
.brand-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #8fd6b4;
  box-shadow: 0 0 16px 2px rgba(143, 214, 180, 0.7);
}
.brand-headline {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: clamp(40px, 5.5vw, 68px);
  line-height: 1.04;
  letter-spacing: -0.025em;
  margin-bottom: 28px;
}
.brand-headline em { font-style: italic; font-weight: 500; color: #9be0bd; }
.brand-sub {
  font-size: 16.5px;
  line-height: 1.65;
  color: #bcd2c8;
  max-width: 40ch;
  margin-bottom: 44px;
}
.brand-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #87a99a;
}
.brand-meta-sep { opacity: 0.5; }

/* ---------- Right form panel ---------- */
.form-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  background: var(--color-bg);
}
.form-shell { width: 100%; max-width: 380px; }
.form-head { margin-bottom: 28px; }
.form-eyebrow {
  font-size: 12.5px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-primary);
  margin-bottom: 8px;
}
.form-title {
  font-family: var(--font-display);
  font-size: 34px;
  font-weight: 600;
  letter-spacing: -0.02em;
}
.submit-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
}
.submit-arrow { transition: transform var(--dur) var(--ease-spring); }
.submit-btn:hover:not(:disabled) .submit-arrow { transform: translateX(4px); }

@media (max-width: 880px) {
  .login-split { grid-template-columns: 1fr; }
  .brand-panel { padding: 48px 32px 40px; min-height: auto; }
  .brand-mark { margin-bottom: 32px; }
  .brand-headline { font-size: clamp(34px, 9vw, 48px); margin-bottom: 18px; }
  .brand-sub { margin-bottom: 8px; font-size: 15px; }
  .brand-meta { display: none; }
  .form-panel { padding: 40px 24px 56px; }
}
@media (max-width: 380px) {
  .brand-panel { padding: 36px 22px 30px; }
  .form-title { font-size: 28px; }
}
</style>
