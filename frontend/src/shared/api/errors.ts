import { AxiosError } from 'axios'

export function extractError(e: unknown, fallback = 'Что-то пошло не так'): string {
  if (e instanceof AxiosError) {
    const detail = e.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (detail && typeof detail === 'object') {
      if ('message' in detail && typeof detail.message === 'string') return detail.message
    }
    return e.message || fallback
  }
  if (e instanceof Error) return e.message
  return fallback
}
