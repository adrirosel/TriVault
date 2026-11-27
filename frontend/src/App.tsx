import { Navigate, Route, Routes } from 'react-router-dom'
import { GuestRoute, ProtectedRoute } from '@/utils/guards'
import { Login } from '@/pages/Login'
import { Register } from '@/pages/Register'
import { Dashboard } from '@/pages/Dashboard'
import { Accounts } from '@/pages/Accounts'
import { Categories } from '@/pages/Categories'
import { Transactions } from '@/pages/Transactions'

export function App() {
  return (
    <Routes>
      <Route element={<GuestRoute />}>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/cuentas" element={<Accounts />} />
        <Route path="/categorias" element={<Categories />} />
        <Route path="/transacciones" element={<Transactions />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
