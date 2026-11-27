import { useRegisterSW } from 'virtual:pwa-register/react'
import { Button } from '@/components/ui/Button'

/** Shows a toast when a new version of the app has been downloaded by the service worker. */
export function UpdatePrompt() {
  const {
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW()

  if (!needRefresh) return null

  return (
    <div
      role="alert"
      className="fixed inset-x-4 bottom-[calc(5rem+env(safe-area-inset-bottom))] md:bottom-6 md:left-auto md:right-6 md:w-80 z-40 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-lg space-y-3"
    >
      <p className="text-sm text-[var(--color-text)]">Hay una nueva versión de TriVault disponible.</p>
      <div className="flex gap-2">
        <Button type="button" className="flex-1" onClick={() => void updateServiceWorker(true)}>
          Recargar
        </Button>
        <Button type="button" variant="ghost" onClick={() => setNeedRefresh(false)}>
          Más tarde
        </Button>
      </div>
    </div>
  )
}
