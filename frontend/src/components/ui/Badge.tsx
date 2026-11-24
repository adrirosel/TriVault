type Variant = 'income' | 'expense' | 'transfer' | 'daily' | 'emergency' | 'investment' | 'fixed' | 'variable'

const map: Record<Variant, { label: string; cls: string }> = {
  income: {
    label: 'Ingreso',
    cls: 'bg-[var(--color-success-bg)] text-[var(--color-success)] border-[var(--color-success)]/25',
  },
  expense: {
    label: 'Gasto',
    cls: 'bg-[var(--color-danger-bg)] text-[var(--color-danger)] border-[var(--color-danger)]/25',
  },
  transfer: {
    label: 'Transferencia',
    cls: 'bg-[var(--color-accent-light)] text-[var(--color-accent)] border-[var(--color-accent)]/25',
  },
  daily: {
    label: 'Diario',
    cls: 'bg-[var(--color-accent-light)] text-[var(--color-accent)] border-[var(--color-accent)]/25',
  },
  emergency: {
    label: 'Emergencia',
    cls: 'bg-[var(--color-warn-bg)] text-[var(--color-warn)] border-[var(--color-warn)]/25',
  },
  investment: {
    label: 'Inversión',
    cls: 'bg-[var(--color-base)] text-[var(--color-text-muted)] border-[var(--color-border)]',
  },
  fixed: {
    label: 'Fijo',
    cls: 'bg-[var(--color-base)] text-[var(--color-text-muted)] border-[var(--color-border)]',
  },
  variable: {
    label: 'Variable',
    cls: 'bg-transparent text-[var(--color-text-muted)] border-[var(--color-border)]',
  },
}

interface Props {
  variant: Variant
  label?: string
}

export function Badge({ variant, label }: Props) {
  const { label: defaultLabel, cls } = map[variant]
  return (
    <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${cls}`}>
      {label ?? defaultLabel}
    </span>
  )
}
