export type OrderType = 'buy' | 'sell'

export interface FundPosition {
  id: number
  account_id: number
  isin: string
  fund_name: string
  shares: string
  total_invested: string
  current_nav: string
  last_updated: string
  market_value: string
}

export interface FundPositionCreate {
  account_id: number
  isin: string
  fund_name: string
  current_nav?: string
}

export interface FundPositionUpdate {
  fund_name?: string
  current_nav?: string
}

export interface FundContribution {
  id: number
  fund_position_id: number
  operation_date: string
  order_type: OrderType
  shares: string
  purchase_nav: string
  gross_amount: string
  fee: string
  notes: string | null
  affects_cash: boolean
  created_at: string
}

export interface FundContributionCreate {
  operation_date: string
  order_type: OrderType
  shares: string
  purchase_nav: string
  gross_amount: string
  fee?: string
  notes?: string
  affects_cash: boolean
}
