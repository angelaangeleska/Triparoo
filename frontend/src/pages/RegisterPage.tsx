import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Compass, UserPlus } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { useAuth } from '../context/AuthContext'
import { ApiError } from '../api/client'
import FadeIn from '../components/ui/FadeIn'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Label } from '../components/ui/Label'

const schema = z.object({
  first_name: z.string().optional(),
  last_name: z.string().optional(),
  email: z.string().email(),
  username: z.string().min(3, 'Username must be at least 3 characters'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
})

type FormValues = z.infer<typeof schema>

export default function RegisterPage() {
  const { register: registerUser, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [error, setError] = useState('')

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  if (isAuthenticated) {
    return <Navigate to="/planner" replace />
  }

  const onSubmit = handleSubmit(async (data) => {
    setError('')
    try {
      await registerUser(data)
      navigate('/planner')
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Registration failed'
      setError(message)
      toast.error(message)
    }
  })

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12">
      <FadeIn className="w-full max-w-md">
        <div className="glass dark:bg-brand-900/60 dark:border-brand-800 rounded-3xl shadow-card p-8 sm:p-10">
          <div className="text-center mb-8">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-sunset-500 to-sunset-600 flex items-center justify-center mx-auto mb-4 shadow-glow">
              <Compass className="w-7 h-7 text-white" />
            </div>
            <h1 className="font-display text-3xl font-bold text-brand-900 dark:text-white">
              {t('auth.joinTitle')}
            </h1>
            <p className="text-brand-600 dark:text-brand-300 mt-2">{t('auth.registerSubtitle')}</p>
          </div>

          <form onSubmit={onSubmit} className="space-y-4">
            {error && (
              <div className="px-4 py-3 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-300 text-sm">
                {error}
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="first_name">{t('auth.firstName')}</Label>
                <Input id="first_name" {...register('first_name')} />
              </div>
              <div>
                <Label htmlFor="last_name">{t('auth.lastName')}</Label>
                <Input id="last_name" {...register('last_name')} />
              </div>
            </div>

            <div>
              <Label htmlFor="email">{t('auth.email')}</Label>
              <Input id="email" type="email" error={!!errors.email} {...register('email')} />
            </div>

            <div>
              <Label htmlFor="username">{t('auth.username')}</Label>
              <Input id="username" error={!!errors.username} {...register('username')} />
              {errors.username && <p className="text-xs text-red-500 mt-1">{errors.username.message}</p>}
            </div>

            <div>
              <Label htmlFor="password">{t('auth.password')}</Label>
              <Input id="password" type="password" error={!!errors.password} {...register('password')} />
              {errors.password && <p className="text-xs text-red-500 mt-1">{errors.password.message}</p>}
            </div>

            <Button type="submit" variant="accent" size="lg" className="w-full mt-2" disabled={isSubmitting}>
              <UserPlus className="w-5 h-5" />
              {isSubmitting ? t('auth.creatingAccount') : t('auth.createAccount')}
            </Button>
          </form>

          <p className="text-center text-sm text-brand-600 dark:text-brand-300 mt-6">
            {t('auth.haveAccount')}{' '}
            <Link
              to="/login"
              className="font-semibold text-brand-700 dark:text-brand-200 hover:text-brand-900 dark:hover:text-white"
            >
              {t('auth.signIn')}
            </Link>
          </p>
        </div>
      </FadeIn>
    </div>
  )
}
