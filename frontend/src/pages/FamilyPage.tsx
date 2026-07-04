import { Navigate } from 'react-router-dom'
import { Users } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import FamilyMemberEditor from '../components/family/FamilyMemberEditor'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import FadeIn from '../components/ui/FadeIn'

export default function FamilyPage() {
  const { isAuthenticated, loading: authLoading } = useAuth()

  if (authLoading) return <LoadingSpinner fullScreen message="Loading..." />
  if (!isAuthenticated) return <Navigate to="/login" replace />

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <FadeIn>
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-brand-500/10 text-brand-700 text-sm font-medium mb-4">
            <Users className="w-4 h-4" />
            Your family profile
          </div>
          <h1 className="font-display text-4xl sm:text-5xl font-bold text-brand-900 mb-3">
            Who is traveling?
          </h1>
          <p className="text-brand-600 text-lg max-w-xl mx-auto">
            Add everyone in your party. For kids under 18, pick their interests — we use this across
            trip planning and destination activity suggestions.
          </p>
        </div>
      </FadeIn>

      <FadeIn delay={0.1}>
        <div className="glass rounded-3xl shadow-card p-6 sm:p-8">
          <FamilyMemberEditor />
          <p className="mt-6 text-sm text-brand-500 text-center">
            Your family info is saved for this browser session and used on the planner and destination pages.
          </p>
        </div>
      </FadeIn>
    </div>
  )
}
