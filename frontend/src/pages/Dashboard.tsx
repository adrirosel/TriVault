import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Layout } from '@/components/layout/Layout'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { ErrorMessage } from '@/components/ui/ErrorMessage'
import { accountsApi } from '@/api/accounts'
import { transactionsApi } from '@/api/transactions'
import type { Account, BucketType } from '@/types/account'
import type { Transaction } from '@/types/transaction'
import { apiErrorMessage, formatDate, formatEUR } from '@/utils/format'

const BUCKET_ORDER: BucketType[] = ['daily', 'emergency', 'investment']

function sumBalances(accounts: Account[], bucket?: BucketType): number {
  return accounts
    .filter((a) => (bucket ? a.bucket_type === bucket : true))
    .reduce((acc, a) => acc + parseFloat(a.current_balance), 0)
}

export function Dashboard() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const [accRes, txRes] = await Promise.all([accountsApi.list(), transactionsApi.list()])
        if (cancelled) return
        setAccounts(accRes.data)
        const sorted = [...txRes.data].sort(
          (a, b) => new Date(b.transaction_date).getTime() - new Date(a.transaction_date).getTime(),
        )
        setTransactions(sorted.slice(0, 8))
      } catch (err) {
        if (!cancelled) setError(apiErrorMessage(err))
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const netWorth = sumBalances(accounts)
  const accountName = (id: number) => accounts.find((a) => a.id === id)?.name ?? `#${id}`

  return (
    <Layout
      title="Dashboard"
      actions={
        <>
          <Link to="/cuentas">
            <Button type="button" variant="ghost">
              Ver cuentas
            </Button>
          </Link>
          <Link to="/transacciones">
            <Button type="button">Registrar movimiento</Button>
          </Link>
        </>
      }
    >
      <ErrorMessage message={error} />

      {loading ? (
        <p className="num text-sm text-[var(--color-text-muted)] animate-pulse">Cargando…</p>
      ) : (
        <div className="grid gap-8 lg:grid-cols-[5fr_7fr]">
          <section className="space-y-6">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-text-muted)] mb-2">
                Patrimonio neto
              </p>
              <p className="num heading-xl text-[var(--color-text)]">{formatEUR(netWorth)}</p>
            </div>

            <ul className="space-y-3">
              {BUCKET_ORDER.map((bucket) => {
                const total = sumBalances(accounts, bucket)
                const count = accounts.filter((a) => a.bucket_type === bucket).length
                return (
                  <li
                    key={bucket}
                    className="flex items-center justify-between border-b border-[var(--color-border)] pb-3"
                  >
                    <div className="flex items-center gap-2">
                      <Badge variant={bucket} />
                      <span className="num text-xs text-[var(--color-text-muted)]">
                        {count} {count === 1 ? 'cuenta' : 'cuentas'}
                      </span>
                    </div>
                    <span className="num text-sm font-medium text-[var(--color-text)]">
                      {formatEUR(total)}
                    </span>
                  </li>
                )
              })}
            </ul>

            {accounts.length === 0 && (
              <p className="prose-narrow text-sm text-[var(--color-text-muted)]">
                Aún no tienes cuentas. Crea los cubos Diario, Emergencia e Inversión para empezar.
              </p>
            )}
          </section>

          <section>
            <div className="flex items-baseline justify-between mb-4">
              <h2 className="text-lg font-semibold text-[var(--color-text)]">Movimientos recientes</h2>
              <Link
                to="/transacciones"
                className="text-xs text-[var(--color-accent)] hover:opacity-80 transition-opacity duration-150"
              >
                Ver todos
              </Link>
            </div>

            {transactions.length === 0 ? (
              <p className="prose-narrow text-sm text-[var(--color-text-muted)] border border-[var(--color-border)] rounded-xl px-5 py-8">
                Sin movimientos este mes — registra el primero.
              </p>
            ) : (
              <ul className="divide-y divide-[var(--color-border)] border border-[var(--color-border)] rounded-xl overflow-hidden">
                {transactions.map((tx) => (
                  <li
                    key={tx.id}
                    className="flex items-center justify-between gap-4 px-4 py-3 bg-[var(--color-surface)]"
                  >
                    <div className="min-w-0 space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant={tx.type} />
                        <span className="num text-xs text-[var(--color-text-muted)]">
                          {formatDate(tx.transaction_date)}
                        </span>
                      </div>
                      <p className="text-sm text-[var(--color-text)] truncate">
                        {tx.description || accountName(tx.account_id)}
                        {tx.type === 'transfer' && tx.destination_account_id
                          ? ` → ${accountName(tx.destination_account_id)}`
                          : ''}
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
          </section>
        </div>
      )}
    </Layout>
  )
}
