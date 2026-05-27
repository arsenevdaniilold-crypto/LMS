import { ref, watch } from 'vue'

export type ThemeMode = 'light' | 'dark'
const STORAGE_KEY = 'cf-theme'

function initial(): ThemeMode {
  if (typeof window === 'undefined') return 'light'
  const saved = localStorage.getItem(STORAGE_KEY) as ThemeMode | null
  if (saved === 'light' || saved === 'dark') return saved
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

const mode = ref<ThemeMode>(initial())

function apply(value: ThemeMode) {
  if (typeof document === 'undefined') return
  document.documentElement.setAttribute('data-theme', value)
}

apply(mode.value)

watch(mode, (v) => {
  apply(v)
  try { localStorage.setItem(STORAGE_KEY, v) } catch { /* ignore */ }
})

export function useTheme() {
  return {
    mode,
    toggle() {
      mode.value = mode.value === 'dark' ? 'light' : 'dark'
    },
    set(v: ThemeMode) {
      mode.value = v
    },
  }
}
