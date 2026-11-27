export type CategoryType = 'income' | 'expense'

export interface Category {
  id: number
  user_id: number
  name: string
  type: CategoryType
  is_fixed: boolean
  created_at: string
}

export interface CategoryCreate {
  name: string
  type: CategoryType
  is_fixed?: boolean
}

export interface CategoryUpdate {
  name?: string
  is_fixed?: boolean
}
