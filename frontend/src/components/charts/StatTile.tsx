import type { ReactNode } from 'react'

interface Props {
  label: string
  value: string
  detail?: ReactNode
  tone?: 'default' | 'positive' | 'negative'
  action?: ReactNode
}

const toneClass = {
  default: 'text-[var(--color-text)]',
  positive: 'text-[var(--color-success)]',
  negative: 'text-[var(--color-danger)]',
}

/** Single headline number: a figure is clearer than a chart for one value. */
export function StatTile({ label, value, detail, tone = 'default', action }: Props) {
  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 md:p-5 space-y-1 min-w-0">
      <div className="flex items-start justify-between gap-2">
        <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)]">{label}</p>
        {action}
      </div>
      <p className={`num text-2xl md:text-[1.75rem] font-semibold tracking-tight ${toneClass[tone]}`}>{value}</p>
      {detail && <div className="text-xs text-[var(--color-text-muted)]">{detail}</div>}
    </div>
  )
}
