import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Compass, UserPlus } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { ApiError } from '../api/client'
import FadeIn from '../components/ui/FadeIn'

export default function RegisterPage() {
  const { register, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    email: '',
    username: '',
    password: '',
    first_name: '',
    last_name: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (isAuthenticated) {
    navigate('/planner')
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(form)
      navigate('/planner')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const update = (field: string, value: string) => setForm((f) => ({ ...f, [field]: value }))

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12">
      <FadeIn className="w-full max-w-md">
        <div className="glass rounded-3xl shadow-card p-8 sm:p-10">
          <div className="text-center mb-8">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-sunset-500 to-sunset-600 flex items-center justify-center mx-auto mb-4 shadow-glow">
              <Compass className="w-7 h-7 text-white" />
            </div>
            <h1 className="font-display text-3xl font-bold text-brand-900">Join the adventure</h1>
            <p className="text-brand-600 mt-2">Create your free account to start planning</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="px-4 py-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
                {error}
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-brand-700 mb-1.5">First name</label>
                <input
                  value={form.first_name}
                  onChange={(e) => update('first_name', e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-brand-200 bg-white/80 focus:outline-none focus:ring-2 focus:ring-brand-400"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-brand-700 mb-1.5">Last name</label>
                <input
                  value={form.last_name}
                  onChange={(e) => update('last_name', e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-brand-200 bg-white/80 focus:outline-none focus:ring-2 focus:ring-brand-400"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-brand-700 mb-1.5">Email</label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => update('email', e.target.value)}
                required
                className="w-full px-4 py-3 rounded-xl border border-brand-200 bg-white/80 focus:outline-none focus:ring-2 focus:ring-brand-400"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-brand-700 mb-1.5">Username</label>
              <input
                value={form.username}
                onChange={(e) => update('username', e.target.value)}
                required
                minLength={3}
                className="w-full px-4 py-3 rounded-xl border border-brand-200 bg-white/80 focus:outline-none focus:ring-2 focus:ring-brand-400"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-brand-700 mb-1.5">Password</label>
              <input
                type="password"
                value={form.password}
                onChange={(e) => update('password', e.target.value)}
                required
                minLength={8}
                className="w-full px-4 py-3 rounded-xl border border-brand-200 bg-white/80 focus:outline-none focus:ring-2 focus:ring-brand-400"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3.5 bg-gradient-to-r from-sunset-500 to-sunset-600 text-white font-semibold rounded-xl hover:from-sunset-600 hover:to-brand-700 disabled:opacity-60 transition-all shadow-soft mt-2"
            >
              <UserPlus className="w-5 h-5" />
              {loading ? 'Creating account...' : 'Create account'}
            </button>
          </form>

          <p className="text-center text-sm text-brand-600 mt-6">
            Already have an account?{' '}
            <Link to="/login" className="font-semibold text-brand-700 hover:text-brand-900">
              Sign in
            </Link>
          </p>
        </div>
      </FadeIn>
    </div>
  )
}
