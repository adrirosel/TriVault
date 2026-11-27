import { api } from './client'
import type { Cashflow, FundsPerformance, Inflation, Summary } from '@/types/analytics'

/** Browser timezone so months start at local midnight (falls back to the API default). */
const tz = Intl.DateTimeFormat().resolvedOptions().timeZone

export const analyticsApi = {
  summary: () => api.get<Summary>('/analytics/summary'),
  cashflow: (months = 6) => api.get<Cashflow>('/analytics/cashflow', { params: { months, tz } }),
  inflation: () => api.get<Inflation>('/analytics/inflation'),
  funds: () => api.get<FundsPerformance>('/analytics/funds'),
}
