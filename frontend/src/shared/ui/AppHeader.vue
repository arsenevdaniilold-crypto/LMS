<template>
  <header class="topbar">
    <div class="topbar-inner">
      <nav class="top-links">
        <RouterLink to="/" class="top-link">Главная</RouterLink>
        <RouterLink to="/classes" class="top-link">Каталог</RouterLink>
        <RouterLink v-if="auth.user?.is_admin" to="/admin" class="top-link admin-chip">Админка</RouterLink>
      </nav>

      <div class="top-right">
        <button
          class="theme-btn"
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
        <NotificationsBell />
        <RouterLink to="/profile" class="user-link">
          <span class="avatar">
            <img
              v-if="auth.user?.avatar_url"
              :src="auth.user.avatar_url"
              :alt="auth.user.username"
            />
            <template v-else>{{ (auth.user?.username || '?').charAt(0).toUpperCase() }}</template>
          </span>
          <span class="user-name">{{ auth.user?.username }}</span>
        </RouterLink>
        <button class="logout" :disabled="loggingOut" @click="onLogout">
          {{ loggingOut ? '…' : 'Выйти' }}
        </button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/shared/stores/authStore'
import NotificationsBell from './NotificationsBell.vue'
import { useTheme } from '@/shared/stores/themeStore'

const auth = useAuthStore()
const theme = useTheme()
const router = useRouter()
const loggingOut = ref(false)

async function onLogout() {
  loggingOut.value = true
  try {
    await auth.logout()
    await router.push('/login')
  } finally {
    loggingOut.value = false
  }
}
</script>

<style scoped>
.topbar {
  height: 74px;
  background: rgba(var(--bg-rgb), 0.92);
  backdrop-filter: saturate(180%) blur(8px);
  -webkit-backdrop-filter: saturate(180%) blur(8px);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 100;
}
.topbar-inner {
  height: 100%;
  max-width: 1320px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 28px;
  padding: 0 34px;
}

/* ---------- Top nav links ---------- */
.top-links {
  display: flex;
  gap: 22px;
}
.top-link {
  position: relative;
  font-size: 15px;
  font-weight: 700;
  color: var(--color-text);
  text-decoration: none;
  padding: 8px 0;
}
.top-link::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 2px;
  background: var(--color-primary);
  transform: scaleX(0);
  transform-origin: left center;
  transition: transform var(--dur) var(--ease-out);
}
.top-link:hover { text-decoration: none; }
.top-link:hover::after,
.top-link.router-link-active::after { transform: scaleX(1); }
.top-link.admin-chip {
  background: var(--color-accent);
  color: var(--accent-ink);
  padding: 8px 14px;
  border-radius: var(--radius-pill);
  border-bottom: none;
}
.top-link.admin-chip::after { display: none; }
.top-link.admin-chip:hover { background: var(--color-accent-hover); color: var(--accent-ink); border-bottom: none; }

/* ---------- Right cluster ---------- */
.top-right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 14px;
}

.user-link {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--color-text);
  text-decoration: none;
  padding: 4px 12px 4px 4px;
  border-radius: var(--radius-pill);
  transition: background var(--dur-fast) var(--ease-out);
}
.user-link:hover { background: var(--color-bg-2); text-decoration: none; }

.avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  overflow: hidden;
  flex-shrink: 0;
}
.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.user-name {
  font-size: 14.5px;
  font-weight: 800;
}

.logout {
  background: transparent;
  border: none;
  padding: 4px 6px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-decoration: underline;
  text-underline-offset: 3px;
  cursor: pointer;
}
.logout:hover { color: var(--color-text); }

.theme-btn {
  width: 38px;
  height: 38px;
  padding: 0;
  border-radius: 50%;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  color: var(--color-text);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background var(--dur-fast) var(--ease-out), transform var(--dur-fast) var(--ease-out);
}
.theme-btn:hover { background: var(--color-bg-2); transform: translateY(-1px); }
.theme-btn svg { display: block; }

@media (max-width: 900px) {
  .topbar { height: 68px; }
  .topbar-inner { padding: 0 18px; gap: 16px; }
  .top-links { gap: 14px; }
  .user-name { display: none; }
}
</style>
