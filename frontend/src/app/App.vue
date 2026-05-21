<template>
  <AppHeader v-if="showHeader" />
  <RouterView />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/shared/stores/authStore'
import AppHeader from '@/shared/ui/AppHeader.vue'

const route = useRoute()
const auth = useAuthStore()

const showHeader = computed(() => {
  return auth.isLoggedIn && !route.meta.guest
})
</script>
