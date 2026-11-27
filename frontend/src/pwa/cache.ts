import { API_CACHE_NAME } from './constants'

/** Remove cached financial data from the device (called on logout so the next user never sees it). */
export async function clearApiCache(): Promise<void> {
  if (typeof caches === 'undefined') return
  await caches.delete(API_CACHE_NAME)
}
