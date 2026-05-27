<template>
  <div class="decor" aria-hidden="true">
    <!-- Soft drifting color mesh (works in both themes) -->
    <span class="mesh mesh-1"></span>
    <span class="mesh mesh-2"></span>
    <span class="mesh mesh-3"></span>

    <!-- Floating confetti stars — scattered across whole page -->
    <svg class="confetti c1" viewBox="0 0 30 30" fill="none">
      <path d="M15 1 L18 11 L29 13 L20 20 L23 30 L15 24 L7 30 L10 20 L1 13 L12 11 Z"
            fill="var(--color-accent)" stroke="var(--color-text)" stroke-width="1.2" stroke-linejoin="round"/>
    </svg>
    <svg class="confetti c2" viewBox="0 0 24 24" fill="none">
      <path d="M12 1 L14 9 L23 10 L16 16 L18 24 L12 19 L6 24 L8 16 L1 10 L10 9 Z"
            fill="var(--color-primary)"/>
    </svg>
    <svg class="confetti c3" viewBox="0 0 20 20" fill="none">
      <path d="M10 0 L11 9 L20 10 L11 11 L10 20 L9 11 L0 10 L9 9 Z" fill="var(--color-accent)"/>
    </svg>
    <svg class="confetti c4" viewBox="0 0 14 14" fill="none">
      <path d="M7 0 L8 6 L14 7 L8 8 L7 14 L6 8 L0 7 L6 6 Z" fill="var(--color-primary)"/>
    </svg>

    <!-- Little doodles: arrow + dots + tick -->
    <svg class="doodle doodle-arrow" viewBox="0 0 80 60" fill="none">
      <path d="M5 30 Q 30 5, 70 25 M 60 18 L 70 25 L 62 32"
            stroke="var(--color-primary)" stroke-width="2.5"
            stroke-linecap="round" stroke-linejoin="round" fill="none"/>
    </svg>
    <svg class="doodle doodle-dots" viewBox="0 0 60 60" fill="none">
      <circle cx="6" cy="6" r="2.5" fill="var(--color-text)"/>
      <circle cx="20" cy="6" r="2.5" fill="var(--color-text)"/>
      <circle cx="34" cy="6" r="2.5" fill="var(--color-text)"/>
      <circle cx="6" cy="20" r="2.5" fill="var(--color-text)"/>
      <circle cx="20" cy="20" r="2.5" fill="var(--color-text)"/>
      <circle cx="34" cy="20" r="2.5" fill="var(--color-text)"/>
      <circle cx="6" cy="34" r="2.5" fill="var(--color-text)"/>
      <circle cx="20" cy="34" r="2.5" fill="var(--color-text)"/>
      <circle cx="34" cy="34" r="2.5" fill="var(--color-text)"/>
    </svg>
    <svg class="doodle doodle-tick" viewBox="0 0 40 40" fill="none">
      <circle cx="20" cy="20" r="17" stroke="var(--color-primary)" stroke-width="2.5" fill="none"/>
      <path d="M12 21 L18 27 L29 14" stroke="var(--color-primary)" stroke-width="2.8"
            stroke-linecap="round" stroke-linejoin="round" fill="none"/>
    </svg>
    <svg class="doodle doodle-wave" viewBox="0 0 240 40" fill="none" preserveAspectRatio="none">
      <path d="M2 20 Q 30 4, 60 20 T 120 20 T 180 20 T 238 20"
            stroke="var(--color-accent)" stroke-width="3" stroke-linecap="round" fill="none"/>
    </svg>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
.decor {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

/* ---------- Color mesh — drifting blobs ---------- */
.mesh {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.55;
  pointer-events: none;
}
.mesh-1 {
  width: 480px;
  height: 480px;
  background: var(--color-accent);
  top: -180px;
  left: 6%;
  animation: drift1 22s ease-in-out infinite;
}
.mesh-2 {
  width: 420px;
  height: 420px;
  background: var(--color-primary);
  bottom: -200px;
  left: 25%;
  opacity: 0.32;
  animation: drift2 26s ease-in-out infinite;
}
.mesh-3 {
  width: 340px;
  height: 340px;
  background: var(--color-accent);
  top: 30%;
  left: -160px;
  opacity: 0.35;
  animation: drift3 30s ease-in-out infinite;
}

:root[data-theme="dark"] .mesh-1 { opacity: 0.22; }
:root[data-theme="dark"] .mesh-2 { opacity: 0.18; }
:root[data-theme="dark"] .mesh-3 { opacity: 0.20; }

@keyframes drift1 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50%      { transform: translate(40px, 30px) scale(1.08); }
}
@keyframes drift2 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50%      { transform: translate(-50px, -20px) scale(1.05); }
}
@keyframes drift3 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50%      { transform: translate(30px, -40px) scale(1.1); }
}

/* ---------- Confetti stars scattered around ---------- */
.confetti {
  position: absolute;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.1));
}
.c1 {
  width: 30px; height: 30px;
  top: 14%;
  left: 4%;
  animation: float-spin 12s linear infinite;
}
.c2 {
  width: 22px; height: 22px;
  top: 64%;
  left: 9%;
  animation: float-spin 18s linear infinite reverse;
}
.c3 {
  width: 24px; height: 24px;
  top: 76%;
  left: 38%;
  animation: pulse-soft 3.4s ease-in-out infinite;
}
.c4 {
  width: 18px; height: 18px;
  top: 22%;
  left: 44%;
  animation: pulse-soft 2.8s ease-in-out infinite 0.6s;
}

@keyframes float-spin {
  from { transform: rotate(0); }
  to   { transform: rotate(360deg); }
}
@keyframes pulse-soft {
  0%, 100% { transform: scale(1); opacity: 0.8; }
  50%      { transform: scale(1.3); opacity: 1; }
}

/* ---------- Doodle bits ---------- */
.doodle { position: absolute; opacity: 0.55; }
.doodle-arrow {
  width: 90px; height: 60px;
  top: 50%;
  left: 32%;
  transform: rotate(-12deg);
}
.doodle-dots {
  width: 54px; height: 54px;
  top: 88%;
  left: 18%;
  opacity: 0.4;
}
.doodle-tick {
  width: 46px; height: 46px;
  top: 6%;
  left: 36%;
  animation: pulse-soft 4s ease-in-out infinite 1s;
}
.doodle-wave {
  width: 260px; height: 40px;
  bottom: 4%;
  left: 4%;
  opacity: 0.7;
}

@media (max-width: 760px) {
  .c3, .c4, .doodle-arrow, .doodle-dots, .doodle-tick { display: none; }
  .mesh-1, .mesh-2, .mesh-3 { filter: blur(60px); }
}
</style>
