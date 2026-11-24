/** Format a decimal string as EUR with JetBrains Mono via CSS class `num` */
export function formatEUR(value: string | number): string {
  const n = typeof value === 'string' ? parseFloat(value) : value
  return new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(n)
}

/** Format ISO date string to dd/mm/yyyy */
export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(new Date(iso))
}

/** Format ISO date string to dd/mm/yyyy HH:mm */
export function formatDateTime(iso: string): string {
  return new Intl.DateTimeFormat('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso))
}

/** Current date in ISO format for input[type=datetime-local] */
export function nowISO(): string {
  return new Date().toISOString().slice(0, 16)
}

/** Extract axios error detail message */
export function apiErrorMessage(err: unknown): string {
  if (typeof err === 'object' && err !== null && 'response' in err) {
    const e = err as { response?: { data?: { detail?: string | { msg: string }[] } } }
    const detail = e.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) return detail.map((d) => d.msg).join(', ')
  }
  return 'Ha ocurrido un error inesperado.'
}
