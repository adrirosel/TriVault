import type { BucketType } from './account'
import type { CategoryType } from './category'

export interface BucketTotal {
  bucket_type: BucketType
  total: string
  cash: string
  funds_value: string
  accounts: number
}

export interface Summary {
  net_worth: string
  buckets: BucketTotal[]
}

export interface CategoryTotal {
  category_id: number
  name: string
  type: CategoryType
  is_fixed: boolean
  total: string
}

export interface MonthTotal {
  month: string
  income: string
  expense: string
  net: string
}

export interface Cashflow {
  date_from: string
  date_to: string
  timezone: string
  income: string
  expense: string
  net: string
  savings_rate: string | null
  fixed_expense: string
  variable_expense: string
  by_category: CategoryTotal[]
  monthly: MonthTotal[]
}

export interface Inflation {
  annual_inflation_rate: string
  liquid_balance: string
  annual_loss: string
  monthly_loss: string
}

export interface FundPerformance {
  position_id: number
  isin: string
  fund_name: string
  shares: string
  current_nav: string
  market_value: string
  invested: string
  nominal_gain: string
  nominal_return_pct: string | null
  inflation_adjusted_cost: string
  accumulated_inflation_pct: string | null
  real_gain: string
  real_return_pct: string | null
  beats_inflation: boolean | null
  first_operation: string | null
}

export interface FundsPerformance {
  annual_inflation_rate: string
  positions: FundPerformance[]
  market_value: string
  invested: string
  nominal_gain: string
  nominal_return_pct: string | null
  inflation_adjusted_cost: string
  real_gain: string
  real_return_pct: string | null
  beats_inflation: boolean | null
}
