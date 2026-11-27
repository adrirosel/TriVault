import { useOnlineStatus } from '@/hooks/useOnlineStatus'

export function OfflineBanner() {
  const online = useOnlineStatus()
  if (online) return null
  return (
    <div
      role="status"
      className="sticky top-0 z-30 bg-[var(--color-warn-bg)] text-[var(--color-warn)] border-b border-[var(--color-border)] px-4 md:px-8 py-2 text-xs font-medium"
    >
      Sin conexión — mostrando los últimos datos guardados. Los cambios se podrán hacer al recuperar la conexión.
    </div>
  )
}
