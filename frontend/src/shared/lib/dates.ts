/**
 * Human-friendly relative deadline labels, e.g. "через 3 дня", "сегодня до 23:59",
 * "просрочено на 2 дня". Returns the label and a "severity" useful for color-coding.
 */
export type DeadlineSeverity = 'safe' | 'soon' | 'today' | 'overdue'

const TIME_FMT: Intl.DateTimeFormatOptions = { hour: '2-digit', minute: '2-digit' }
const DATE_FMT: Intl.DateTimeFormatOptions = { day: '2-digit', month: '2-digit', year: 'numeric' }

function plural(n: number, one: string, few: string, many: string): string {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return one
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return few
  return many
}

export interface DeadlineInfo {
  label: string
  severity: DeadlineSeverity
}

/** Returns null if iso is null/invalid. */
export function describeDeadline(iso: string | null | undefined): DeadlineInfo | null {
  if (!iso) return null
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return null

  const now = new Date()
  const diffMs = d.getTime() - now.getTime()
  const dayMs = 24 * 60 * 60 * 1000

  // Compare by calendar day, not by 24h windows — "сегодня" if same date.
  const sameDay =
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()

  // Already overdue
  if (diffMs < 0) {
    const overdueDays = Math.floor(-diffMs / dayMs)
    if (overdueDays === 0) {
      return {
        label: `просрочено сегодня`,
        severity: 'overdue',
      }
    }
    return {
      label: `просрочено на ${overdueDays} ${plural(overdueDays, 'день', 'дня', 'дней')}`,
      severity: 'overdue',
    }
  }

  if (sameDay) {
    return {
      label: `сегодня до ${d.toLocaleTimeString('ru-RU', TIME_FMT)}`,
      severity: 'today',
    }
  }

  const days = Math.ceil(diffMs / dayMs)
  if (days === 1) return { label: 'завтра', severity: 'today' }
  if (days <= 3) return { label: `через ${days} ${plural(days, 'день', 'дня', 'дней')}`, severity: 'soon' }
  if (days <= 7) return { label: `через ${days} ${plural(days, 'день', 'дня', 'дней')}`, severity: 'safe' }

  return { label: d.toLocaleDateString('ru-RU', DATE_FMT), severity: 'safe' }
}

export function formatDateTime(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
