import type { ReactNode } from 'react'

export interface NavItem {
  to: string
  label: string
  icon: ReactNode
}

const iconProps = {
  width: 22,
  height: 22,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.8,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
  'aria-hidden': true,
}

/** Single source of truth for the desktop sidebar and the mobile bottom bar. */
export const NAV_LINKS: NavItem[] = [
  {
    to: '/',
    label: 'Dashboard',
    icon: (
      <svg {...iconProps}>
        <rect x="3" y="3" width="7" height="9" rx="1.5" />
        <rect x="14" y="3" width="7" height="5" rx="1.5" />
        <rect x="14" y="12" width="7" height="9" rx="1.5" />
        <rect x="3" y="16" width="7" height="5" rx="1.5" />
      </svg>
    ),
  },
  {
    to: '/cuentas',
    label: 'Cuentas',
    icon: (
      <svg {...iconProps}>
        <rect x="3" y="6" width="18" height="13" rx="2" />
        <path d="M3 10h18M16 15h2" />
      </svg>
    ),
  },
  {
    to: '/categorias',
    label: 'Categorías',
    icon: (
      <svg {...iconProps}>
        <path d="M4 7h10M4 12h16M4 17h7" />
      </svg>
    ),
  },
  {
    to: '/transacciones',
    label: 'Movimientos',
    icon: (
      <svg {...iconProps}>
        <path d="M7 4v16M7 20l-3-3M7 20l3-3M17 20V4M17 4l-3 3M17 4l3 3" />
      </svg>
    ),
  },
]
