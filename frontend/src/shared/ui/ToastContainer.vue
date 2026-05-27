<template>
  <Teleport to="body">
    <div class="toast-stack" aria-live="polite" aria-atomic="true">
      <TransitionGroup name="toast">
        <div
          v-for="t in toast.items"
          :key="t.id"
          class="toast"
          :class="`toast-${t.kind}`"
          role="status"
          @click="toast.dismiss(t.id)"
        >
          <span class="toast-icon" aria-hidden="true">
            <template v-if="t.kind === 'success'">✓</template>
            <template v-else-if="t.kind === 'error'">!</template>
            <template v-else>i</template>
          </span>
          <span class="toast-msg">{{ t.message }}</span>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { useToast } from '@/shared/stores/toastStore'
const toast = useToast()
</script>

<style scoped>
.toast-stack {
  position: fixed;
  right: 24px;
  bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 9999;
  pointer-events: none;
}
.toast {
  pointer-events: auto;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  min-width: 240px;
  max-width: 380px;
  padding: 12px 16px 12px 14px;
  border-radius: 14px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  box-shadow: 0 12px 30px -8px rgba(20, 14, 8, 0.22);
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text);
  cursor: pointer;
}
.toast-icon {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 800;
  font-size: 14px;
  flex-shrink: 0;
}
.toast-success .toast-icon { background: var(--color-success); }
.toast-error   .toast-icon { background: var(--color-danger); }
.toast-info    .toast-icon { background: var(--color-primary); }

.toast-success { border-color: var(--color-success-soft); }
.toast-error   { border-color: #f4c8c0; }
.toast-info    { border-color: var(--color-primary-soft); }

.toast-msg { line-height: 1.35; }

/* Enter/leave animation */
.toast-enter-active,
.toast-leave-active { transition: transform 0.25s var(--ease-spring), opacity 0.2s var(--ease-out); }
.toast-enter-from { opacity: 0; transform: translateX(40px); }
.toast-leave-to   { opacity: 0; transform: translateX(40px); }
.toast-move { transition: transform 0.25s var(--ease-out); }

@media (max-width: 600px) {
  .toast-stack { right: 12px; bottom: 12px; left: 12px; }
  .toast { min-width: 0; max-width: 100%; }
}
</style>
