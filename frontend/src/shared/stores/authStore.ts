import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import http from '@/shared/api/http'

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

  async function login(payload: LoginPayload): Promise<void> {
    await http.post('/auth/login', payload)
    await fetchMe()
  }

  async function register(payload: RegisterPayload): Promise<void> {
    await http.post('/auth/register', payload)
    await fetchMe()
  }

  async function logout(): Promise<void> {
    try {
      await http.post('/auth/logout')
    } finally {
      user.value = null
    }
  }

  async function init(): Promise<void> {
    await fetchMe()
    isReady.value = true
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