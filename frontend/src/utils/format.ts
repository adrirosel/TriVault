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

/** Convert an ISO date (or now) to the local "YYYY-MM-DDTHH:mm" value expected by input[type=datetime-local]. */
export function toLocalInputValue(iso?: string): string {
  const d = iso ? new Date(iso) : new Date()
  return new Date(d.getTime() - d.getTimezoneOffset() * 60_000).toISOString().slice(0, 16)
}

/** Current local date-time for input[type=datetime-local] (toISOString alone would be UTC). */
export function nowISO(): string {
  return toLocalInputValue()
}

/** Parse a decimal string ("-1234.5") into integer cents without float arithmetic. */
function toCents(value: string): bigint {
  const trimmed = value.trim()
  const negative = trimmed.startsWith('-')
  const [intPart, fracPart = ''] = trimmed.replace(/^[-+]/, '').split('.')
  const cents = BigInt(intPart || '0') * 100n + BigInt((fracPart + '00').slice(0, 2))
  return negative ? -cents : cents
}

/** Sum decimal money strings exactly (integer cents) and return a 2-decimal string. */
export function sumDecimal(values: string[]): string {
  const total = values.reduce((acc, v) => acc + toCents(v), 0n)
  const negative = total < 0n
  const abs = negative ? -total : total
  const frac = (abs % 100n).toString().padStart(2, '0')
  return `${negative ? '-' : ''}${abs / 100n}.${frac}`
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
