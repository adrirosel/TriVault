export type BucketType = 'daily' | 'emergency' | 'investment'

export interface Account {
  id: number
  user_id: number
  name: string
  bucket_type: BucketType
  current_balance: string
  currency: string
  created_at: string
}

export interface AccountCreate {
  name: string
  bucket_type: BucketType
  initial_balance?: string
  currency?: string
}

export interface AccountUpdate {
  name?: string
  bucket_type?: BucketType
}
