import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import http from '@/shared/api/http'
import { connect as wsConnect, disconnect as wsDisconnect } from '@/shared/ws/client'
import { useNotificationStore } from '@/shared/stores/notificationStore'

const AUTH_EVENT_KEY = 'lms-auth-event'

function broadcastAuthEvent(type: 'login' | 'logout'): void {
  try {
    localStorage.setItem(AUTH_EVENT_KEY, JSON.stringify({ type, at: Date.now() }))
  } catch {
    // ignore storage errors (private mode, etc.)
  }
}

interface User {
  id: string
  email: string
  username: string
  avatar_url: string | null
  is_admin: boolean
}

interface LoginPayload {
  email: string
  password: string
}

interface RegisterPayload {
  email: string
  username: string
  password: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isReady = ref(false)

  const isLoggedIn = computed(() => user.value !== null)

  async function fetchMe(): Promise<User | null> {
    try {
      const { data } = await http.get<User>('/users/me')
      user.value = data
      return data
    } catch {
      user.value = null
      return null
    }
  }

  async function startSession(): Promise<void> {
    const notif = useNotificationStore()
    await notif.fetch()
    wsConnect()
  }

  function endSession(): void {
    wsDisconnect()
    useNotificationStore().reset()
  }

  async function login(payload: LoginPayload): Promise<void> {
    await http.post('/auth/login', payload)
    await fetchMe()
    if (user.value) await startSession()
    broadcastAuthEvent('login')
  }

  async function register(payload: RegisterPayload): Promise<void> {
    await http.post('/auth/register', payload)
    await fetchMe()
    if (user.value) await startSession()
    broadcastAuthEvent('login')
  }

  async function logout(): Promise<void> {
    try {
      await http.post('/auth/logout')
    } finally {
      user.value = null
      endSession()
      broadcastAuthEvent('logout')
    }
  }

  async function syncFromOtherTab(): Promise<void> {
    endSession()
    const me = await fetchMe()
    if (me) await startSession()
  }

  async function init(): Promise<void> {
    await fetchMe()
    if (user.value) await startSession()
    isReady.value = true

    window.addEventListener('storage', (e) => {
      if (e.key === AUTH_EVENT_KEY && e.newValue !== null) {
        void syncFromOtherTab()
      }
    })
  }

  return {
    user,
    isReady,
    isLoggedIn,
    fetchMe,
    login,
    register,
    logout,
    init,
  }
})