import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'

export function ProtectedRoute() {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <span className="num text-sm text-[var(--color-text-muted)] animate-pulse">
          Cargando…
        </span>
      </div>
    )
  }
  return user ? <Outlet /> : <Navigate to="/login" replace />
}

export function GuestRoute() {
  const { user, loading } = useAuth()
  if (loading) return null
  return user ? <Navigate to="/" replace /> : <Outlet />
}
