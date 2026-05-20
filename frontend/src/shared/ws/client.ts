import { ref } from 'vue'
import { useNotificationStore } from '@/shared/stores/notificationStore'

let socket: WebSocket | null = null
let reconnectTimer: number | null = null
let stopped = false

export const wsState = ref<'disconnected' | 'connecting' | 'connected'>('disconnected')

function wsUrl(): string {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${window.location.host}/ws`
}

function scheduleReconnect() {
  if (stopped) return
  if (reconnectTimer != null) return
  reconnectTimer = window.setTimeout(() => {
    reconnectTimer = null
    connect()
  }, 3000)
}

export function connect() {
  stopped = false
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    return
  }
  try {
    socket = new WebSocket(wsUrl())
    wsState.value = 'connecting'
  } catch (e) {
    console.warn('[ws] failed to create socket', e)
    wsState.value = 'disconnected'
    scheduleReconnect()
    return
  }

  socket.onopen = () => {
    console.log('[ws] open')
    wsState.value = 'connected'
  }

  socket.onmessage = (event) => {
    console.log('[ws] message', event.data)
    try {
      const data = JSON.parse(event.data)
      const store = useNotificationStore()
      store.handleIncoming(data)
    } catch (e) {
      console.warn('[ws] handle error', e)
    }
  }

  socket.onclose = (event) => {
    console.log('[ws] close', event.code, event.reason)
    socket = null
    wsState.value = 'disconnected'
    scheduleReconnect()
  }

  socket.onerror = (e) => {
    console.warn('[ws] error', e)
    socket?.close()
  }
}

export function disconnect() {
  stopped = true
  if (reconnectTimer != null) {
    window.clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  socket?.close()
  socket = null
  wsState.value = 'disconnected'
}
