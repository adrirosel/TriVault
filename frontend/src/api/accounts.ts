import { api } from './client'
import type { Account, AccountCreate, AccountUpdate } from '@/types/account'

export const accountsApi = {
  list: () => api.get<Account[]>('/accounts'),
  get: (id: number) => api.get<Account>(`/accounts/${id}`),
  create: (data: AccountCreate) => api.post<Account>('/accounts', data),
  update: (id: number, data: AccountUpdate) => api.patch<Account>(`/accounts/${id}`, data),
  remove: (id: number) => api.delete(`/accounts/${id}`),
}
