import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { MonthTotal } from '@/types/analytics'
import { formatEUR, formatMonth } from '@/utils/format'

const SERIES = [
  { key: 'income', label: 'Ingresos', color: 'var(--series-1)' },
  { key: 'expense', label: 'Gastos', color: 'var(--series-2)' },
] as const

const compact = (n: number) =>
  new Intl.NumberFormat('es-ES', { notation: 'compact', maximumFractionDigits: 1 }).format(n)

/** Round axis ticks: step of 1, 2, 2.5 or 5 x 10^n giving at most ~5 intervals. */
function niceTicks(max: number): number[] {
  if (max <= 0) return [0]
  const raw = max / 4
  const magnitude = 10 ** Math.floor(Math.log10(raw))
  const step = [1, 2, 2.5, 5, 10].map((m) => m * magnitude).find((s) => s >= raw) ?? raw
  const top = Math.ceil(max / step) * step
  return Array.from({ length: Math.round(top / step) + 1 }, (_, i) => i * step)
}

interface Row {
  month: string
  income: number
  expense: number
  net: number
}

interface TooltipProps {
  active?: boolean
  payload?: ReadonlyArray<{ payload?: unknown }>
  label?: string | number
}

function MonthTooltip({ active, payload, label }: TooltipProps) {
  if (!active || !payload?.length) return null
  const row = payload[0].payload as Row
  return (
    <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-xs shadow-md space-y-1">
      <p className="font-medium text-[var(--color-text)]">{formatMonth(String(label))}</p>
      {SERIES.map((s) => (
        <p key={s.key} className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-1.5 text-[var(--color-text-muted)]">
            <span className="h-2 w-2 rounded-sm" style={{ background: s.color }} aria-hidden />
            {s.label}
          </span>
          <span className="num text-[var(--color-text)]">{formatEUR(row[s.key])}</span>
        </p>
      ))}
      <p className="flex justify-between gap-4 border-t border-[var(--color-border)] pt-1">
        <span className="text-[var(--color-text-muted)]">Ahorro</span>
        <span className="num text-[var(--color-text)]">{formatEUR(row.net)}</span>
      </p>
    </div>
  )
}

/** Income vs expenses per month: grouped bars on one shared axis. */
export function CashflowChart({ months }: { months: MonthTotal[] }) {
  const data = months.map((m) => ({
    month: m.month,
    income: Number(m.income),
    expense: Number(m.expense),
    net: Number(m.net),
  }))
  const ticks = niceTicks(Math.max(0, ...data.flatMap((d) => [d.income, d.expense])))

  return (
    <figure className="space-y-3">
      <figcaption className="flex items-center gap-4 text-xs text-[var(--color-text-muted)]">
        {SERIES.map((s) => (
          <span key={s.key} className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-sm" style={{ background: s.color }} aria-hidden />
            {s.label}
          </span>
        ))}
      </figcaption>
      <div className="h-56 md:h-64 -ml-2">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} barGap={2} barCategoryGap="28%">
            <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
            <XAxis
              dataKey="month"
              tickFormatter={formatMonth}
              tickLine={false}
              axisLine={false}
              tick={{ fill: 'var(--color-text-muted)', fontSize: 11 }}
            />
            <YAxis
              width={44}
              ticks={ticks}
              domain={[0, ticks[ticks.length - 1]]}
              tickFormatter={compact}
              tickLine={false}
              axisLine={false}
              tick={{ fill: 'var(--color-text-muted)', fontSize: 11 }}
            />
            <Tooltip
              content={(p) => <MonthTooltip active={p.active} payload={p.payload as TooltipProps['payload']} label={p.label} />}
              cursor={{ fill: 'var(--color-border)', opacity: 0.4 }} />
            {SERIES.map((s) => (
              <Bar key={s.key} dataKey={s.key} name={s.label} fill={s.color} radius={[4, 4, 0, 0]} maxBarSize={22} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </figure>
  )
}
