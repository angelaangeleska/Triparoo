import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import {
  Baby,
  Calendar,
  Euro,
  Minus,
  Plane,
  Plus,
  Search,
  Sparkles,
  Trash2,
  User,
} from 'lucide-react'
import { api, ApiError } from '../api/client'
import { useAuth } from '../context/AuthContext'
import type { DestinationRecommendation, TripMember } from '../types'
import { INTEREST_OPTIONS, MONTHS } from '../types'
import RecommendationCard from '../components/planner/RecommendationCard'
import OriginLocationInput from '../components/planner/OriginLocationInput'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import FadeIn from '../components/ui/FadeIn'

const defaultMembers: TripMember[] = [
  { age: 35, interests: [] },
  { age: 33, interests: [] },
  { age: 11, gender: 'female', interests: ['disney', 'science'] },
]

export default function PlannerPage() {
  const { isAuthenticated, loading: authLoading } = useAuth()

  const [members, setMembers] = useState<TripMember[]>(defaultMembers)
  const [budget, setBudget] = useState(1500)
  const [preferredMonth, setPreferredMonth] = useState(8)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [originLocation, setOriginLocation] = useState('')
  const [recommendations, setRecommendations] = useState<DestinationRecommendation[]>([])
  const [originMessage, setOriginMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [searched, setSearched] = useState(false)

  const addMember = () => setMembers([...members, { age: 30, interests: [] }])
  const removeMember = (i: number) => setMembers(members.filter((_, idx) => idx !== i))
  const updateMember = (i: number, field: keyof TripMember, value: string | number | string[]) => {
    setMembers(members.map((m, idx) => (idx === i ? { ...m, [field]: value } : m)))
  }

  const toggleInterest = (memberIdx: number, interest: string) => {
    const current = members[memberIdx].interests
    const next = current.includes(interest)
      ? current.filter((x) => x !== interest)
      : [...current, interest]
    updateMember(memberIdx, 'interests', next)
  }

  const handleSearch = async () => {
    setError('')
    setLoading(true)
    setSearched(true)
    try {
      const res = await api.recommend({
        members,
        budget,
        preferred_month: preferredMonth,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        origin_location: originLocation.trim() || undefined,
      })
      setRecommendations(res.recommendations)
      setOriginMessage(res.origin_message || '')
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
            Tell us about your family and we'll find the perfect destinations ranked by our hybrid recommendation engine.
          </p>
        </div>
      </FadeIn>

      <FadeIn delay={0.1}>
        <div className="glass rounded-3xl shadow-card p-6 sm:p-8 mb-10">
          {/* Family members */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-brand-900 flex items-center gap-2">
                <User className="w-5 h-5 text-brand-500" />
                Family members
              </h2>
              <button
                onClick={addMember}
                className="flex items-center gap-1.5 text-sm font-medium text-brand-600 hover:text-brand-800 px-3 py-1.5 rounded-lg hover:bg-brand-50 transition-colors"
              >
                <Plus className="w-4 h-4" />
                Add member
              </button>
            </div>

            <div className="space-y-4">
              {members.map((member, i) => (
                <div key={i} className="p-4 rounded-2xl bg-white/60 border border-brand-100">
                  <div className="flex items-start gap-4 flex-wrap">
                    <div className="flex items-center gap-2">
                      <Baby className="w-4 h-4 text-brand-400" />
                      <label className="text-sm text-brand-600">Age</label>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => updateMember(i, 'age', Math.max(0, member.age - 1))}
                          className="w-8 h-8 rounded-lg bg-brand-100 hover:bg-brand-200 flex items-center justify-center"
                        >
                          <Minus className="w-3.5 h-3.5" />
                        </button>
                        <input
                          type="number"
                          value={member.age}
                          onChange={(e) => updateMember(i, 'age', parseInt(e.target.value) || 0)}
                          className="w-16 text-center py-1.5 rounded-lg border border-brand-200 bg-white font-semibold"
                          min={0}
                          max={120}
                        />
                        <button
                          onClick={() => updateMember(i, 'age', member.age + 1)}
                          className="w-8 h-8 rounded-lg bg-brand-100 hover:bg-brand-200 flex items-center justify-center"
                        >
                          <Plus className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <div>
                      <label className="text-sm text-brand-600 block mb-1">Gender (optional)</label>
                      <select
                        value={member.gender || ''}
                        onChange={(e) => updateMember(i, 'gender', e.target.value || '')}
                        className="px-3 py-1.5 rounded-lg border border-brand-200 bg-white text-sm"
                      >
                        <option value="">—</option>
                        <option value="male">Male</option>
                        <option value="female">Female</option>
                      </select>
                    </div>

                    {members.length > 1 && (
                      <button
                        onClick={() => removeMember(i)}
                        className="ml-auto p-2 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>

                  {member.age < 18 && (
                    <div className="mt-3">
                      <label className="text-xs text-brand-500 font-medium mb-2 block">Interests</label>
                      <div className="flex flex-wrap gap-2">
                        {INTEREST_OPTIONS.map((interest) => (
                          <button
                            key={interest}
                            onClick={() => toggleInterest(i, interest)}
                            className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                              member.interests.includes(interest)
                                ? 'bg-brand-500 text-white'
                                : 'bg-brand-100 text-brand-700 hover:bg-brand-200'
                            }`}
                          >
                            {interest.replace('_', ' ')}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Budget & dates */}
          <div className="grid sm:grid-cols-2 gap-6 mb-8">
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-brand-700 mb-2">
                <Euro className="w-4 h-4" />
                Budget (EUR)
              </label>
              <input
                type="number"
                value={budget}
                onChange={(e) => setBudget(parseFloat(e.target.value) || 0)}
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
                Departing from (city or country)
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
            onClick={handleSearch}
            disabled={loading || budget <= 0}
            className="w-full flex items-center justify-center gap-2 py-4 bg-gradient-to-r from-brand-500 to-brand-600 text-white font-semibold rounded-2xl hover:from-brand-600 hover:to-brand-700 disabled:opacity-60 transition-all shadow-soft text-lg"
          >
            <Search className="w-5 h-5" />
            {loading ? 'Finding destinations...' : 'Get recommendations'}
          </button>
        </div>
      </FadeIn>

      {loading && <LoadingSpinner message="Analyzing destinations for your family..." />}

      {!loading && searched && recommendations.length === 0 && !error && (
        <FadeIn>
          <div className="text-center py-16 glass rounded-2xl">
            <p className="text-brand-600">No destinations found matching your criteria. Try increasing your budget.</p>
          </div>
        </FadeIn>
      )}

      {!loading && recommendations.length > 0 && (
        <div className="space-y-6">
          <FadeIn>
            <h2 className="font-display text-2xl font-bold text-brand-900">
              Top {recommendations.length} destinations for your family
            </h2>
            {originMessage && (
              <p className="text-brand-600 text-sm mt-2 flex items-center gap-2">
                <Plane className="w-4 h-4" />
                {originMessage}
              </p>
            )}
          </FadeIn>
          {recommendations.map((rec, i) => (
            <FadeIn key={rec.destination_id} delay={i * 0.08}>
              <RecommendationCard
                rec={rec}
                rank={i + 1}
                startDate={startDate || undefined}
                endDate={endDate || undefined}
                partySize={members.length}
              />
            </FadeIn>
          ))}
        </div>
      )}
    </div>
  )
}
