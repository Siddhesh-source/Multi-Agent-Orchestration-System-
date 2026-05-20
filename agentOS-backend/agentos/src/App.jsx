import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import AppShell from './components/layout/AppShell'
import Dashboard from './pages/Dashboard'
import TaskView from './pages/TaskView'
import Memory from './pages/Memory'

// ─── React Query Client ───────────────────────────────────────────────
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5_000,
    },
  },
})

// ─── App ─────────────────────────────────────────────────────────────
// AppShell acts as a layout route — it renders Outlet internally with
// AnimatePresence so the sidebar never re-mounts on navigation.
export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<Dashboard />} />
            <Route path="task/:id" element={<TaskView />} />
            <Route path="memory" element={<Memory />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
