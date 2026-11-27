import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import { Layout } from '@/components/layout/Layout'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { ErrorMessage } from '@/components/ui/ErrorMessage'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { accountsApi } from '@/api/accounts'
import { categoriesApi } from '@/api/categories'
import { transactionsApi } from '@/api/transactions'
import type { Account } from '@/types/account'
import type { Category } from '@/types/category'
import type {
  Transaction,
  TransactionCreate,
  TransactionType,
  TransactionUpdate,
} from '@/types/transaction'
import { apiErrorMessage, formatDate, formatEUR, nowISO, toLocalInputValue } from '@/utils/format'

const TYPE_OPTIONS = [
  { value: 'expense', label: 'Gasto' },
  { value: 'income', label: 'Ingreso' },
  { value: 'transfer', label: 'Transferencia' },
]

export function Transactions() {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [accounts, setAccounts] = useState<Account[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const [type, setType] = useState<TransactionType>('expense')
  const [accountId, setAccountId] = useState('')
  const [destinationId, setDestinationId] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [amount, setAmount] = useState('')
  const [description, setDescription] = useState('')
  const [date, setDate] = useState(nowISO())
  const [editingId, setEditingId] = useState<number | null>(null)

  const load = useCallback(async () => {
    try {
      const [txRes, accRes, catRes] = await Promise.all([
        transactionsApi.list(),
        accountsApi.list(),
        categoriesApi.list(),
      ])
      const sorted = [...txRes.data].sort(
        (a, b) => new Date(b.transaction_date).getTime() - new Date(a.transaction_date).getTime(),
      )
      setTransactions(sorted)
      setAccounts(accRes.data)
      setCategories(catRes.data)
      setAccountId((prev) => {
        if (prev && accRes.data.some((a) => String(a.id) === prev)) return prev
        return accRes.data[0] ? String(accRes.data[0].id) : ''
      })
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const accountOptions = useMemo(
    () => accounts.map((a) => ({ value: String(a.id), label: `${a.name} (${a.bucket_type})` })),
    [accounts],
  )

  const categoryOptions = useMemo(
    () =>
      categories
        .filter((c) => c.type === type)
        .map((c) => ({ value: String(c.id), label: c.name })),
    [categories, type],
  )

  const accountName = (id: number) => accounts.find((a) => a.id === id)?.name ?? `#${id}`
  const categoryName = (id: number | null) =>
    id == null ? '—' : (categories.find((c) => c.id === id)?.name ?? `#${id}`)

  const resetForm = () => {
    setEditingId(null)
    setType('expense')
    setDestinationId('')
    setCategoryId('')
    setAmount('')
    setDescription('')
    setDate(nowISO())
  }

  const startEdit = (tx: Transaction) => {
    setError('')
    setEditingId(tx.id)
    setType(tx.type)
    setAccountId(String(tx.account_id))
    setDestinationId(tx.destination_account_id != null ? String(tx.destination_account_id) : '')
    setCategoryId(tx.category_id != null ? String(tx.category_id) : '')
    setAmount(tx.amount)
    setDescription(tx.description ?? '')
    setDate(toLocalInputValue(tx.transaction_date))
  }

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setSaving(true)
    const isTransfer = type === 'transfer'
    try {
      if (editingId != null) {
        // Send every field explicitly so switching type clears the field that no longer applies.
        const update: TransactionUpdate = {
          account_id: Number(accountId),
          amount,
          type,
          transaction_date: new Date(date).toISOString(),
          description: description || null,
          destination_account_id: isTransfer ? Number(destinationId) : null,
          category_id: isTransfer ? null : Number(categoryId),
        }
        await transactionsApi.update(editingId, update)
      } else {
        const payload: TransactionCreate = {
          account_id: Number(accountId),
          amount,
          type,
          transaction_date: new Date(date).toISOString(),
          description: description || undefined,
        }
        if (isTransfer) {
          payload.destination_account_id = Number(destinationId)
        } else {
          payload.category_id = Number(categoryId)
        }
        await transactionsApi.create(payload)
      }
      resetForm()
      await load()
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const onDelete = async (id: number) => {
    if (!confirm('¿Eliminar este movimiento? Se revertirá el saldo.')) return
    setError('')
    try {
      await transactionsApi.remove(id)
      if (editingId === id) resetForm()
      await load()
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }

  return (
    <Layout title="Transacciones">
      <ErrorMessage message={error} />

      {loading ? (
        <p className="num text-sm text-[var(--color-text-muted)] animate-pulse">Cargando…</p>
      ) : (
        <div className="grid gap-8 lg:grid-cols-[7fr_5fr]">
          <section>
            {transactions.length === 0 ? (
              <p className="prose-narrow text-sm text-[var(--color-text-muted)] border border-[var(--color-border)] rounded-xl px-5 py-8">
                Sin movimientos este mes — registra el primero.
              </p>
            ) : (
              <div className="border border-[var(--color-border)] rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-[var(--color-base)] border-b border-[var(--color-border)]">
                    <tr className="text-left text-xs uppercase tracking-wide text-[var(--color-text-muted)]">
                      <th className="px-3 py-2 font-medium">Fecha</th>
                      <th className="px-3 py-2 font-medium">Tipo</th>
                      <th className="px-3 py-2 font-medium">Detalle</th>
                      <th className="px-3 py-2 font-medium text-right">Importe</th>
                      <th className="px-3 py-2 font-medium text-right"> </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--color-border)] bg-[var(--color-surface)]">
                    {transactions.map((tx) => (
                      <tr key={tx.id} className={editingId === tx.id ? 'bg-[var(--color-base)]' : undefined}>
                        <td className="px-3 py-2 num text-xs text-[var(--color-text-muted)] whitespace-nowrap">
                          {formatDate(tx.transaction_date)}
                        </td>
                        <td className="px-3 py-2">
                          <Badge variant={tx.type} />
                        </td>
                        <td className="px-3 py-2 min-w-0">
                          <p className="text-[var(--color-text)] truncate">
                            {tx.description ||
                              (tx.type === 'transfer'
                                ? `${accountName(tx.account_id)} → ${accountName(tx.destination_account_id!)}`
                                : categoryName(tx.category_id))}
                          </p>
                          <p className="num text-xs text-[var(--color-text-muted)]">
                            #{tx.id} · {accountName(tx.account_id)}
                          </p>
                        </td>
                        <td
                          className={[
                            'px-3 py-2 num text-right font-medium whitespace-nowrap',
                            tx.type === 'expense'
                              ? 'text-[var(--color-danger)]'
                              : tx.type === 'income'
                                ? 'text-[var(--color-success)]'
                                : 'text-[var(--color-text)]',
                          ].join(' ')}
                        >
                          {tx.type === 'expense' ? '−' : tx.type === 'income' ? '+' : ''}
                          {formatEUR(tx.amount)}
                        </td>
                        <td className="px-3 py-2 text-right whitespace-nowrap space-x-2">
                          <Button type="button" variant="ghost" onClick={() => startEdit(tx)}>
                            Editar
                          </Button>
                          <Button type="button" variant="danger" onClick={() => void onDelete(tx.id)}>
                            Eliminar
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section>
            <form
              onSubmit={onSubmit}
              className="border border-[var(--color-border)] rounded-xl p-5 bg-[var(--color-surface)] space-y-4"
            >
              <h2 className="text-lg font-semibold text-[var(--color-text)]">
                {editingId != null ? `Editar movimiento #${editingId}` : 'Nuevo movimiento'}
              </h2>

              <Select
                label="Tipo"
                options={TYPE_OPTIONS}
                value={type}
                onChange={(e) => {
                  setType(e.target.value as TransactionType)
                  setCategoryId('')
                  setDestinationId('')
                }}
              />

              <Select
                label={type === 'transfer' ? 'Cuenta origen' : 'Cuenta'}
                required
                options={[{ value: '', label: 'Selecciona…' }, ...accountOptions]}
                value={accountId}
                onChange={(e) => setAccountId(e.target.value)}
              />

              {type === 'transfer' ? (
                <Select
                  label="Cuenta destino"
                  required
                  options={[
                    { value: '', label: 'Selecciona…' },
                    ...accountOptions.filter((o) => o.value !== accountId),
                  ]}
                  value={destinationId}
                  onChange={(e) => setDestinationId(e.target.value)}
                />
              ) : (
                <Select
                  label="Categoría"
                  required
                  options={[{ value: '', label: 'Selecciona…' }, ...categoryOptions]}
                  value={categoryId}
                  onChange={(e) => setCategoryId(e.target.value)}
                />
              )}

              <Input
                label="Importe (EUR)"
                className="num"
                type="number"
                step="0.01"
                min="0.01"
                required
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
              />

              <Input
                label="Fecha"
                className="num"
                type="datetime-local"
                required
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />

              <Input
                label="Descripción"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Opcional"
              />

              <Button
                type="submit"
                loading={saving}
                className="w-full"
                disabled={accounts.length === 0 || (type !== 'transfer' && categories.length === 0)}
              >
                {editingId != null ? 'Guardar cambios' : 'Registrar'}
              </Button>

              {editingId != null && (
                <Button type="button" variant="ghost" className="w-full" onClick={resetForm}>
                  Cancelar edición
                </Button>
              )}

              {accounts.length === 0 && (
                <p className="text-xs text-[var(--color-text-muted)]">
                  Necesitas al menos una cuenta antes de registrar movimientos.
                </p>
              )}
              {type !== 'transfer' && categories.length === 0 && (
                <p className="text-xs text-[var(--color-text-muted)]">
                  Crea una categoría de {type === 'income' ? 'ingreso' : 'gasto'} primero.
                </p>
              )}
            </form>
          </section>
        </div>
      )}
    </Layout>
  )
}
