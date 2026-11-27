import { useState } from 'react'
import type { BucketTotal } from '@/types/analytics'
import type { BucketType } from '@/types/account'
import { formatEUR } from '@/utils/format'

const BUCKETS: { type: BucketType; label: string; color: string }[] = [
  { type: 'daily', label: 'Diario', color: 'var(--series-1)' },
  { type: 'emergency', label: 'Emergencia', color: 'var(--series-2)' },
  { type: 'investment', label: 'Inversión', color: 'var(--series-3)' },
]

/**
 * Part-to-whole of net worth across the three buckets as one 100 % stacked bar.
 * Identity is never colour-alone: every segment is listed below with name, amount and share.
 */
export function BucketSplit({ buckets }: { buckets: BucketTotal[] }) {
  const [hovered, setHovered] = useState<BucketType | null>(null)
  const byType = new Map(buckets.map((b) => [b.bucket_type, b]))
  const positive = BUCKETS.map((b) => ({ ...b, value: Math.max(Number(byType.get(b.type)?.total ?? 0), 0) }))
  const total = positive.reduce((acc, b) => acc + b.value, 0)
  const share = (value: number) => (total === 0 ? 0 : (value / total) * 100)
  const pct = (value: number) =>
    new Intl.NumberFormat('es-ES', { maximumFractionDigits: 1 }).format(share(value)) + ' %'

  return (
    <figure className="space-y-4" aria-label="Reparto del patrimonio por cubo">
      <div className="flex h-3 w-full gap-[2px] rounded-full overflow-hidden bg-[var(--color-border)]">
        {total > 0 &&
          positive
            .filter((b) => b.value > 0)
            .map((b) => (
              <div
                key={b.type}
                className="h-full transition-opacity duration-150"
                style={{
                  width: `${share(b.value)}%`,
                  background: b.color,
                  opacity: hovered && hovered !== b.type ? 0.35 : 1,
                }}
                onMouseEnter={() => setHovered(b.type)}
                onMouseLeave={() => setHovered(null)}
                title={`${b.label}: ${formatEUR(b.value)} (${pct(b.value)})`}
              />
            ))}
      </div>

      <ul className="space-y-2">
        {positive.map((b) => {
          const detail = byType.get(b.type)
          const hasFunds = detail && Number(detail.funds_value) !== 0
          return (
            <li
              key={b.type}
              className="flex items-center justify-between gap-3 text-sm"
              onMouseEnter={() => setHovered(b.type)}
              onMouseLeave={() => setHovered(null)}
            >
              <span className="flex items-center gap-2 min-w-0">
                <span className="h-2.5 w-2.5 shrink-0 rounded-sm" style={{ background: b.color }} aria-hidden />
                <span className="text-[var(--color-text)]">{b.label}</span>
                <span className="num text-xs text-[var(--color-text-muted)]">{pct(b.value)}</span>
              </span>
              <span className="text-right">
                <span className="num font-medium text-[var(--color-text)]">{formatEUR(detail?.total ?? '0')}</span>
                {hasFunds && (
                  <span className="block num text-[11px] text-[var(--color-text-muted)]">
                    {formatEUR(detail.cash)} efectivo · {formatEUR(detail.funds_value)} fondos
                  </span>
                )}
              </span>
            </li>
          )
        })}
      </ul>
    </figure>
  )
}
