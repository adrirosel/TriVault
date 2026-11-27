import { useCallback, useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { ErrorMessage } from '@/components/ui/ErrorMessage'
import { BucketSplit } from '@/components/charts/BucketSplit'
import { CashflowChart } from '@/components/charts/CashflowChart'
import { CategoryBars } from '@/components/charts/CategoryBars'
import { StatTile } from '@/components/charts/StatTile'
import { accountsApi } from '@/api/accounts'
import { analyticsApi } from '@/api/analytics'
import { authApi } from '@/api/auth'
import { transactionsApi } from '@/api/transactions'
import { useAuth } from '@/context/AuthContext'
import type { Account } from '@/types/account'
import type { Cashflow, FundsPerformance, Inflation, Summary } from '@/types/analytics'
import type { Transaction } from '@/types/transaction'
import { apiErrorMessage, formatDate, formatEUR, formatPct, formatSignedEUR } from '@/utils/format'

interface DashboardData {
  summary: Summary
  cashflow: Cashflow
  inflation: Inflation
  funds: FundsPerformance
  accounts: Account[]
  recent: Transaction[]
}

function Section({ title, action, children }: { title: string; action?: ReactNode; children: ReactNode }) {
  return (
    <section className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 md:p-5 space-y-4 min-w-0">
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="text-[1rem] font-semibold text-[var(--color-text)]">{title}</h2>
        {action}
      </div>
      {children}
    </section>
  )
}

function InflationRateEditor({ rate, onSaved }: { rate: string; onSaved: () => Promise<void> }) {
  const [editing, setEditing] = useState(false)
  const [value, setValue] = useState(rate)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await authApi.patchMe(value)
      await onSaved()
      setEditing(false)
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  if (!editing) {
    return (
      <button
        type="button"
        className="text-xs text-[var(--color-accent)] hover:opacity-80 whitespace-nowrap"
        onClick={() => {
          setValue(rate)
          setEditing(true)
        }}
      >
        IPC {formatPct(rate, false)} · cambiar
      </button>
    )
  }
  return (
    <form onSubmit={submit} className="flex items-center gap-2">
      <input
        aria-label="Inflación anual (%)"
        className="num w-20 rounded-md border border-[var(--color-border)] bg-[var(--color-base)] px-2 py-1 text-[1rem] md:text-sm text-[var(--color-text)]"
        type="number"
        step="0.01"
        min="0"
        max="100"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        autoFocus
      />
      <Button requiresNetwork type="submit" loading={saving} className="px-2 py-1">
        OK
      </Button>
      {error && <span className="text-xs text-[var(--color-danger)]">{error}</span>}
    </form>
  )
}

export function Dashboard() {
  const { refreshUser } = useAuth()
  const [data, setData] = useState<DashboardData | null>(null)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    try {
      const [summary, cashflow, inflation, funds, accounts, recent] = await Promise.all([
        analyticsApi.summary(),
        analyticsApi.cashflow(6),
        analyticsApi.inflation(),
        analyticsApi.funds(),
        accountsApi.list(),
        transactionsApi.list({ limit: 6 }),
      ])
      setData({
        summary: summary.data,
        cashflow: cashflow.data,
        inflation: inflation.data,
        funds: funds.data,
        accounts: accounts.data,
        recent: recent.data,
      })
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const afterRateChange = async () => {
    await refreshUser()
    await load()
  }

  const accountName = (id: number) => data?.accounts.find((a) => a.id === id)?.name ?? `#${id}`
  const savings = data?.cashflow.savings_rate ?? null

  return (
    <Layout
      title="Dashboard"
      actions={
        <Link to="/transacciones">
          <Button type="button">Registrar movimiento</Button>
        </Link>
      }
    >
      <ErrorMessage message={error} />

      {!data ? (
        !error && <p className="num text-sm text-[var(--color-text-muted)] animate-pulse">Cargando…</p>
      ) : (
        <div className="space-y-4 md:space-y-6">
          {/* Headline figures: one number each, no chart needed */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 md:gap-4">
            <StatTile
              label="Patrimonio neto"
              value={formatEUR(data.summary.net_worth)}
              detail={`${data.accounts.length} ${data.accounts.length === 1 ? 'cuenta' : 'cuentas'}`}
            />
            <StatTile
              label="Tasa de ahorro (mes)"
              value={formatPct(savings, false)}
              tone={savings == null ? 'default' : Number(savings) >= 0 ? 'positive' : 'negative'}
              detail={
                <span className="num">
                  {formatEUR(data.cashflow.income)} ingresos · {formatEUR(data.cashflow.expense)} gastos
                </span>
              }
            />
            <StatTile
              label="Pérdida por inflación"
              value={`${formatEUR(data.inflation.annual_loss)}/año`}
              tone={Number(data.inflation.annual_loss) > 0 ? 'negative' : 'default'}
              detail={
                <span className="num">
                  {formatEUR(data.inflation.monthly_loss)}/mes sobre {formatEUR(data.inflation.liquid_balance)} líquidos
                </span>
              }
              action={<InflationRateEditor rate={data.inflation.annual_inflation_rate} onSaved={afterRateChange} />}
            />
          </div>

          <div className="grid grid-cols-[minmax(0,1fr)] gap-4 md:gap-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
            <Section title="Reparto por cubo">
              <BucketSplit buckets={data.summary.buckets} />
            </Section>

            <Section
              title="Ingresos vs gastos"
              action={<span className="text-xs text-[var(--color-text-muted)]">últimos 6 meses</span>}
            >
              <CashflowChart months={data.cashflow.monthly} />
            </Section>
          </div>

          <div className="grid grid-cols-[minmax(0,1fr)] gap-4 md:gap-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
            <Section
              title="Gasto por categoría (mes)"
              action={
                <span className="num text-[11px] text-[var(--color-text-muted)] text-right">
                  fijo {formatEUR(data.cashflow.fixed_expense)} · variable {formatEUR(data.cashflow.variable_expense)}
                </span>
              }
            >
              <CategoryBars categories={data.cashflow.by_category} />
            </Section>

            <Section
              title="Fondos indexados"
              action={
                <Link to="/inversiones" className="text-xs text-[var(--color-accent)] hover:opacity-80">
                  Ver inversiones
                </Link>
              }
            >
              {data.funds.positions.length === 0 ? (
                <p className="text-sm text-[var(--color-text-muted)]">
                  Aún no tienes fondos. Añádelos desde{' '}
                  <Link to="/inversiones" className="text-[var(--color-accent)]">
                    Inversiones
                  </Link>
                  .
                </p>
              ) : (
                <div className="space-y-4">
                  <dl className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                    {[
                      ['Valor', formatEUR(data.funds.market_value)],
                      ['Invertido', formatEUR(data.funds.invested)],
                      ['Rentab. nominal', formatPct(data.funds.nominal_return_pct)],
                      ['Rentab. real', formatPct(data.funds.real_return_pct)],
                    ].map(([label, value]) => (
                      <div key={label}>
                        <dt className="text-xs text-[var(--color-text-muted)]">{label}</dt>
                        <dd className="num font-medium text-[var(--color-text)]">{value}</dd>
                      </div>
                    ))}
                  </dl>
                  {data.funds.beats_inflation != null && (
                    <p className="text-sm">
                      <span
                        className={data.funds.beats_inflation ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'}
                      >
                        {data.funds.beats_inflation ? '▲ Tu cartera bate a la inflación' : '▼ Tu cartera no bate a la inflación'}
                      </span>{' '}
                      <span className="num text-[var(--color-text-muted)]">({formatSignedEUR(data.funds.real_gain)} reales)</span>
                    </p>
                  )}
                </div>
              )}
            </Section>
          </div>

          <Section
            title="Movimientos recientes"
            action={
              <Link to="/transacciones" className="text-xs text-[var(--color-accent)] hover:opacity-80">
                Ver todos
              </Link>
            }
          >
            {data.recent.length === 0 ? (
              <p className="text-sm text-[var(--color-text-muted)]">Sin movimientos todavía — registra el primero.</p>
            ) : (
              <ul className="divide-y divide-[var(--color-border)] -mx-4 md:-mx-5">
                {data.recent.map((tx) => (
                  <li key={tx.id} className="flex items-center justify-between gap-4 px-4 md:px-5 py-3">
                    <div className="min-w-0 space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant={tx.type} />
                        <span className="num text-xs text-[var(--color-text-muted)]">{formatDate(tx.transaction_date)}</span>
                      </div>
                      <p className="text-sm text-[var(--color-text)] truncate">
                        {tx.description || accountName(tx.account_id)}
                        {tx.type === 'transfer' && tx.destination_account_id ? ` → ${accountName(tx.destination_account_id)}` : ''}
                      </p>
                    </div>
                    <span
                      className={[
                        'num text-sm font-medium shrink-0',
                        tx.type === 'expense'
                          ? 'text-[var(--color-danger)]'
                          : tx.type === 'income'
                            ? 'text-[var(--color-success)]'
                            : 'text-[var(--color-text)]',
                      ].join(' ')}
                    >
                      {tx.type === 'expense' ? '−' : tx.type === 'income' ? '+' : ''}
                      {formatEUR(tx.amount)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </Section>
        </div>
      )}
    </Layout>
  )
}
