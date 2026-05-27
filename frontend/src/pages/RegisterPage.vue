<template>
  <div class="auth-page">
    <AuthDecor />
    <button
      class="auth-theme-btn"
      :title="theme.mode.value === 'dark' ? 'Светлая тема' : 'Тёмная тема'"
      @click="theme.toggle()"
    >
      <svg v-if="theme.mode.value === 'dark'" width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <circle cx="12" cy="12" r="4.5" stroke="currentColor" stroke-width="2"/>
        <path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.93 4.93l2.12 2.12M16.95 16.95l2.12 2.12M4.93 19.07l2.12-2.12M16.95 7.05l2.12-2.12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
      <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
      </svg>
    </button>
    <div class="hero-wrap">
      <div class="grid-2">
        <!-- Left: editorial copy -->
        <div class="hero-copy">
          <h1 class="hero-title">
            начните<br />свой путь<br /><em>сегодня</em>
          </h1>
          <p class="hero-text">
            создайте аккаунт, чтобы вести <mark>классы</mark>, публиковать
            <mark>задания</mark> и отслеживать прогресс — всё в одном месте
          </p>
          <div class="hero-meta">
            <span>Бесплатно</span>
            <span class="sep">·</span>
            <span>Без карты</span>
            <span class="sep">·</span>
            <span>2 минуты</span>
          </div>
        </div>

        <!-- Right: animated hero-art with doodles + floating mini-cards + auth card -->
        <div class="hero-art">
          <!-- Background blobs (warm yellow) -->
          <div class="hero-blob a"></div>
          <div class="hero-blob b"></div>
          <div class="hero-sweep"></div>

          <!-- Decorative doodles (SVG) -->
          <svg class="doodle wave-1" viewBox="0 0 200 60" fill="none" aria-hidden="true">
            <path d="M2 30 Q 20 5, 40 30 T 80 30 T 120 30 T 160 30 T 200 30"
                  stroke="#2c6b52" stroke-width="3" stroke-linecap="round" fill="none"/>
          </svg>
          <svg class="doodle wave-2" viewBox="0 0 160 40" fill="none" aria-hidden="true">
            <path d="M2 20 Q 16 4, 30 20 T 60 20 T 90 20 T 120 20 T 160 20"
                  stroke="#171511" stroke-width="2.5" stroke-linecap="round" fill="none"/>
          </svg>

          <svg class="doodle star star-1" viewBox="0 0 30 30" fill="none" aria-hidden="true">
            <path d="M15 1 L18 11 L29 13 L20 20 L23 30 L15 24 L7 30 L10 20 L1 13 L12 11 Z"
                  fill="#ffe35c" stroke="#171511" stroke-width="1.5" stroke-linejoin="round"/>
          </svg>
          <svg class="doodle star star-2" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M12 1 L14 9 L23 10 L16 16 L18 24 L12 19 L6 24 L8 16 L1 10 L10 9 Z"
                  fill="#2c6b52"/>
          </svg>
          <svg class="doodle sparkle sparkle-1" viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path d="M10 0 L11 9 L20 10 L11 11 L10 20 L9 11 L0 10 L9 9 Z" fill="#ffe35c"/>
          </svg>
          <svg class="doodle sparkle sparkle-2" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <path d="M7 0 L8 6 L14 7 L8 8 L7 14 L6 8 L0 7 L6 6 Z" fill="#2c6b52"/>
          </svg>

          <svg class="doodle dots" viewBox="0 0 60 60" fill="none" aria-hidden="true">
            <circle cx="6" cy="6" r="3" fill="#171511"/>
            <circle cx="20" cy="6" r="3" fill="#171511"/>
            <circle cx="34" cy="6" r="3" fill="#171511"/>
            <circle cx="6" cy="20" r="3" fill="#171511"/>
            <circle cx="20" cy="20" r="3" fill="#171511"/>
            <circle cx="34" cy="20" r="3" fill="#171511"/>
            <circle cx="6" cy="34" r="3" fill="#171511"/>
            <circle cx="20" cy="34" r="3" fill="#171511"/>
            <circle cx="34" cy="34" r="3" fill="#171511"/>
          </svg>

          <svg class="doodle arrow" viewBox="0 0 80 60" fill="none" aria-hidden="true">
            <path d="M5 30 Q 30 5, 70 25 M 60 18 L 70 25 L 62 32"
                  stroke="#2c6b52" stroke-width="2.5" stroke-linecap="round"
                  stroke-linejoin="round" fill="none"/>
          </svg>

          <!-- Floating LMS feature cards (real product entities) -->
          <div class="float-card fc-announce" aria-hidden="true">
            <div class="fc-icon">📣</div>
            <div class="fc-body">
              <div class="fc-title">Объявление</div>
              <div class="fc-sub">Защита в пятницу</div>
            </div>
          </div>

          <div class="float-card fc-grade" aria-hidden="true">
            <div class="fc-grade-num">92</div>
            <div class="fc-body">
              <div class="fc-title">Новая оценка</div>
              <div class="fc-sub">FastAPI · 100</div>
            </div>
          </div>

          <div class="float-card fc-group" aria-hidden="true">
            <div class="fc-avatars">
              <span class="fc-av" style="background:#2c6b52">К</span>
              <span class="fc-av" style="background:#895800">М</span>
              <span class="fc-av" style="background:#31318a">А</span>
              <span class="fc-av fc-av-plus">+1</span>
            </div>
            <div class="fc-body">
              <div class="fc-title">Команда Alpha</div>
              <div class="fc-sub">4 участника</div>
            </div>
          </div>

          <!-- Auth card -->
          <div class="auth-card">
            <div class="auth-title">Создать аккаунт</div>
            <div class="auth-sub">
              уже есть аккаунт?
              <RouterLink to="/login">войти</RouterLink>
            </div>

            <div v-if="formError" class="form-error">{{ formError }}</div>

            <form @submit.prevent="onSubmit" novalidate>
              <div class="form-group">
                <label for="username">Имя пользователя</label>
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

              <div class="form-group">
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

              <div class="form-group">
                <label for="password">Пароль</label>
                <input
                  id="password"
                  v-model="password"
                  type="password"
                  autocomplete="new-password"
                  placeholder="минимум 8 символов"
                  :disabled="loading"
                  :class="{ 'has-error': fieldErrors.password }"
                  required
                />
                <span v-if="fieldErrors.password" class="error-text">{{ fieldErrors.password }}</span>
              </div>

              <button type="submit" class="btn-primary btn-wide" :disabled="loading">
                {{ loading ? 'Создаём…' : 'Зарегистрироваться' }}
              </button>
            </form>

            <p class="notice">
              уже есть аккаунт? <RouterLink to="/login">войти</RouterLink>
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { AxiosError } from 'axios'
import { useAuthStore } from '@/shared/stores/authStore'
import { useTheme } from '@/shared/stores/themeStore'
import AuthDecor from '@/shared/ui/AuthDecor.vue'

const theme = useTheme()

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
.auth-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--color-bg);
  position: relative;
}
.auth-theme-btn {
  position: absolute;
  top: 20px;
  right: 22px;
  z-index: 10;
  width: 40px;
  height: 40px;
  padding: 0;
  border-radius: 50%;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  color: var(--color-text);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background var(--dur-fast) var(--ease-out), transform var(--dur-fast) var(--ease-out);
}
.auth-theme-btn:hover { background: var(--color-bg-2); transform: translateY(-1px); }

/* ---------- Hero wrap ---------- */
.hero-wrap {
  position: relative;
  z-index: 2;
  flex: 1;
  max-width: 1320px;
  width: 100%;
  margin: 0 auto;
  padding: 40px 30px;
  display: flex;
  align-items: stretch;
}
.grid-2 {
  display: grid;
  grid-template-columns: 1.08fr 0.92fr;
  gap: 34px;
  align-items: center;
  width: 100%;
}

/* ---------- Left copy ---------- */
.hero-copy { padding-left: 8px; }
.hero-title {
  font-family: var(--font-display);
  font-size: clamp(48px, 7vw, 76px);
  line-height: 0.96;
  letter-spacing: -0.05em;
  font-weight: 800;
  margin-bottom: 22px;
}
.hero-title em {
  font-style: italic;
  font-weight: 600;
  color: var(--color-primary);
}
.hero-text {
  font-size: clamp(20px, 2.2vw, 27px);
  line-height: 1.42;
  font-weight: 700;
  max-width: 620px;
  color: var(--color-text);
}
.hero-text mark {
  background: var(--color-primary-soft);
  padding: 0 8px;
  border-radius: 8px;
  color: var(--color-text);
}
.hero-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 28px;
  font-size: 13px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}
.hero-meta .sep { opacity: 0.5; }

/* ---------- Right hero-art ---------- */
.hero-art {
  position: relative;
  min-height: 640px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background:
    radial-gradient(circle at 20% 20%, rgba(255, 227, 92, 0.28), transparent 34%),
    radial-gradient(circle at 80% 30%, rgba(44, 107, 82, 0.09), transparent 30%),
    linear-gradient(135deg, rgba(44, 107, 82, 0.06), rgba(255, 227, 92, 0.05));
  border-radius: 28px;
}
.hero-blob {
  position: absolute;
  border-radius: 50%;
  background: var(--color-accent);
  pointer-events: none;
}
.hero-blob.a {
  width: 520px;
  height: 520px;
  top: -120px;
  right: -80px;
  filter: saturate(1.05);
  opacity: 0.85;
}
.hero-blob.b {
  width: 340px;
  height: 340px;
  bottom: -120px;
  left: -90px;
  opacity: 0.55;
}
.hero-sweep {
  position: absolute;
  width: 360px;
  height: 640px;
  background: linear-gradient(180deg, rgba(var(--bg-rgb, 246, 241, 233), 0.85), rgba(var(--bg-rgb, 246, 241, 233), 0.3));
  border-radius: 48%;
  right: -180px;
  bottom: -120px;
  pointer-events: none;
}

/* ---------- Doodles (webium-style) ---------- */
.doodle {
  position: absolute;
  pointer-events: none;
  z-index: 2;
}
.wave-1 { top: 38px; left: 30px; width: 130px; height: 40px; transform: rotate(-6deg); }
.wave-2 { bottom: 56px; right: 36px; width: 110px; height: 28px; transform: rotate(8deg); }
.star-1 { top: 24px; right: 90px; width: 36px; height: 36px; animation: float-spin 9s linear infinite; }
.star-2 { bottom: 110px; left: 60px; width: 28px; height: 28px; animation: float-spin 14s linear infinite reverse; }
.sparkle-1 { top: 140px; left: 30px; width: 22px; height: 22px; animation: pulse 3s ease-in-out infinite; }
.sparkle-2 { bottom: 30px; right: 110px; width: 16px; height: 16px; animation: pulse 2.4s ease-in-out infinite 0.6s; }
.dots { top: 200px; right: 28px; width: 50px; height: 50px; opacity: 0.5; }
.arrow { bottom: 200px; left: 12px; width: 80px; height: 60px; opacity: 0.55; transform: rotate(-12deg); }

@keyframes float-spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.9; }
  50% { transform: scale(1.25); opacity: 1; }
}
@keyframes float-y {
  0%, 100% { transform: translateY(0) rotate(var(--rot, 0deg)); }
  50% { transform: translateY(-8px) rotate(var(--rot, 0deg)); }
}

/* ---------- Floating LMS feature cards ---------- */
.float-card {
  position: absolute;
  z-index: 4;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 10px 14px;
  box-shadow: 0 12px 30px -8px rgba(20, 14, 8, 0.18);
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  animation: float-y 5s ease-in-out infinite;
}
.fc-announce {
  top: 60px;
  left: -20px;
  --rot: -4deg;
  animation-delay: 0s;
}
.fc-grade {
  top: 230px;
  right: -10px;
  --rot: 5deg;
  animation-delay: 1.2s;
}
.fc-group {
  bottom: 70px;
  left: 20px;
  --rot: 3deg;
  animation-delay: 2.4s;
}

.fc-icon {
  width: 34px;
  height: 34px;
  background: var(--color-accent-soft);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}
.fc-grade-num {
  width: 34px;
  height: 34px;
  background: var(--color-primary);
  color: #fff;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 800;
}
.fc-body { line-height: 1.2; }
.fc-title {
  font-weight: 800;
  font-size: 13px;
  color: var(--color-text);
}
.fc-sub {
  font-size: 11px;
  color: var(--color-text-muted);
  margin-top: 2px;
}
.fc-avatars {
  display: flex;
  align-items: center;
}
.fc-av {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  color: #fff;
  font-size: 11px;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: -6px;
  border: 2px solid var(--color-surface);
}
.fc-av:first-child { margin-left: 0; }
.fc-av-plus {
  background: var(--color-bg-2);
  color: var(--color-text);
}

/* ---------- Auth card ---------- */
.auth-card {
  position: relative;
  z-index: 5;
  width: 430px;
  max-width: 100%;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 30px;
  box-shadow: var(--shadow-lg);
  padding: 34px;
}
.auth-title {
  font-family: var(--font-display);
  font-size: 30px;
  font-weight: 800;
  letter-spacing: -0.025em;
  margin-bottom: 6px;
}
.auth-sub {
  font-size: 15px;
  color: var(--color-text-muted);
  margin-bottom: 24px;
}
.auth-sub a {
  color: var(--color-text);
  font-weight: 800;
  text-decoration: underline;
}
.notice {
  font-size: 13px;
  color: var(--color-text-muted);
  text-align: center;
  margin-top: 14px;
}
.notice a { color: var(--color-text); font-weight: 800; text-decoration: underline; }

/* ---------- Responsive ---------- */
@media (max-width: 1100px) {
  .grid-2 { grid-template-columns: 1fr; gap: 20px; }
  .hero-art { min-height: 600px; margin-bottom: 30px; }
  .hero-wrap { padding: 24px 24px; }
}
@media (max-width: 760px) {
  .hero-wrap { padding: 18px 16px 30px; }
  .hero-title { font-size: 46px; letter-spacing: -0.04em; }
  .hero-text { font-size: 18px; }
  .auth-card { width: 100%; padding: 26px; }
  /* Hide cluttering elements on small screens */
  .fc-announce, .fc-grade, .fc-group { display: none; }
  .arrow, .dots { display: none; }
}
</style>
