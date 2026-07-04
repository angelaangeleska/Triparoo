import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthProvider, useAuth } from './AuthContext'
import { api } from '../api/client'

vi.mock('../api/client', () => ({
  api: {
    me: vi.fn(),
    login: vi.fn(),
    register: vi.fn(),
  },
}))

function TestConsumer() {
  const { user, isAuthenticated, login, logout } = useAuth()
  return (
    <div>
      <span data-testid="status">{isAuthenticated ? 'in' : 'out'}</span>
      <span data-testid="user">{user?.username ?? 'none'}</span>
      <button onClick={() => login('demo@familytrip.com', 'DemoPass123!')}>login</button>
      <button onClick={logout}>logout</button>
    </div>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('starts logged out when no token is stored', async () => {
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    )
    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('out'))
    expect(api.me).not.toHaveBeenCalled()
  })

  it('restores the session from a stored token on mount', async () => {
    localStorage.setItem('access_token', 'existing-token')
    vi.mocked(api.me).mockResolvedValue({
      id: 1,
      email: 'demo@familytrip.com',
      username: 'demo',
      is_active: true,
      created_at: '2024-01-01',
    })

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    )

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('in'))
    expect(screen.getByTestId('user')).toHaveTextContent('demo')
  })

  it('clears an invalid stored token instead of leaving the user stuck logged out silently', async () => {
    localStorage.setItem('access_token', 'stale-token')
    localStorage.setItem('refresh_token', 'stale-refresh')
    vi.mocked(api.me).mockRejectedValue(new Error('401'))

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    )

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('out'))
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(localStorage.getItem('refresh_token')).toBeNull()
  })

  it('logs in, stores tokens, and exposes the user', async () => {
    vi.mocked(api.login).mockResolvedValue({
      access_token: 'new-access',
      refresh_token: 'new-refresh',
    })
    vi.mocked(api.me).mockResolvedValue({
      id: 1,
      email: 'demo@familytrip.com',
      username: 'demo',
      is_active: true,
      created_at: '2024-01-01',
    })

    const user = userEvent.setup()
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    )
    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('out'))

    await user.click(screen.getByText('login'))

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('in'))
    expect(localStorage.getItem('access_token')).toBe('new-access')
    expect(localStorage.getItem('refresh_token')).toBe('new-refresh')
  })

  it('logs out and clears stored tokens', async () => {
    localStorage.setItem('access_token', 'existing-token')
    vi.mocked(api.me).mockResolvedValue({
      id: 1,
      email: 'demo@familytrip.com',
      username: 'demo',
      is_active: true,
      created_at: '2024-01-01',
    })

    const user = userEvent.setup()
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    )
    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('in'))

    await user.click(screen.getByText('logout'))

    expect(screen.getByTestId('status')).toHaveTextContent('out')
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(localStorage.getItem('refresh_token')).toBeNull()
  })
})
