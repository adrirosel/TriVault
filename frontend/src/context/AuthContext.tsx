import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'
import { authApi } from '@/api/auth'
import type { User } from '@/types/auth'

interface AuthState {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    try {
      const { data } = await authApi.me()
      setUser(data)
    } catch {
      setUser(null)
    }
  }, [])

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      refreshUser().finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [refreshUser])

  const login = async (email: string, password: string) => {
    await authApi.login(email, password)
    await refreshUser()
  }

  const register = async (email: string, password: string) => {
    await authApi.register(email, password)
    await authApi.login(email, password)
    await refreshUser()
  }

  const logout = () => {
    authApi.logout()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
