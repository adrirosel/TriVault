import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'
import { Button } from '@/components/ui/Button'
import { ErrorMessage } from '@/components/ui/ErrorMessage'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { accountsApi } from '@/api/accounts'
import { analyticsApi } from '@/api/analytics'
import { fundsApi } from '@/api/funds'
import type { Account } from '@/types/account'
import type { FundPerformance } from '@/types/analytics'
import type { FundContribution, FundPosition, OrderType } from '@/types/fund'
import {
  apiErrorMessage,
  formatDate,
  formatEUR,
  formatPct,
  formatQty,
  formatSignedEUR,
  todayISODate,
} from '@/utils/format'

const card = 'rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 md:p-5'

/** Suggested gross amount = shares x NAV, rounded to cents (the user can override it). */
function suggestGross(shares: string, nav: string): string {
  const s = Number(shares)
  const n = Number(nav)
  if (!s || !n) return ''
  return (Math.round(s * n * 100) / 100).toFixed(2)
}

function Metric({ label, value, tone }: { label: string; value: string; tone?: 'pos' | 'neg' }) {
  const color =
    tone === 'pos' ? 'text-[var(--color-success)]' : tone === 'neg' ? 'text-[var(--color-danger)]' : 'text-[var(--color-text)]'
  return (
    <div className="min-w-0">
      <dt className="text-[11px] uppercase tracking-wide text-[var(--color-text-muted)]">{label}</dt>
      <dd className={`num text-sm font-medium truncate ${color}`}>{value}</dd>
    </div>
  )
}

const signTone = (value: string | null) => (value == null || Number(value) === 0 ? undefined : Number(value) > 0 ? 'pos' : 'neg')

function ContributionHistory({
  position,
  onChanged,
  onError,
}: {
  position: FundPosition
  onChanged: () => Promise<void>
  onError: (msg: string) => void
}) {
  const [items, setItems] = useState<FundContribution[] | null>(null)

  const load = useCallback(async () => {
    const { data } = await fundsApi.contributions(position.id)
    setItems(data)
  }, [position.id])

  useEffect(() => {
    void load()
  }, [load])

  const remove = async (c: FundContribution) => {
    const verb = c.order_type === 'buy' ? 'compra' : 'venta'
    if (!confirm(`¿Eliminar esta ${verb}? Se recalculará la posición${c.affects_cash ? ' y se revertirá el efectivo' : ''}.`)) return
    try {
      await fundsApi.removeContribution(position.id, c.id)
      await load()
      await onChanged()
    } catch (err) {
      onError(apiErrorMessage(err))
    }
  }

  if (!items) return <p className="text-xs text-[var(--color-text-muted)] animate-pulse">Cargando…</p>
  if (items.length === 0) return <p className="text-xs text-[var(--color-text-muted)]">Sin operaciones.</p>
  return (
    <ul className="divide-y divide-[var(--color-border)] text-sm">
      {items.map((c) => (
        <li key={c.id} className="flex items-center justify-between gap-3 py-2">
          <div className="min-w-0">
            <p className="text-[var(--color-text)]">
              <span className={c.order_type === 'buy' ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'}>
                {c.order_type === 'buy' ? 'Compra' : 'Venta'}
              </span>{' '}
              <span className="num">
                {formatQty(c.shares)} × {formatQty(c.purchase_nav)} €
              </span>
            </p>
            <p className="num text-xs text-[var(--color-text-muted)]">
              {formatDate(c.operation_date)} · {formatEUR(c.gross_amount)}
              {Number(c.fee) > 0 && ` + ${formatEUR(c.fee)} comisión`}
              {!c.affects_cash && ' · histórica'}
            </p>
          </div>
          <Button requiresNetwork type="button" variant="danger" className="px-2 py-1 text-xs" onClick={() => void remove(c)}>
            Eliminar
          </Button>
        </li>
      ))}
    </ul>
  )
}

export function Investments() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [positions, setPositions] = useState<FundPosition[]>([])
  const [performance, setPerformance] = useState<Map<number, FundPerformance>>(new Map())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState<number | null>(null)
  const [navEdit, setNavEdit] = useState<{ id: number; value: string } | null>(null)

  // New fund form
  const [fundAccount, setFundAccount] = useState('')
  const [isin, setIsin] = useState('')
  const [fundName, setFundName] = useState('')
  const [savingFund, setSavingFund] = useState(false)

  // Operation form
  const [opFund, setOpFund] = useState('')
  const [opType, setOpType] = useState<OrderType>('buy')
  const [opDate, setOpDate] = useState(todayISODate())
  const [opShares, setOpShares] = useState('')
  const [opNav, setOpNav] = useState('')
  const [opGross, setOpGross] = useState('')
  const [opGrossTouched, setOpGrossTouched] = useState(false)
  const [opFee, setOpFee] = useState('0')
  const [opNotes, setOpNotes] = useState('')
  const [opHistorical, setOpHistorical] = useState(false)
  const [savingOp, setSavingOp] = useState(false)

  const investmentAccounts = useMemo(() => accounts.filter((a) => a.bucket_type === 'investment'), [accounts])

  const load = useCallback(async () => {
    try {
      const [acc, pos, perf] = await Promise.all([accountsApi.list(), fundsApi.list(), analyticsApi.funds()])
      setAccounts(acc.data)
      setPositions(pos.data)
      setPerformance(new Map(perf.data.positions.map((p) => [p.position_id, p])))
      const firstInvestment = acc.data.find((a) => a.bucket_type === 'investment')
      setFundAccount((prev) => prev || (firstInvestment ? String(firstInvestment.id) : ''))
      setOpFund((prev) => (prev && pos.data.some((p) => String(p.id) === prev) ? prev : pos.data[0] ? String(pos.data[0].id) : ''))
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const accountOf = (id: number) => accounts.find((a) => a.id === id)
  const selectedFund = positions.find((p) => String(p.id) === opFund)
  const selectedCash = selectedFund ? accountOf(selectedFund.account_id)?.current_balance : undefined

  const createFund = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setSavingFund(true)
    try {
      const { data } = await fundsApi.create({ account_id: Number(fundAccount), isin: isin.trim(), fund_name: fundName })
      setIsin('')
      setFundName('')
      setOpFund(String(data.id))
      await load()
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setSavingFund(false)
    }
  }

  const submitOperation = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setSavingOp(true)
    try {
      await fundsApi.addContribution(Number(opFund), {
        operation_date: opDate,
        order_type: opType,
        shares: opShares,
        purchase_nav: opNav,
        gross_amount: opGross,
        fee: opFee || '0',
        notes: opNotes || undefined,
        affects_cash: !opHistorical,
      })
      setOpShares('')
      setOpNav('')
      setOpGross('')
      setOpGrossTouched(false)
      setOpFee('0')
      setOpNotes('')
      setOpHistorical(false)
      await load()
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setSavingOp(false)
    }
  }

  const saveNav = async () => {
    if (!navEdit) return
    setError('')
    try {
      await fundsApi.update(navEdit.id, { current_nav: navEdit.value })
      setNavEdit(null)
      await load()
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }

  const deleteFund = async (p: FundPosition) => {
    if (!confirm(`¿Eliminar ${p.fund_name}? Solo es posible si no tiene operaciones.`)) return
    setError('')
    try {
      await fundsApi.remove(p.id)
      await load()
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }

  const onSharesOrNav = (shares: string, nav: string) => {
    if (!opGrossTouched) setOpGross(suggestGross(shares, nav))
  }

  return (
    <Layout title="Inversiones">
      <ErrorMessage message={error} />

      {loading ? (
        <p className="num text-sm text-[var(--color-text-muted)] animate-pulse">Cargando…</p>
      ) : investmentAccounts.length === 0 ? (
        <p className={`${card} prose-narrow text-sm text-[var(--color-text-muted)]`}>
          Necesitas una cuenta de tipo <strong>Inversión</strong> (tu bróker) para registrar fondos.{' '}
          <Link to="/cuentas" className="text-[var(--color-accent)]">
            Crear cuenta
          </Link>
        </p>
      ) : (
        <div className="grid grid-cols-[minmax(0,1fr)] gap-6 md:gap-8 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)]">
          <section className="space-y-4">
            {positions.length === 0 && (
              <p className={`${card} text-sm text-[var(--color-text-muted)]`}>
                Aún no tienes fondos. Da de alta el primero con su ISIN.
              </p>
            )}
            {positions.map((p) => {
              const perf = performance.get(p.id)
              const account = accountOf(p.account_id)
              return (
                <article key={p.id} className={`${card} space-y-4`}>
                  <header className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h2 className="font-semibold text-[var(--color-text)] truncate">{p.fund_name}</h2>
                      <p className="num text-xs text-[var(--color-text-muted)]">
                        {p.isin} · {account?.name ?? `#${p.account_id}`}
                      </p>
                    </div>
                    <p className="num text-lg font-semibold text-[var(--color-text)] shrink-0">{formatEUR(p.market_value)}</p>
                  </header>

                  <dl className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <Metric label="Participaciones" value={formatQty(p.shares)} />
                    <Metric label="Invertido" value={formatEUR(p.total_invested)} />
                    <Metric
                      label="Plusvalía"
                      value={perf ? `${formatSignedEUR(perf.nominal_gain)} (${formatPct(perf.nominal_return_pct)})` : '—'}
                      tone={signTone(perf?.nominal_gain ?? null)}
                    />
                    <Metric
                      label="Real vs IPC"
                      value={perf ? formatPct(perf.real_return_pct) : '—'}
                      tone={signTone(perf?.real_return_pct ?? null)}
                    />
                  </dl>

                  <div className="flex flex-wrap items-center gap-2 text-xs text-[var(--color-text-muted)]">
                    {navEdit?.id === p.id ? (
                      <>
                        <input
                          aria-label="Nuevo valor liquidativo"
                          className="num w-28 rounded-md border border-[var(--color-border)] bg-[var(--color-base)] px-2 py-1 text-[1rem] md:text-sm text-[var(--color-text)]"
                          type="number"
                          step="0.0001"
                          min="0.0001"
                          value={navEdit.value}
                          onChange={(e) => setNavEdit({ id: p.id, value: e.target.value })}
                          autoFocus
                        />
                        <Button requiresNetwork type="button" className="px-2 py-1 text-xs" onClick={() => void saveNav()}>
                          Guardar
                        </Button>
                        <Button type="button" variant="ghost" className="px-2 py-1 text-xs" onClick={() => setNavEdit(null)}>
                          Cancelar
                        </Button>
                      </>
                    ) : (
                      <>
                        <span className="num">
                          VL {formatQty(p.current_nav)} € · {formatDate(p.last_updated)}
                        </span>
                        <Button
                          requiresNetwork
                          type="button"
                          variant="ghost"
                          className="px-2 py-1 text-xs"
                          onClick={() => setNavEdit({ id: p.id, value: p.current_nav })}
                        >
                          Actualizar VL
                        </Button>
                      </>
                    )}
                    <Button
                      type="button"
                      variant="ghost"
                      className="px-2 py-1 text-xs"
                      onClick={() => setExpanded(expanded === p.id ? null : p.id)}
                    >
                      {expanded === p.id ? 'Ocultar operaciones' : 'Operaciones'}
                    </Button>
                    {Number(p.shares) === 0 && (
                      <Button requiresNetwork type="button" variant="danger" className="px-2 py-1 text-xs" onClick={() => void deleteFund(p)}>
                        Eliminar
                      </Button>
                    )}
                  </div>

                  {expanded === p.id && (
                    <ContributionHistory position={p} onChanged={load} onError={setError} />
                  )}
                </article>
              )
            })}
          </section>

          <section className="space-y-6">
            {positions.length > 0 && (
              <form onSubmit={submitOperation} className={`${card} space-y-4`}>
                <h2 className="text-lg font-semibold text-[var(--color-text)]">Registrar operación</h2>
                <Select
                  label="Fondo"
                  required
                  options={positions.map((p) => ({ value: String(p.id), label: `${p.fund_name} (${p.isin})` }))}
                  value={opFund}
                  onChange={(e) => setOpFund(e.target.value)}
                />
                <div className="grid grid-cols-2 gap-3">
                  <Select
                    label="Tipo"
                    options={[
                      { value: 'buy', label: 'Compra' },
                      { value: 'sell', label: 'Venta' },
                    ]}
                    value={opType}
                    onChange={(e) => setOpType(e.target.value as OrderType)}
                  />
                  <Input
                    label="Fecha"
                    className="num"
                    type="date"
                    required
                    max={todayISODate()}
                    value={opDate}
                    onChange={(e) => setOpDate(e.target.value)}
                  />
                  <Input
                    label="Participaciones"
                    className="num"
                    type="number"
                    step="0.0001"
                    min="0.0001"
                    required
                    value={opShares}
                    onChange={(e) => {
                      setOpShares(e.target.value)
                      onSharesOrNav(e.target.value, opNav)
                    }}
                  />
                  <Input
                    label="Valor liquidativo"
                    className="num"
                    type="number"
                    step="0.0001"
                    min="0.0001"
                    required
                    value={opNav}
                    onChange={(e) => {
                      setOpNav(e.target.value)
                      onSharesOrNav(opShares, e.target.value)
                    }}
                  />
                  <Input
                    label="Importe bruto (€)"
                    className="num"
                    type="number"
                    step="0.01"
                    min="0.01"
                    required
                    value={opGross}
                    onChange={(e) => {
                      setOpGross(e.target.value)
                      setOpGrossTouched(true)
                    }}
                  />
                  <Input
                    label="Comisión (€)"
                    className="num"
                    type="number"
                    step="0.01"
                    min="0"
                    value={opFee}
                    onChange={(e) => setOpFee(e.target.value)}
                  />
                </div>
                <Input label="Notas" placeholder="Opcional" value={opNotes} onChange={(e) => setOpNotes(e.target.value)} />

                <label className="flex items-start gap-2 text-sm text-[var(--color-text)]">
                  <input
                    type="checkbox"
                    className="mt-1"
                    checked={opHistorical}
                    onChange={(e) => setOpHistorical(e.target.checked)}
                  />
                  <span>
                    Posición histórica
                    <span className="block text-xs text-[var(--color-text-muted)]">
                      Ya la tenías antes de usar TriVault: no se descuenta ni abona efectivo de la cuenta.
                    </span>
                  </span>
                </label>

                {selectedCash !== undefined && !opHistorical && (
                  <p className="num text-xs text-[var(--color-text-muted)]">
                    Efectivo disponible en {accountOf(selectedFund!.account_id)?.name}: {formatEUR(selectedCash)}
                  </p>
                )}

                <Button requiresNetwork type="submit" loading={savingOp} className="w-full">
                  {opType === 'buy' ? 'Registrar compra' : 'Registrar venta'}
                </Button>
              </form>
            )}

            <form onSubmit={createFund} className={`${card} space-y-4`}>
              <h2 className="text-lg font-semibold text-[var(--color-text)]">Nuevo fondo</h2>
              <Select
                label="Cuenta de inversión"
                required
                options={investmentAccounts.map((a) => ({ value: String(a.id), label: a.name }))}
                value={fundAccount}
                onChange={(e) => setFundAccount(e.target.value)}
              />
              <Input
                label="ISIN"
                className="num uppercase"
                required
                minLength={12}
                maxLength={12}
                placeholder="IE00B4L5Y983"
                value={isin}
                onChange={(e) => setIsin(e.target.value.toUpperCase())}
              />
              <Input
                label="Nombre"
                required
                maxLength={150}
                placeholder="iShares Core MSCI World"
                value={fundName}
                onChange={(e) => setFundName(e.target.value)}
              />
              <Button requiresNetwork type="submit" loading={savingFund} className="w-full">
                Añadir fondo
              </Button>
            </form>
          </section>
        </div>
      )}
    </Layout>
  )
}
