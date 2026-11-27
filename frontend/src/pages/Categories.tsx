import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import { Layout } from '@/components/layout/Layout'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { ErrorMessage } from '@/components/ui/ErrorMessage'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { categoriesApi } from '@/api/categories'
import type { Category, CategoryType } from '@/types/category'
import { apiErrorMessage } from '@/utils/format'

type Filter = 'all' | CategoryType

const TYPE_OPTIONS = [
  { value: 'expense', label: 'Gasto' },
  { value: 'income', label: 'Ingreso' },
]

const FIXED_OPTIONS = [
  { value: 'false', label: 'Variable' },
  { value: 'true', label: 'Fijo' },
]

export function Categories() {
  const [categories, setCategories] = useState<Category[]>([])
  const [filter, setFilter] = useState<Filter>('all')
  const [name, setName] = useState('')
  const [type, setType] = useState<CategoryType>('expense')
  const [isFixed, setIsFixed] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    try {
      const { data } = await categoriesApi.list()
      setCategories(data)
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const filtered = useMemo(
    () => (filter === 'all' ? categories : categories.filter((c) => c.type === filter)),
    [categories, filter],
  )

  const resetForm = () => {
    setName('')
    setType('expense')
    setIsFixed(false)
    setEditingId(null)
  }

  const startEdit = (cat: Category) => {
    setEditingId(cat.id)
    setName(cat.name)
    setType(cat.type)
    setIsFixed(cat.is_fixed)
  }

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      if (editingId !== null) {
        await categoriesApi.update(editingId, { name, is_fixed: isFixed })
      } else {
        await categoriesApi.create({ name, type, is_fixed: isFixed })
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
    if (!confirm('¿Eliminar esta categoría?')) return
    setError('')
    try {
      await categoriesApi.remove(id)
      if (editingId === id) resetForm()
      await load()
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }

  return (
    <Layout title="Categorías">
      <ErrorMessage message={error} />

      {loading ? (
        <p className="num text-sm text-[var(--color-text-muted)] animate-pulse">Cargando…</p>
      ) : (
        <div className="grid gap-8 lg:grid-cols-[7fr_5fr]">
          <section className="space-y-4">
            <div className="flex gap-2 flex-wrap">
              {(
                [
                  ['all', 'Todas'],
                  ['income', 'Ingresos'],
                  ['expense', 'Gastos'],
                ] as const
              ).map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setFilter(value)}
                  className={[
                    'rounded-lg border px-3 py-1.5 text-xs font-medium',
                    'transition-all duration-150 ease-out active:scale-[0.98]',
                    filter === value
                      ? 'border-[var(--color-accent)] text-[var(--color-accent)] bg-[var(--color-accent-light)]'
                      : 'border-[var(--color-border)] text-[var(--color-text-muted)] hover:border-[var(--color-text-muted)]',
                  ].join(' ')}
                >
                  {label}
                </button>
              ))}
            </div>

            {filtered.length === 0 ? (
              <p className="prose-narrow text-sm text-[var(--color-text-muted)] border border-[var(--color-border)] rounded-xl px-5 py-8">
                No hay categorías en este filtro. Crea una a la derecha.
              </p>
            ) : (
              <div className="border border-[var(--color-border)] rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-[var(--color-base)] border-b border-[var(--color-border)]">
                    <tr className="text-left text-xs uppercase tracking-wide text-[var(--color-text-muted)]">
                      <th className="px-4 py-3 font-medium">Nombre</th>
                      <th className="px-4 py-3 font-medium">Tipo</th>
                      <th className="px-4 py-3 font-medium">Naturaleza</th>
                      <th className="px-4 py-3 font-medium text-right">Acciones</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--color-border)] bg-[var(--color-surface)]">
                    {filtered.map((cat) => (
                      <tr key={cat.id}>
                        <td className="px-4 py-3 text-[var(--color-text)]">
                          {cat.name}{' '}
                          <span className="num text-xs text-[var(--color-text-muted)]">#{cat.id}</span>
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant={cat.type} />
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant={cat.is_fixed ? 'fixed' : 'variable'} />
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex justify-end gap-2">
                            <Button type="button" variant="ghost" onClick={() => startEdit(cat)}>
                              Editar
                            </Button>
                            <Button
                              type="button"
                              variant="danger"
                              onClick={() => void onDelete(cat.id)}
                            >
                              Eliminar
                            </Button>
                          </div>
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
                {editingId !== null ? 'Editar categoría' : 'Nueva categoría'}
              </h2>
              <Input
                label="Nombre"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="p. ej. Supermercado"
              />
              <Select
                label="Tipo"
                required
                options={TYPE_OPTIONS}
                value={type}
                disabled={editingId !== null}
                onChange={(e) => setType(e.target.value as CategoryType)}
              />
              <Select
                label="Naturaleza"
                options={FIXED_OPTIONS}
                value={String(isFixed)}
                onChange={(e) => setIsFixed(e.target.value === 'true')}
              />
              <div className="flex gap-2">
                {editingId !== null && (
                  <Button type="button" variant="ghost" onClick={resetForm} className="flex-1">
                    Cancelar
                  </Button>
                )}
                <Button type="submit" loading={saving} className="flex-1">
                  {editingId !== null ? 'Guardar' : 'Crear categoría'}
                </Button>
              </div>
            </form>
          </section>
        </div>
      )}
    </Layout>
  )
}
