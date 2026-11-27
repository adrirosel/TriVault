import type { ReactNode } from 'react'
import { Sidebar } from './Sidebar'

interface Props {
  children: ReactNode
  title?: string
  actions?: ReactNode
}

export function Layout({ children, title, actions }: Props) {
  return (
    <div className="flex h-screen overflow-hidden bg-[var(--color-base)]">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        {(title ?? actions) && (
          <header className="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-base)] px-8 py-4 flex items-center justify-between">
            {title && (
              <h1 className="text-2xl font-semibold tracking-tight text-[var(--color-text)]">
                {title}
              </h1>
            )}

            {actions && <div className="flex items-center gap-3">{actions}</div>}
          </header>
        )}
        <div className="px-8 py-6">{children}</div>
      </main>
    </div>
  )
}
