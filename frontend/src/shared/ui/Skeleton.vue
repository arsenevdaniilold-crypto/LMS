<template>
  <span class="sk" :style="style" aria-hidden="true" />
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    width?: string | number
    height?: string | number
    circle?: boolean
    radius?: string
  }>(),
  { width: '100%', height: 14, circle: false, radius: '8px' },
)

function unit(v: string | number): string {
  return typeof v === 'number' ? `${v}px` : v
}

const style = computed(() => ({
  width: unit(props.width),
  height: unit(props.height),
  borderRadius: props.circle ? '50%' : props.radius,
}))
</script>

<style scoped>
.sk {
  display: inline-block;
  background: linear-gradient(
    90deg,
    var(--color-bg-2) 0%,
    var(--color-bg-3) 50%,
    var(--color-bg-2) 100%
  );
  background-size: 200% 100%;
  animation: sk-shimmer 1.4s ease-in-out infinite;
  vertical-align: middle;
}

@keyframes sk-shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
