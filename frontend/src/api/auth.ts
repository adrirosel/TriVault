import { api } from './client'
import type { TokenResponse, User } from '@/types/auth'

export const authApi = {
  register: (email: string, password: string) =>
    api.post<User>('/auth/register', { email, password }),

  login: async (email: string, password: string): Promise<string> => {
    const { data } = await api.post<TokenResponse>('/auth/login', { email, password })
    localStorage.setItem('access_token', data.access_token)
    return data.access_token
  },

  me: () => api.get<User>('/auth/me'),

  patchMe: (annual_inflation_rate: string) =>
    api.patch<User>('/auth/me', { annual_inflation_rate }),

  logout: () => localStorage.removeItem('access_token'),
}
