export interface User {
  id: number
  email: string
  annual_inflation_rate: string
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}
