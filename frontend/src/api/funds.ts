import { api } from './client'
import type {
  FundContribution,
  FundContributionCreate,
  FundPosition,
  FundPositionCreate,
  FundPositionUpdate,
} from '@/types/fund'

export const fundsApi = {
  list: () => api.get<FundPosition[]>('/funds'),
  create: (data: FundPositionCreate) => api.post<FundPosition>('/funds', data),
  update: (id: number, data: FundPositionUpdate) => api.patch<FundPosition>(`/funds/${id}`, data),
  remove: (id: number) => api.delete(`/funds/${id}`),
  contributions: (id: number) => api.get<FundContribution[]>(`/funds/${id}/contributions`),
  addContribution: (id: number, data: FundContributionCreate) =>
    api.post<FundContribution>(`/funds/${id}/contributions`, data),
  removeContribution: (id: number, contributionId: number) =>
    api.delete(`/funds/${id}/contributions/${contributionId}`),
}
