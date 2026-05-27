<template>
  <div class="timeline">
    <div
      v-for="(step, i) in steps"
      :key="step.id"
      class="step"
      :class="{
        'is-done': step.state === 'done',
        'is-active': step.state === 'active',
        'is-failed': step.state === 'failed',
      }"
    >
      <div class="step-dot" aria-hidden="true">
        <template v-if="step.state === 'done'">✓</template>
        <template v-else-if="step.state === 'failed'">!</template>
        <template v-else-if="step.state === 'active'">●</template>
        <template v-else>{{ i + 1 }}</template>
      </div>
      <div class="step-body">
        <div class="step-label">{{ step.label }}</div>
        <div v-if="step.sub" class="step-sub muted">{{ step.sub }}</div>
      </div>
      <div v-if="i < steps.length - 1" class="step-connector" aria-hidden="true"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
export type StepState = 'upcoming' | 'active' | 'done' | 'failed' | 'skipped'

export interface TimelineStep {
  id: string
  label: string
  state: StepState
  sub?: string
}

defineProps<{ steps: TimelineStep[] }>()
</script>

<style scoped>
.timeline {
  display: flex;
  align-items: flex-start;
  gap: 0;
  padding: 8px 0 4px;
  flex-wrap: wrap;
}
.step {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1 1 0;
  min-width: 110px;
  text-align: center;
  padding: 0 6px;
}

.step-dot {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 15px;
  background: var(--color-bg-2);
  color: var(--color-text-subtle);
  border: 2px solid var(--color-border);
  z-index: 2;
  position: relative;
  transition: transform var(--dur) var(--ease-spring), background var(--dur) var(--ease-out);
}

.step-body { margin-top: 10px; }
.step-label {
  font-size: 13.5px;
  font-weight: 800;
  color: var(--color-text-muted);
  letter-spacing: -0.005em;
}
.step-sub {
  font-size: 11.5px;
  margin-top: 2px;
}

/* Connector line between steps */
.step-connector {
  position: absolute;
  top: 17px;
  left: 50%;
  right: -50%;
  height: 3px;
  background: var(--color-border);
  z-index: 1;
}

/* States */
.step.is-done .step-dot {
  background: var(--color-success);
  color: #fff;
  border-color: var(--color-success);
}
.step.is-done .step-label { color: var(--color-text); }
.step.is-done + .step .step-connector,
.step.is-done .step-connector { background: var(--color-success); }

.step.is-active .step-dot {
  background: var(--color-accent);
  color: var(--color-text);
  border-color: var(--color-text);
  transform: scale(1.08);
  box-shadow: 0 0 0 6px rgba(255, 227, 92, 0.35);
  animation: dot-pulse 1.8s ease-in-out infinite;
}
.step.is-active .step-label { color: var(--color-text); }

.step.is-failed .step-dot {
  background: var(--color-danger);
  color: #fff;
  border-color: var(--color-danger);
}
.step.is-failed .step-label { color: var(--color-danger); }

@keyframes dot-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(255, 227, 92, 0.55); }
  50%      { box-shadow: 0 0 0 8px rgba(255, 227, 92, 0); }
}

@media (max-width: 720px) {
  .timeline { flex-direction: column; gap: 14px; }
  .step { flex-direction: row; align-items: center; text-align: left; width: 100%; gap: 14px; }
  .step-body { margin-top: 0; }
  .step-connector {
    top: 36px;
    left: 17px;
    right: auto;
    bottom: -14px;
    width: 3px;
    height: auto;
  }
}
</style>
