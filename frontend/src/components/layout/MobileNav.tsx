import { NavLink } from 'react-router-dom'
import { NAV_LINKS } from './navLinks'

/** Bottom tab bar shown below the md breakpoint (phones / installed PWA). */
export function MobileNav() {
  return (
    <nav
      aria-label="Navegación principal"
      className="md:hidden fixed inset-x-0 bottom-0 z-20 border-t border-[var(--color-border)] bg-[var(--color-surface)] pb-[env(safe-area-inset-bottom)]"
    >
      <ul className="grid grid-cols-4">
        {NAV_LINKS.map(({ to, label, icon }) => (
          <li key={to}>
            <NavLink
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                [
                  'flex flex-col items-center gap-0.5 py-2 text-[11px] font-medium',
                  'transition-colors duration-150',
                  isActive
                    ? 'text-[var(--color-accent)]'
                    : 'text-[var(--color-text-muted)] active:text-[var(--color-text)]',
                ].join(' ')
              }
            >
              {icon}
              <span>{label}</span>
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  )
}
