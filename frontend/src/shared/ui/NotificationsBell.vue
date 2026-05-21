<template>
  <div class="bell-wrapper" ref="rootEl">
    <button class="bell-btn" :class="{ active: open }" :title="wsTitle" @click="toggle">
      <span class="bell-icon">🔔</span>
      <span v-if="notif.unreadCount > 0" class="badge">{{ notif.unreadCount }}</span>
      <span class="ws-dot" :class="`ws-${wsState}`"></span>
    </button>

    <div v-if="open" class="dropdown">
      <div class="dropdown-header">
        <h3>Уведомления</h3>
        <button v-if="notif.unreadCount > 0" class="link-btn" @click="onMarkAll">
          Отметить всё прочитанным
        </button>
      </div>
      <div class="dropdown-body">
        <div v-if="notif.loading" class="muted">Загрузка…</div>
        <div v-else-if="notif.items.length === 0" class="muted">Пока пусто</div>
        <button
          v-for="n in notif.items"
          :key="n.id"
          class="notif-item"
          :class="{ unread: !n.read }"
          @click="onClick(n)"
        >
          <div class="notif-title">{{ titleFor(n) }}</div>
          <div class="notif-meta">{{ formatDate(n.created_at) }}</div>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationStore } from '@/shared/stores/notificationStore'
import { wsState } from '@/shared/ws/client'
import type { Notification } from '@/shared/api/types'

const notif = useNotificationStore()
const router = useRouter()
const open = ref(false)
const rootEl = ref<HTMLElement | null>(null)

const wsTitle = computed(() => {
  if (wsState.value === 'connected') return 'Real-time подключено'
  if (wsState.value === 'connecting') return 'Подключение…'
  return 'Real-time отключено'
})

function toggle() {
  open.value = !open.value
}

function onDocClick(e: MouseEvent) {
  if (!rootEl.value) return
  if (!rootEl.value.contains(e.target as Node)) open.value = false
}

onMounted(() => {
  document.addEventListener('click', onDocClick)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', onDocClick)
})

async function onMarkAll() {
  await notif.markAllRead()
}

function titleFor(n: Notification): string {
  const p = n.payload as Record<string, string>
  switch (n.type) {
    case 'announcement_created':
      return `Новое объявление в ${p.class_name || 'классе'}: ${p.title || ''}`
    case 'announcement_updated':
      return `Объявление изменено в ${p.class_name || 'классе'}: ${p.title || ''}`
    case 'announcement_deleted':
      return `Объявление удалено в ${p.class_name || 'классе'}`
    case 'assignment_created':
      return `Новое задание в ${p.class_name || 'классе'}: ${p.name || ''}`
    case 'assignment_updated':
      return `Задание изменено в ${p.class_name || 'классе'}: ${p.name || ''}`
    case 'assignment_deleted':
      return `Задание удалено в ${p.class_name || 'классе'}: ${p.name || ''}`
    case 'solution_graded':
      return p.redistributed
        ? `Оценки распределены: ${p.assignment_name || ''}`
        : `Решение оценено: ${p.assignment_name || ''}${p.grade ? ` (${p.grade})` : ''}`
    case 'solution_returned':
      return `Решение возвращено на доработку: ${p.assignment_name || ''}`
    case 'solution_pending_redistribution':
      return `Нужно перераспределить оценку: ${p.assignment_name || ''}`
    default:
      return n.type
  }
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function onClick(n: Notification) {
  await notif.markOneRead(n.id)
  const p = n.payload as Record<string, string>
  open.value = false
  if (n.type.startsWith('announcement_') && p.class_id) {
    await router.push(`/classes/${p.class_id}`)
  } else if (n.type === 'assignment_deleted' && p.class_id) {
    // assignment is gone — go to the class
    await router.push(`/classes/${p.class_id}`)
  } else if ((n.type === 'assignment_created' || n.type === 'assignment_updated') && p.assignment_id) {
    await router.push(`/assignments/${p.assignment_id}`)
  } else if (
    (n.type === 'solution_graded' ||
      n.type === 'solution_returned' ||
      n.type === 'solution_pending_redistribution') &&
    p.solution_id
  ) {
    if (n.type === 'solution_pending_redistribution') {
      await router.push(`/solutions/${p.solution_id}/redistribute`)
    } else {
      await router.push(`/solutions/${p.solution_id}`)
    }
  }
}
</script>

<style scoped>
.bell-wrapper {
  position: relative;
}
.bell-btn {
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.bell-btn.active {
  background: var(--color-surface);
}
.bell-icon {
  font-size: 16px;
}
.badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: var(--color-danger);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
}
.ws-dot {
  position: absolute;
  bottom: -2px;
  right: -2px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: 1.5px solid var(--color-bg);
}
.ws-connected { background: var(--color-success); }
.ws-connecting { background: var(--color-warning); }
.ws-disconnected { background: var(--color-text-muted); }
.dropdown {
  position: absolute;
  top: 44px;
  right: 0;
  width: 360px;
  max-height: 480px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.dropdown-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.dropdown-header h3 {
  font-size: 14px;
  margin: 0;
}
.link-btn {
  background: transparent;
  color: var(--color-primary);
  padding: 0;
  font-size: 12px;
  border: none;
}
.dropdown-body {
  overflow-y: auto;
  flex: 1;
}
.muted {
  padding: 16px;
  color: var(--color-text-muted);
  font-size: 14px;
  text-align: center;
}
.notif-item {
  width: 100%;
  background: transparent;
  border: none;
  border-bottom: 1px solid var(--color-border);
  text-align: left;
  padding: 10px 16px;
  display: block;
}
.notif-item:last-child {
  border-bottom: none;
}
.notif-item:hover {
  background: var(--color-surface);
}
.notif-item.unread {
  background: #eff6ff;
}
.notif-title {
  font-size: 13px;
  line-height: 1.3;
  color: var(--color-text);
}
.notif-meta {
  font-size: 11px;
  color: var(--color-text-muted);
  margin-top: 2px;
}

@media (max-width: 640px) {
  .dropdown {
    width: 92vw;
    right: -8px;
  }
}
</style>
