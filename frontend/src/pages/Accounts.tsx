import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Layout } from '@/components/layout/Layout'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { ErrorMessage } from '@/components/ui/ErrorMessage'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { accountsApi } from '@/api/accounts'
import type { Account, AccountCreate, BucketType } from '@/types/account'
import { apiErrorMessage, formatEUR } from '@/utils/format'

const BUCKET_OPTIONS = [
  { value: 'daily', label: 'Diario' },
  { value: 'emergency', label: 'Emergencia' },
  { value: 'investment', label: 'Inversión' },
]

const emptyForm = {
  name: '',
  bucket_type: 'daily' as BucketType,
  initial_balance: '0.00',
}

export function Accounts() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [form, setForm] = useState(emptyForm)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    try {
      const { data } = await accountsApi.list()
      setAccounts(data)
      setSelectedId((prev) => {
        if (prev !== null && data.some((a) => a.id === prev)) return prev
        return data[0]?.id ?? null
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

  const selected = accounts.find((a) => a.id === selectedId) ?? null

  const resetForm = () => {
    setForm(emptyForm)
    setEditingId(null)
  }

  const startEdit = (account: Account) => {
    setEditingId(account.id)
    setSelectedId(account.id)
    setForm({
      name: account.name,
      bucket_type: account.bucket_type,
      initial_balance: account.current_balance,
    })
  }

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      if (editingId !== null) {
        await accountsApi.update(editingId, {
          name: form.name,
          bucket_type: form.bucket_type,
        })
      } else {
        const payload: AccountCreate = {
          name: form.name,
          bucket_type: form.bucket_type,
          initial_balance: form.initial_balance || '0.00',
        }
        const { data } = await accountsApi.create(payload)
        setSelectedId(data.id)
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
    if (!confirm('¿Eliminar esta cuenta? No se puede deshacer.')) return
    setError('')
    try {
      await accountsApi.remove(id)
      if (selectedId === id) setSelectedId(null)
      if (editingId === id) resetForm()
      await load()
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }

  return (
    <Layout
      title="Cuentas"
      actions={
        editingId !== null ? (
          <Button type="button" variant="ghost" onClick={resetForm}>
            Cancelar edición
          </Button>
        ) : undefined
      }
    >
      <ErrorMessage message={error} />

      {loading ? (
        <p className="num text-sm text-[var(--color-text-muted)] animate-pulse">Cargando…</p>
      ) : (
        <div className="grid grid-cols-[minmax(0,1fr)] gap-6 md:gap-8 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)]">
          <section>
            {accounts.length === 0 ? (
              <p className="prose-narrow text-sm text-[var(--color-text-muted)] border border-[var(--color-border)] rounded-xl px-5 py-8">
                No hay cuentas. Crea el cubo Diario, Emergencia o Inversión a la derecha.
              </p>
            ) : (
              <ul className="divide-y divide-[var(--color-border)] border border-[var(--color-border)] rounded-xl overflow-hidden">
                {accounts.map((account) => (
                  <li key={account.id}>
                    <button
                      type="button"
                      onClick={() => setSelectedId(account.id)}
                      className={[
                        'w-full flex items-center justify-between gap-4 px-4 py-3 text-left',
                        'bg-[var(--color-surface)] transition-opacity duration-150',
                        'hover:opacity-80 active:scale-[0.98]',
                        selectedId === account.id ? 'border-l-2 border-l-[var(--color-accent)]' : '',
                      ].join(' ')}
                    >
                      <div className="min-w-0 space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-medium text-[var(--color-text)] truncate">
                            {account.name}
                          </span>
                          <Badge variant={account.bucket_type} />
                        </div>
                        <span className="num text-xs text-[var(--color-text-muted)]">
                          #{account.id} · {account.currency}
                        </span>
                      </div>
                      <span className="num text-sm font-medium text-[var(--color-text)] shrink-0">
                        {formatEUR(account.current_balance)}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}

            {selected && (
              <div className="mt-6 border border-[var(--color-border)] rounded-xl p-5 bg-[var(--color-surface)] space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-semibold text-[var(--color-text)]">{selected.name}</h2>
                    <div className="mt-2 flex items-center gap-2">
                      <Badge variant={selected.bucket_type} />
                      <span className="num text-xs text-[var(--color-text-muted)]">#{selected.id}</span>
                    </div>
                  </div>
                  <p className="num text-2xl font-semibold text-[var(--color-text)]">
                    {formatEUR(selected.current_balance)}
                  </p>
                </div>
                <div className="flex gap-2 pt-2">
                  <Button requiresNetwork type="button" variant="ghost" onClick={() => startEdit(selected)}>
                    Editar
                  </Button>
                  <Button requiresNetwork type="button" variant="danger" onClick={() => void onDelete(selected.id)}>
                    Eliminar
                  </Button>
                </div>
              </div>
            )}
          </section>

          <section>
            <form
              onSubmit={onSubmit}
              className="border border-[var(--color-border)] rounded-xl p-5 bg-[var(--color-surface)] space-y-4"
            >
              <h2 className="text-lg font-semibold text-[var(--color-text)]">
                {editingId !== null ? 'Editar cuenta' : 'Nueva cuenta'}
              </h2>
              <Input
                label="Nombre"
                required
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="p. ej. Nómina"
              />
              <Select
                label="Cubo"
                required
                options={BUCKET_OPTIONS}
                value={form.bucket_type}
                onChange={(e) =>
                  setForm((f) => ({ ...f, bucket_type: e.target.value as BucketType }))
                }
              />
              {editingId === null && (
                <Input
                  label="Saldo inicial"
                  className="num"
                  type="number"
                  step="0.01"
                  min="0"
                  value={form.initial_balance}
                  onChange={(e) => setForm((f) => ({ ...f, initial_balance: e.target.value }))}
                />
              )}
              <Button requiresNetwork type="submit" loading={saving} className="w-full">
                {editingId !== null ? 'Guardar cambios' : 'Crear cuenta'}
              </Button>
            </form>
          </section>
        </div>
      )}
    </Layout>
  )
}
