<template>
  <PageDecor v-if="showHeader" />
  <AppHeader v-if="showHeader" />
  <RouterView v-slot="{ Component, route }">
    <Transition name="route" mode="out-in">
      <component :is="Component" :key="route.fullPath" />
    </Transition>
  </RouterView>
  <ToastContainer />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/shared/stores/authStore'
import AppHeader from '@/shared/ui/AppHeader.vue'
import ToastContainer from '@/shared/ui/ToastContainer.vue'
import PageDecor from '@/shared/ui/PageDecor.vue'

const route = useRoute()
const auth = useAuthStore()

const showHeader = computed(() => {
  return auth.isLoggedIn && !route.meta.guest
})
</script>
