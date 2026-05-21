<template>
  <header class="app-header">
    <div class="container header-inner">
      <RouterLink to="/" class="brand">
        <span class="brand-dot"></span>LMS
      </RouterLink>
      <nav class="nav">
        <RouterLink to="/" class="nav-link">Главная</RouterLink>
        <RouterLink to="/classes" class="nav-link">Каталог</RouterLink>
        <RouterLink v-if="auth.user?.is_admin" to="/admin" class="nav-link">Админка</RouterLink>
      </nav>
      <div class="header-right">
        <NotificationsBell />
        <RouterLink to="/profile" class="user-link">
          <span class="user-avatar">{{ (auth.user?.username || '?').charAt(0).toUpperCase() }}</span>
          <span class="username">{{ auth.user?.username }}</span>
        </RouterLink>
        <button class="btn-ghost logout-btn" :disabled="loggingOut" @click="onLogout">
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

const auth = useAuthStore()
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
.app-header {
  background: rgba(250, 248, 243, 0.82);
  backdrop-filter: saturate(180%) blur(14px);
  -webkit-backdrop-filter: saturate(180%) blur(14px);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 100;
}
.header-inner {
  display: flex;
  align-items: center;
  gap: 28px;
  padding-top: 14px;
  padding-bottom: 14px;
}
.brand {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 21px;
  letter-spacing: -0.01em;
  color: var(--color-text);
}
.brand:hover { text-decoration: none; }
.brand-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-soft);
}
.nav {
  display: flex;
  gap: 4px;
  flex: 1;
}
.nav-link {
  color: var(--color-text-muted);
  font-size: 14px;
  font-weight: 500;
  padding: 7px 13px;
  border-radius: var(--radius-pill);
  transition: background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out);
}
.nav-link:hover { background: var(--color-surface-sunken); color: var(--color-text); text-decoration: none; }
.nav-link.router-link-active {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}
.header-right {
  display: flex;
  gap: 10px;
  align-items: center;
}
.user-link {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  color: var(--color-text);
  padding: 4px 10px 4px 4px;
  border-radius: var(--radius-pill);
  transition: background var(--dur-fast) var(--ease-out);
}
.user-link:hover { background: var(--color-surface-sunken); text-decoration: none; }
.user-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fdfdfb;
  font-size: 13px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.username { font-size: 14px; font-weight: 500; }
.logout-btn { padding: 7px 12px; font-size: 13px; }

@media (max-width: 640px) {
  .header-inner { gap: 14px; }
  .nav { gap: 2px; }
  .nav-link { font-size: 13px; padding: 6px 10px; }
  .username { display: none; }
}

@media (max-width: 380px) {
  .header-inner { gap: 10px; padding-top: 11px; padding-bottom: 11px; }
  .brand { font-size: 18px; }
  .header-right { gap: 6px; }
  .logout-btn { padding: 6px 10px; }
}
</style>
