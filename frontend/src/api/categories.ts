import { api } from './client'
import type { Category, CategoryCreate, CategoryUpdate } from '@/types/category'

export const categoriesApi = {
  list: () => api.get<Category[]>('/categories'),
  create: (data: CategoryCreate) => api.post<Category>('/categories', data),
  update: (id: number, data: CategoryUpdate) => api.patch<Category>(`/categories/${id}`, data),
  remove: (id: number) => api.delete(`/categories/${id}`),
}
