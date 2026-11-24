export type TransactionType = 'income' | 'expense' | 'transfer'

export interface Transaction {
  id: number
  user_id: number
  account_id: number
  destination_account_id: number | null
  category_id: number | null
  amount: string
  type: TransactionType
  description: string | null
  transaction_date: string
  import_hash: string | null
  created_at: string
}

export interface TransactionCreate {
  account_id: number
  amount: string
  type: TransactionType
  transaction_date: string
  category_id?: number
  destination_account_id?: number
  description?: string
}

export interface TransactionUpdate {
  description?: string
  transaction_date?: string
}
