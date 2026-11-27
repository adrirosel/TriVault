import { api } from './client'
import type { Transaction, TransactionCreate, TransactionUpdate } from '@/types/transaction'

export const transactionsApi = {
  list: (accountId?: number) =>
    api.get<Transaction[]>('/transactions', { params: accountId ? { account_id: accountId } : {} }),
  create: (data: TransactionCreate) => api.post<Transaction>('/transactions', data),
  update: (id: number, data: TransactionUpdate) =>
    api.patch<Transaction>(`/transactions/${id}`, data),
  remove: (id: number) => api.delete(`/transactions/${id}`),
}
