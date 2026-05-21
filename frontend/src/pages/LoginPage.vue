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
          Учитесь.<br />Преподавайте.<br /><em>Растите.</em>
        </h1>
        <p class="brand-sub reveal" style="animation-delay: 220ms">
          Единое пространство для классов, заданий и оценок —
          с уведомлениями в реальном времени.
        </p>
        <div class="brand-meta reveal" style="animation-delay: 320ms">
          <span class="brand-meta-item">Классы</span>
          <span class="brand-meta-sep">·</span>
          <span class="brand-meta-item">Задания</span>
          <span class="brand-meta-sep">·</span>
          <span class="brand-meta-item">Оценки</span>
        </div>
      </div>
    </aside>

    <!-- Right: form -->
    <main class="form-panel">
      <div class="form-shell">
        <header class="form-head reveal" style="animation-delay: 80ms">
          <p class="form-eyebrow">Добро пожаловать</p>
          <h2 class="form-title">Вход в аккаунт</h2>
        </header>

        <div v-if="formError" class="form-error reveal">{{ formError }}</div>

        <form @submit.prevent="onSubmit" novalidate>
          <div class="form-group reveal" style="animation-delay: 160ms">
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

          <div class="form-group reveal" style="animation-delay: 220ms">
            <label for="password">Пароль</label>
            <input
              id="password"
              v-model="password"
              type="password"
              autocomplete="current-password"
              placeholder="••••••••"
              :disabled="loading"
              :class="{ 'has-error': fieldErrors.password }"
              required
            />
            <span v-if="fieldErrors.password" class="error-text">{{ fieldErrors.password }}</span>
          </div>

          <button type="submit" class="btn-primary submit-btn reveal" style="animation-delay: 280ms" :disabled="loading">
            <span>{{ loading ? 'Входим…' : 'Войти' }}</span>
            <svg v-if="!loading" class="submit-arrow" width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </form>

        <p class="auth-footer reveal" style="animation-delay: 340ms">
          Нет аккаунта? <RouterLink to="/register">Зарегистрироваться</RouterLink>
        </p>
      </div>
    </main>
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
/* fine grain + a faint dotted scholar grid for texture */
.brand-noise {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image:
    radial-gradient(rgba(255, 255, 255, 0.06) 1px, transparent 1.4px);
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
.brand-headline em {
  font-style: italic;
  font-weight: 500;
  color: #9be0bd;
}
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

/* ---------- Responsive: collapse to single column ---------- */
@media (max-width: 880px) {
  .login-split { grid-template-columns: 1fr; }
  .brand-panel {
    padding: 48px 32px 40px;
    min-height: auto;
  }
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
