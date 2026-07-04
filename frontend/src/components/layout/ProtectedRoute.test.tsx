import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './ProtectedRoute'

const mockUseAuth = vi.fn()
vi.mock('../../context/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}))

function renderProtected() {
  return render(
    <MemoryRouter initialEntries={['/planner']}>
      <Routes>
        <Route path="/login" element={<div>Login Page</div>} />
        <Route element={<ProtectedRoute />}>
          <Route path="/planner" element={<div>Planner Page</div>} />
        </Route>
      </Routes>
    </MemoryRouter>
  )
}

describe('ProtectedRoute', () => {
  it('shows a loading state while auth status is still resolving', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false, loading: true })
    renderProtected()
    expect(screen.queryByText('Planner Page')).not.toBeInTheDocument()
    expect(screen.queryByText('Login Page')).not.toBeInTheDocument()
  })

  it('redirects an unauthenticated visitor to /login instead of the protected page', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false, loading: false })
    renderProtected()
    expect(screen.getByText('Login Page')).toBeInTheDocument()
    expect(screen.queryByText('Planner Page')).not.toBeInTheDocument()
  })

  it('renders the protected page for an authenticated visitor', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true, loading: false })
    renderProtected()
    expect(screen.getByText('Planner Page')).toBeInTheDocument()
  })
})
