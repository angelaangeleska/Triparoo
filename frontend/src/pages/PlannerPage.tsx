import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import {
  Calendar,
  Euro,
  Pencil,
  Plane,
  RefreshCw,
  Search,
  Sparkles,
  Users,
} from 'lucide-react'
import { api, ApiError } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { isKid, useFamily } from '../context/FamilyContext'
import type { DestinationRecommendation } from '../types'
import { MONTHS } from '../types'
import RecommendationCard from '../components/planner/RecommendationCard'
import OriginLocationInput from '../components/planner/OriginLocationInput'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import FadeIn from '../components/ui/FadeIn'
import NumericInput from '../components/ui/NumericInput'

export default function PlannerPage() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const { members, kids } = useFamily()

  const [budget, setBudget] = useState(1500)
  const [preferredMonth, setPreferredMonth] = useState(8)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [originLocation, setOriginLocation] = useState('Sofia, Bulgaria')
  const [recommendations, setRecommendations] = useState<DestinationRecommendation[]>([])
  const [originMessage, setOriginMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [searched, setSearched] = useState(false)
  const [regenerateCount, setRegenerateCount] = useState(0)

  const handleSearch = async (isRegenerate = false) => {
    setError('')
    setLoading(true)
    setSearched(true)
    const nextRegenerateCount = isRegenerate ? regenerateCount + 1 : 0
    try {
      const res = await api.recommend({
        members,
        budget,
        preferred_month: preferredMonth,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        origin_location: originLocation.trim() || undefined,
        regenerate_count: nextRegenerateCount,
      })
      setRecommendations(res.recommendations.filter((r) => r.estimated_total_cost <= budget))
      setOriginMessage(res.origin_message || '')
      setRegenerateCount(nextRegenerateCount)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Search failed')
    } finally {
      setLoading(false)
    }
  }

  if (authLoading) return <LoadingSpinner fullScreen message="Loading..." />
  if (!isAuthenticated) return <Navigate to="/login" replace />

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <FadeIn>
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-brand-500/10 text-brand-700 text-sm font-medium mb-4">
            <Sparkles className="w-4 h-4" />
            AI-Powered Recommendations
          </div>
          <h1 className="font-display text-4xl sm:text-5xl font-bold text-brand-900 mb-3">
            Plan your family trip
          </h1>
          <p className="text-brand-600 text-lg max-w-xl mx-auto">
            Set your budget and travel dates — we&apos;ll rank destinations using your saved family profile.
          </p>
        </div>
      </FadeIn>

      <FadeIn delay={0.1}>
        <div className="glass rounded-3xl shadow-card p-6 sm:p-8 mb-10">
          <div className="mb-8 p-4 rounded-2xl bg-white/60 border border-brand-100">
            <div className="flex items-start justify-between gap-4 mb-3">
              <h2 className="font-semibold text-brand-900 flex items-center gap-2">
                <Users className="w-5 h-5 text-brand-500" />
                Your family
              </h2>
              <Link
                to="/family"
                className="flex items-center gap-1.5 text-sm font-medium text-brand-600 hover:text-brand-800 px-3 py-1.5 rounded-lg hover:bg-brand-50 transition-colors shrink-0"
              >
                <Pencil className="w-4 h-4" />
                Edit profile
              </Link>
            </div>
            <p className="text-sm text-brand-600 mb-3">
              {members.length} traveler{members.length !== 1 ? 's' : ''}
              {kids.length > 0 && ` · ${kids.length} kid${kids.length !== 1 ? 's' : ''} under 18`}
            </p>
            <div className="flex flex-wrap gap-2">
              {members.map((member, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-50 text-brand-800 text-xs font-medium border border-brand-100"
                >
                  Age {member.age}
                  {isKid(member) && member.interests.length > 0 && (
                    <span className="text-brand-500">
                      · {member.interests.map((x) => x.replace('_', ' ')).join(', ')}
                    </span>
                  )}
                </span>
              ))}
            </div>
            {kids.some((k) => k.interests.length === 0) && (
              <p className="text-xs text-brand-500 mt-3">
                <Link to="/family" className="text-brand-600 font-medium hover:underline">
                  Add interests for your kids
                </Link>{' '}
                to get personalized activity suggestions on destination pages.
              </p>
            )}
          </div>

          <div className="grid sm:grid-cols-2 gap-6 mb-8">
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-brand-700 mb-2">
                <Euro className="w-4 h-4" />
                Budget (EUR)
              </label>
              <NumericInput
                value={budget}
                onChange={setBudget}
                min={100}
                className="w-full px-4 py-3 rounded-xl border border-brand-200 bg-white/80 focus:outline-none focus:ring-2 focus:ring-brand-400 font-semibold text-lg"
              />
            </div>

            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-brand-700 mb-2">
                <Calendar className="w-4 h-4" />
                Preferred month
              </label>
              <select
                value={preferredMonth}
                onChange={(e) => setPreferredMonth(parseInt(e.target.value))}
                className="w-full px-4 py-3 rounded-xl border border-brand-200 bg-white/80 focus:outline-none focus:ring-2 focus:ring-brand-400"
              >
                {MONTHS.map((m, i) => (
                  <option key={m} value={i + 1}>{m}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-brand-700 mb-2 block">Start date (optional)</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-brand-200 bg-white/80 focus:outline-none focus:ring-2 focus:ring-brand-400"
              />
            </div>

            <div>
              <label className="text-sm font-medium text-brand-700 mb-2 block">End date (optional)</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-brand-200 bg-white/80 focus:outline-none focus:ring-2 focus:ring-brand-400"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="flex items-center gap-2 text-sm font-medium text-brand-700 mb-2">
                <Plane className="w-4 h-4" />
                Departing from (city, country, or city + country)
              </label>
              <OriginLocationInput
                value={originLocation}
                onChange={setOriginLocation}
              />
            </div>
          </div>

          {error && (
            <div className="mb-4 px-4 py-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">
              {error}
            </div>
          )}

          <button
            onClick={() => handleSearch()}
            disabled={loading || budget <= 0}
            className="w-full flex items-center justify-center gap-2 py-4 bg-gradient-to-r from-brand-500 to-brand-600 text-white font-semibold rounded-2xl hover:from-brand-600 hover:to-brand-700 disabled:opacity-60 transition-all shadow-soft text-lg"
          >
            <Search className="w-5 h-5" />
            {loading ? 'Finding destinations...' : 'Get recommendations'}
          </button>
        </div>
      </FadeIn>

      {loading && recommendations.length === 0 && (
        <LoadingSpinner message="Analyzing destinations for your family..." />
      )}

      {!loading && searched && recommendations.length === 0 && !error && (
        <FadeIn>
          <div className="text-center py-16 glass rounded-2xl">
            <p className="text-brand-600">No destinations found matching your criteria. Try increasing your budget.</p>
          </div>
        </FadeIn>
      )}

      {recommendations.length > 0 && (
        <div className="space-y-6">
          <FadeIn>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="font-display text-2xl font-bold text-brand-900">
                Top {recommendations.length} destinations for your family
              </h2>
              <button
                onClick={() => handleSearch(true)}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 rounded-xl border border-brand-200 bg-white text-brand-700 font-medium hover:bg-brand-50 disabled:opacity-60"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                {loading ? 'Regenerating...' : 'Regenerate'}
              </button>
            </div>
            {originMessage && (
              <p className="text-brand-600 text-sm mt-2 flex items-center gap-2">
                <Plane className="w-4 h-4" />
                {originMessage}
              </p>
            )}
          </FadeIn>
          <div className={loading ? 'opacity-50 pointer-events-none' : ''}>
            {recommendations.map((rec, i) => (
              <FadeIn key={rec.destination_id} delay={i * 0.08}>
                <RecommendationCard
                  rec={rec}
                  rank={i + 1}
                  budget={budget}
                  startDate={startDate || undefined}
                  endDate={endDate || undefined}
                  partySize={members.length}
                  originLocation={originLocation.trim() || undefined}
                />
              </FadeIn>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
