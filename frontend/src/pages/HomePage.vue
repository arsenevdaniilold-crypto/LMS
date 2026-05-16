<template>
  <div class="container" style="padding-top: 40px">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px">
      <h1>Главная</h1>
      <div style="display: flex; gap: 12px; align-items: center">
        <span v-if="auth.user" style="color: var(--color-text-muted)">
          {{ auth.user.username }}
        </span>
        <button class="btn-secondary" :disabled="loggingOut" @click="onLogout">
          {{ loggingOut ? 'Выходим…' : 'Выйти' }}
        </button>
      </div>
    </div>

    <div class="card">
      <p style="color: var(--color-text-muted)">
        Добро пожаловать{{ auth.user ? `, ${auth.user.username}` : '' }}!
        Остальные разделы появятся на следующих этапах.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/shared/stores/authStore'

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
