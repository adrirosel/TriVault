import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { ErrorMessage } from '@/components/ui/ErrorMessage'
import { apiErrorMessage } from '@/utils/format'

export function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/', { replace: true })
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-dvh grid lg:grid-cols-[5fr_7fr] bg-[var(--color-base)]">
      <section className="flex flex-col justify-center px-8 py-16 lg:px-16 border-b lg:border-b-0 lg:border-r border-[var(--color-border)]">
        <h1 className="heading-xl text-[var(--color-text)] mb-4">
          Tri<span className="text-[var(--color-accent)]">Vault</span>
        </h1>
        <p className="prose-narrow text-[var(--color-text-muted)] text-[1rem] leading-relaxed">
          Controla tus tres cubos: liquidez diaria, colchón de emergencia e inversión en un solo sitio.
        </p>
      </section>

      <section className="flex flex-col justify-center px-8 py-16 lg:px-24">
        <form onSubmit={onSubmit} className="w-full max-w-sm space-y-4">
          <h2 className="text-xl font-semibold text-[var(--color-text)] mb-2">Entrar</h2>
          <ErrorMessage message={error} />
          <Input
            label="Email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Input
            label="Contraseña"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Button requiresNetwork type="submit" loading={loading} className="w-full">
            Entrar
          </Button>
          <p className="text-sm text-[var(--color-text-muted)]">
            ¿Sin cuenta?{' '}
            <Link
              to="/register"
              className="text-[var(--color-accent)] hover:opacity-80 transition-opacity duration-150"
            >
              Crear cuenta
            </Link>
          </p>
        </form>
      </section>
    </div>
  )
}
