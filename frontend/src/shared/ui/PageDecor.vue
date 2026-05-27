<template>
  <div class="page-decor" aria-hidden="true">
    <span class="blob blob-a"></span>
    <span class="blob blob-b"></span>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
.page-decor {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}
.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  pointer-events: none;
}
.blob-a {
  width: 460px;
  height: 460px;
  background: var(--color-accent);
  top: -180px;
  right: -120px;
  opacity: 0.32;
  animation: page-drift-a 28s ease-in-out infinite;
}
.blob-b {
  width: 380px;
  height: 380px;
  background: var(--color-primary);
  bottom: -160px;
  left: -120px;
  opacity: 0.22;
  animation: page-drift-b 34s ease-in-out infinite;
}

:root[data-theme="dark"] .blob-a { opacity: 0.18; }
:root[data-theme="dark"] .blob-b { opacity: 0.14; }

@keyframes page-drift-a {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50%      { transform: translate(-50px, 60px) scale(1.06); }
}
@keyframes page-drift-b {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50%      { transform: translate(60px, -40px) scale(1.08); }
}

@media (prefers-reduced-motion: reduce) {
  .blob { animation: none; }
}
@media (max-width: 760px) {
  .blob { filter: blur(80px); }
  .blob-a { width: 340px; height: 340px; }
  .blob-b { width: 280px; height: 280px; }
}
</style>
