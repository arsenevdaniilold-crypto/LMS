import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface User {
  id: string
  email: string
  username: string
  avatar_url: string | null
  is_admin: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)

  const isLoggedIn = computed(() => user.value !== null)

  function setUser(u: User) {
    user.value = u
  }

  function clear() {
    user.value = null
  }

  return { user, isLoggedIn, setUser, clear }
})
