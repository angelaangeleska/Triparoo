import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Compass, Eye, EyeOff, LogIn } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { useAuth } from '../context/AuthContext'
import { ApiError } from '../api/client'
import FadeIn from '../components/ui/FadeIn'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Label } from '../components/ui/Label'

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
})

type FormValues = z.infer<typeof schema>

interface LocationState {
  from?: { pathname: string }
}

export default function LoginPage() {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const { t } = useTranslation()
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: 'demo@familytrip.com', password: 'DemoPass123!' },
  })

  const redirectTo = (location.state as LocationState)?.from?.pathname || '/planner'

  if (isAuthenticated) {
    return <Navigate to={redirectTo} replace />
  }

  const onSubmit = handleSubmit(async ({ email, password }) => {
    setError('')
    try {
      await login(email, password)
      navigate(redirectTo)
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Login failed'
      setError(message)
      toast.error(message)
    }
  })

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12">
      <FadeIn className="w-full max-w-md">
        <div className="glass dark:bg-brand-900/60 dark:border-brand-800 rounded-3xl shadow-card p-8 sm:p-10">
          <div className="text-center mb-8">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center mx-auto mb-4 shadow-glow">
              <Compass className="w-7 h-7 text-white" />
            </div>
            <h1 className="font-display text-3xl font-bold text-brand-900 dark:text-white">
              {t('auth.welcomeBack')}
            </h1>
            <p className="text-brand-600 dark:text-brand-300 mt-2">{t('auth.loginSubtitle')}</p>
          </div>

          <form onSubmit={onSubmit} className="space-y-5">
            {error && (
              <div className="px-4 py-3 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-300 text-sm">
                {error}
              </div>
            )}

            <div>
              <Label htmlFor="email">{t('auth.email')}</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                error={!!errors.email}
                {...register('email')}
              />
            </div>

            <div>
              <Label htmlFor="password">{t('auth.password')}</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  className="pr-12"
                  error={!!errors.password}
                  {...register('password')}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-brand-400 hover:text-brand-600 dark:hover:text-brand-200"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <Button type="submit" size="lg" className="w-full" disabled={isSubmitting}>
              <LogIn className="w-5 h-5" />
              {isSubmitting ? t('auth.signingIn') : t('auth.signIn')}
            </Button>
          </form>

          <p className="text-center text-sm text-brand-600 dark:text-brand-300 mt-6">
            {t('auth.noAccount')}{' '}
            <Link
              to="/register"
              className="font-semibold text-brand-700 dark:text-brand-200 hover:text-brand-900 dark:hover:text-white"
            >
              {t('auth.createOne')}
            </Link>
          </p>

          <div className="mt-6 p-4 rounded-xl bg-brand-50 dark:bg-brand-800/50 border border-brand-100 dark:border-brand-700">
            <p className="text-xs text-brand-600 dark:text-brand-300 text-center">
              <strong>{t('auth.demoNote')}</strong>
            </p>
          </div>
        </div>
      </FadeIn>
    </div>
  )
}
