import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { MobileNav } from './MobileNav'
import { OfflineBanner } from './OfflineBanner'
import { Sidebar } from './Sidebar'

interface Props {
  children: ReactNode
  title?: string
  actions?: ReactNode
}

export function Layout({ children, title, actions }: Props) {
  const { logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="flex h-[100dvh] overflow-hidden bg-[var(--color-base)]">
      <Sidebar />
      <main className="flex-1 overflow-y-auto pb-[calc(4.5rem+env(safe-area-inset-bottom))] md:pb-0">
        <OfflineBanner />

        {/* Mobile brand bar (sidebar is hidden below md) */}
        <div className="md:hidden flex items-center justify-between px-4 pt-[calc(0.75rem+env(safe-area-inset-top))] pb-1">
          <span className="text-[1rem] font-semibold tracking-tight text-[var(--color-text)]">
            Tri<span className="text-[var(--color-accent)]">Vault</span>
          </span>
          <button
            onClick={() => void handleLogout()}
            className="text-xs text-[var(--color-text-muted)] active:text-[var(--color-danger)]"
          >
            Cerrar sesión
          </button>
        </div>

        {(title ?? actions) && (
          <header className="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-base)] px-4 md:px-8 py-3 md:py-4 flex flex-wrap items-center justify-between gap-3">
            {title && (
              <h1 className="text-xl md:text-2xl font-semibold tracking-tight text-[var(--color-text)]">
                {title}
              </h1>
            )}

            {actions && <div className="flex items-center gap-2 md:gap-3">{actions}</div>}
          </header>
        )}
        <div className="px-4 md:px-8 py-4 md:py-6">{children}</div>
      </main>
      <MobileNav />
    </div>
  )
}
