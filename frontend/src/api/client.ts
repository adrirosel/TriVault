import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL ?? ''

export const api = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token from localStorage on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

// Auth endpoints answer 401 for bad credentials: let the form show the error instead of redirecting.
const AUTH_ENDPOINTS = ['/auth/login', '/auth/register']

// On 401 for an authenticated request (expired/invalid token), clear token and redirect to /login
api.interceptors.response.use(
  (res) => res,
  (error: unknown) => {
    const isAuthEndpoint =
      axios.isAxiosError(error) && AUTH_ENDPOINTS.some((path) => error.config?.url?.endsWith(path))
    if (axios.isAxiosError(error) && error.response?.status === 401 && !isAuthEndpoint) {
      localStorage.removeItem('access_token')
      window.location.replace('/login')
    }
    return Promise.reject(error)
  },
)
