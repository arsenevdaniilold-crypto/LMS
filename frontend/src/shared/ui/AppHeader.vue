<template>
  <header class="app-header">
    <div class="container header-inner">
      <RouterLink to="/" class="brand">LMS</RouterLink>
      <nav class="nav">
        <RouterLink to="/" class="nav-link">Главная</RouterLink>
        <RouterLink to="/classes" class="nav-link">Каталог</RouterLink>
        <RouterLink v-if="auth.user?.is_admin" to="/admin" class="nav-link">Admin</RouterLink>
      </nav>
      <div class="header-right">
        <NotificationsBell />
        <RouterLink to="/profile" class="user-link">
          <span class="username">{{ auth.user?.username }}</span>
        </RouterLink>
        <button class="btn-secondary logout-btn" :disabled="loggingOut" @click="onLogout">
          {{ loggingOut ? '...' : 'Выйти' }}
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
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
  box-shadow: var(--shadow);
  position: sticky;
  top: 0;
  z-index: 100;
}
.header-inner {
  display: flex;
  align-items: center;
  gap: 24px;
  padding-top: 12px;
  padding-bottom: 12px;
}
.brand {
  font-weight: 700;
  font-size: 18px;
  color: var(--color-text);
}
.nav {
  display: flex;
  gap: 16px;
  flex: 1;
}
.nav-link {
  color: var(--color-text-muted);
  font-size: 14px;
  padding: 6px 0;
}
.nav-link.router-link-active {
  color: var(--color-primary);
  font-weight: 500;
}
.header-right {
  display: flex;
  gap: 12px;
  align-items: center;
}
.user-link {
  color: var(--color-text);
}
.username {
  font-size: 14px;
}
.logout-btn {
  padding: 6px 12px;
  font-size: 13px;
}

@media (max-width: 640px) {
  .nav {
    gap: 8px;
  }
  .nav-link {
    font-size: 13px;
  }
  .username {
    display: none;
  }
}

@media (max-width: 380px) {
  .header-inner {
    gap: 10px;
    padding-top: 10px;
    padding-bottom: 10px;
  }
  .brand {
    font-size: 16px;
  }
  .nav {
    gap: 10px;
  }
  .header-right {
    gap: 8px;
  }
  .logout-btn {
    padding: 6px 10px;
  }
}
</style>
