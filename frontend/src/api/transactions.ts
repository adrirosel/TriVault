import { api } from './client'
import type { Transaction, TransactionCreate, TransactionType, TransactionUpdate } from '@/types/transaction'

export interface TransactionFilters {
  account_id?: number
  date_from?: string
  date_to?: string
  type?: TransactionType
  category_id?: number
  limit?: number
  offset?: number
}

export const transactionsApi = {
  list: (filters: TransactionFilters = {}) => api.get<Transaction[]>('/transactions', { params: filters }),
  create: (data: TransactionCreate) => api.post<Transaction>('/transactions', data),
  update: (id: number, data: TransactionUpdate) =>
    api.patch<Transaction>(`/transactions/${id}`, data),
  remove: (id: number) => api.delete(`/transactions/${id}`),
}
