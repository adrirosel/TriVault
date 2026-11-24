import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'

const links = [
  { to: '/',             label: 'Dashboard' },
  { to: '/cuentas',      label: 'Cuentas' },
  { to: '/categorias',   label: 'Categorías' },
  { to: '/transacciones',label: 'Transacciones' },
]

export function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className="flex h-screen w-56 shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)]">
      {/* Brand */}
      <div className="border-b border-[var(--color-border)] px-5 py-4">
        <span className="text-lg font-semibold tracking-tight text-[var(--color-text)]">
          Tri<span className="text-[var(--color-accent)]">Vault</span>
        </span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {links.map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              [
                'flex items-center rounded-lg px-3 py-2 text-sm font-medium',
                'transition-all duration-150 ease-out',
                isActive
                  ? 'bg-[var(--color-accent-light)] text-[var(--color-accent)] border border-[var(--color-accent)]/20'
                  : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-base)]',
              ].join(' ')
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>

      {/* User + logout */}
      <div className="border-t border-[var(--color-border)] px-4 py-4 space-y-1">
        <p className="num text-xs text-[var(--color-text-muted)] truncate">{user?.email}</p>
        <button
          onClick={handleLogout}
          className="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-danger)] transition-colors duration-150"
        >
          Cerrar sesión
        </button>
      </div>
    </aside>
  )
}
