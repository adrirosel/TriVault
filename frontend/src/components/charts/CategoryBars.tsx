import type { CategoryTotal } from '@/types/analytics'
import { formatEUR } from '@/utils/format'

const MAX_ROWS = 6

/** Expense by category: one series, sorted, every bar labelled with its amount. Long tails fold into "Otras". */
export function CategoryBars({ categories }: { categories: CategoryTotal[] }) {
  const expenses = categories.filter((c) => c.type === 'expense')
  if (expenses.length === 0) {
    return <p className="text-sm text-[var(--color-text-muted)]">Sin gastos en este periodo.</p>
  }

  const rows = expenses.slice(0, MAX_ROWS).map((c) => ({ key: String(c.category_id), name: c.name, fixed: c.is_fixed, value: Number(c.total) }))
  const rest = expenses.slice(MAX_ROWS).reduce((acc, c) => acc + Number(c.total), 0)
  if (rest > 0) rows.push({ key: 'other', name: 'Otras', fixed: false, value: rest })
  const max = Math.max(...rows.map((r) => r.value))

  return (
    <ul className="space-y-3" aria-label="Gasto por categoría">
      {rows.map((r) => (
        <li key={r.key} className="space-y-1" title={`${r.name}: ${formatEUR(r.value)}`}>
          <div className="flex items-baseline justify-between gap-3 text-sm">
            <span className="truncate text-[var(--color-text)]">
              {r.name}
              {r.fixed && <span className="ml-1.5 text-[11px] text-[var(--color-text-muted)]">fijo</span>}
            </span>
            <span className="num text-[var(--color-text)]">{formatEUR(r.value)}</span>
          </div>
          <div className="h-2 rounded-full bg-[var(--color-border)]/60">
            <div
              className="h-full rounded-full"
              style={{ width: `${max === 0 ? 0 : (r.value / max) * 100}%`, background: 'var(--series-1)' }}
            />
          </div>
        </li>
      ))}
    </ul>
  )
}
