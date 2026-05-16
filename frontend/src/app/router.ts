import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/shared/stores/authStore'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('@/pages/LoginPage.vue'), meta: { guest: true } },
    { path: '/register', component: () => import('@/pages/RegisterPage.vue'), meta: { guest: true } },
    { path: '/', component: () => import('@/pages/HomePage.vue'), meta: { auth: true } },
    { path: '/classes', component: () => import('@/pages/ClassesPage.vue'), meta: { auth: true } },
    { path: '/classes/:id', component: () => import('@/pages/ClassDetailPage.vue'), meta: { auth: true } },
    { path: '/classes/:id/grades', component: () => import('@/pages/GradesPage.vue'), meta: { auth: true } },
    { path: '/assignments/:id', component: () => import('@/pages/AssignmentPage.vue'), meta: { auth: true } },
    { path: '/solutions/:id', component: () => import('@/pages/SolutionPage.vue'), meta: { auth: true } },
    { path: '/solutions/:id/redistribute', component: () => import('@/pages/RedistributePage.vue'), meta: { auth: true } },
    { path: '/profile', component: () => import('@/pages/ProfilePage.vue'), meta: { auth: true } },
    { path: '/admin', component: () => import('@/pages/AdminPage.vue'), meta: { auth: true, admin: true } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.auth && !auth.isLoggedIn) return '/login'
  if (to.meta.guest && auth.isLoggedIn) return '/'
  if (to.meta.admin && !auth.user?.is_admin) return '/'
})

export default router
