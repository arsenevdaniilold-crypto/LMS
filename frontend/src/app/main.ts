import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from '@/shared/stores/authStore'
import '@/shared/stores/themeStore'  // side-effect: applies saved theme before paint
import '../shared/styles/global.css'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)

const auth = useAuthStore()
auth.init().finally(() => {
  app.use(router)
  app.mount('#app')
})
