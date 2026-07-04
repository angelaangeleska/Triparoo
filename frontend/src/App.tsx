import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { AuthProvider } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import Layout from './components/layout/Layout'
import ProtectedRoute from './components/layout/ProtectedRoute'
import ErrorBoundary from './components/ui/ErrorBoundary'
import LoadingSpinner from './components/ui/LoadingSpinner'

const HomePage = lazy(() => import('./pages/HomePage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))
const PlannerPage = lazy(() => import('./pages/PlannerPage'))
const FamilyPage = lazy(() => import('./pages/FamilyPage'))
const MyTripsPage = lazy(() => import('./pages/MyTripsPage'))
const DestinationsPage = lazy(() => import('./pages/DestinationsPage'))
const DestinationDetailPage = lazy(() => import('./pages/DestinationDetailPage'))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <BrowserRouter>
          <AuthProvider>
            <ErrorBoundary>
              <Suspense fallback={<LoadingSpinner fullScreen />}>
                <Routes>
                  <Route element={<Layout />}>
                    <Route path="/" element={<HomePage />} />
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/register" element={<RegisterPage />} />
                    <Route path="/destinations" element={<DestinationsPage />} />
                    <Route path="/destinations/:id" element={<DestinationDetailPage />} />
                    <Route element={<ProtectedRoute />}>
                      <Route path="/planner" element={<PlannerPage />} />
                      <Route path="/family" element={<FamilyPage />} />
                      <Route path="/trips" element={<MyTripsPage />} />
                    </Route>
                    <Route path="*" element={<Navigate to="/" replace />} />
                  </Route>
                </Routes>
              </Suspense>
              <Toaster richColors position="top-center" />
            </ErrorBoundary>
          </AuthProvider>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
