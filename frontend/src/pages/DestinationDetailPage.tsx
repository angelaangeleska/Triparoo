import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import {
  ArrowLeft,
  Baby,
  Bed,
  Calendar,
  Clock,
  Euro,
  Heart,
  MapPin,
  Sparkles,
  Star,
  Sun,
  Ticket,
  Users as UsersIcon,
  Wallet,
} from 'lucide-react'
import { ApiError } from '../api/client'
import {
  toTripMember,
  useAiGuide,
  useAttractions,
  useBudgetOptimize,
  useCheapestDates,
  useChildActivitiesForChildren,
  useDestination,
  useFamilyMembers,
  useHotels,
  useItinerary,
} from '../api/hooks'
import type { BudgetAlternative, CheapestPeriod, ItineraryDay } from '../types'
import { MONTHS } from '../types'
import HotelCard from '../components/planner/HotelCard'
import OriginLocationInput from '../components/planner/OriginLocationInput'
import CityImage from '../components/ui/CityImage'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import FadeIn from '../components/ui/FadeIn'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Label } from '../components/ui/Label'
import { Badge } from '../components/ui/Badge'
import { Skeleton } from '../components/ui/Skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/Tabs'
import { useAuth } from '../context/AuthContext'

function localDateOffset(days: number): string {
  const d = new Date()
  d.setDate(d.getDate() + days)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export default function DestinationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const { t } = useTranslation()
  const tripState = location.state as {
    startDate?: string
    endDate?: string
    partySize?: number
    originLocation?: string
  } | null

  const destId = parseInt(id || '0')
  const destinationQuery = useDestination(destId)
  const attractionsQuery = useAttractions(destId)
  const familyQuery = useFamilyMembers(isAuthenticated)
  const members = familyQuery.data ?? []
  const children = members.filter((m) => m.age < 18)

  const destination = destinationQuery.data
  const checkIn = tripState?.startDate || localDateOffset(30)
  const checkOut = tripState?.endDate || localDateOffset(35)
  const hotelsQuery = useHotels(
    destination?.city || '',
    checkIn,
    checkOut,
    tripState?.partySize ?? 2,
    0,
    destination?.country || ''
  )

  const [tab, setTab] = useState('overview')

  // Itinerary
  const [duration, setDuration] = useState(5)
  const [itineraryBudget, setItineraryBudget] = useState(1500)
  const [itinerary, setItinerary] = useState<ItineraryDay[] | null>(null)
  const [itineraryCost, setItineraryCost] = useState(0)
  const itineraryMutation = useItinerary()

  // Kids activities — auto-filled from saved family, no re-entry
  const childQueries = useChildActivitiesForChildren(destId, children)

  // AI Trip Guide
  const aiGuideMutation = useAiGuide()

  // Cheapest dates
  const [cheapestPeriods, setCheapestPeriods] = useState<CheapestPeriod[]>([])
  const [datesOrigin, setDatesOrigin] = useState(tripState?.originLocation || '')
  const [datesPartySize, setDatesPartySize] = useState(tripState?.partySize ?? (members.length || 2))
  const [datesOriginMessage, setDatesOriginMessage] = useState('')
  const [datesSearched, setDatesSearched] = useState(false)
  const cheapestDatesMutation = useCheapestDates()

  // Budget
  const [budgetResult, setBudgetResult] = useState<{
    current_estimate: number
    budget: number
    within_budget: boolean
    alternatives: BudgetAlternative[]
  } | null>(null)
  const budgetMutation = useBudgetOptimize()

  const [error, setError] = useState('')

  useEffect(() => {
    setDatesPartySize(tripState?.partySize ?? (members.length || 2))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [members.length])

  const requireAuth = () => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: location } })
      return false
    }
    return true
  }

  const generateItinerary = async () => {
    if (!requireAuth()) return
    if (members.length === 0) {
      toast.error(t('planner.noSavedFamily'))
      return
    }
    setError('')
    try {
      const res = await itineraryMutation.mutateAsync({
        destination_id: destId,
        members: members.map(toTripMember),
        duration_days: duration,
        budget: itineraryBudget,
      })
      setItinerary(res.days)
      setItineraryCost(res.total_estimated_cost)
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Failed to generate itinerary'
      setError(message)
      toast.error(message)
    }
  }

  const generateAiGuide = async () => {
    if (!requireAuth()) return
    if (members.length === 0) {
      toast.error(t('planner.noSavedFamily'))
      return
    }
    try {
      await aiGuideMutation.mutateAsync({
        destination_id: destId,
        members: members.map(toTripMember),
        budget: itineraryBudget,
        start_date: tripState?.startDate,
        end_date: tripState?.endDate,
      })
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : 'Failed to generate AI guide')
    }
  }

  const loadCheapestDates = async () => {
    if (!requireAuth()) return
    if (!datesOrigin.trim()) {
      setError(t('dates.needsOrigin'))
      return
    }
    setError('')
    setDatesSearched(true)
    try {
      const res = await cheapestDatesMutation.mutateAsync({
        destination_id: destId,
        party_size: datesPartySize,
        origin_location: datesOrigin.trim(),
      })
      setCheapestPeriods(res.cheapest_periods)
      setDatesOriginMessage(res.origin_message || '')
    } catch (err) {
      setCheapestPeriods([])
      setError(err instanceof ApiError ? err.message : 'Failed to load dates')
    }
  }

  const loadBudget = async () => {
    if (!requireAuth()) return
    if (members.length === 0) return
    setError('')
    try {
      const res = await budgetMutation.mutateAsync({
        destination_id: destId,
        origin_location: datesOrigin.trim() || tripState?.originLocation || undefined,
        members: members.map(toTripMember),
        budget: itineraryBudget,
        start_date: tripState?.startDate || localDateOffset(30),
        end_date: tripState?.endDate || localDateOffset(37),
      })
      setBudgetResult(res)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to optimize budget')
    }
  }

  const tabs = [
    { key: 'overview', label: t('destinationDetail.tabOverview'), icon: MapPin },
    { key: 'itinerary', label: t('destinationDetail.tabItinerary'), icon: Calendar },
    { key: 'activities', label: t('destinationDetail.tabKids'), icon: Baby },
    { key: 'ai-guide', label: t('destinationDetail.tabAiGuide'), icon: Sparkles },
    { key: 'dates', label: t('destinationDetail.tabDates'), icon: Sun },
    { key: 'budget', label: t('destinationDetail.tabBudget'), icon: Wallet },
  ]

  const handleTabChange = (key: string) => {
    setTab(key)
    if (key === 'dates' && !datesSearched && datesOrigin.trim()) loadCheapestDates()
    if (key === 'budget' && !budgetResult) loadBudget()
  }

  if (destinationQuery.isLoading) return <LoadingSpinner fullScreen />
  if (!destination) {
    return (
      <div className="text-center py-24">
        <p className="text-brand-600 dark:text-brand-300 mb-4">{t('common.error')}</p>
        <Link to="/destinations" className="text-brand-700 dark:text-brand-200 font-medium hover:underline">
          ← {t('destinations.title')}
        </Link>
      </div>
    )
  }

  return (
    <div>
      {/* Hero banner */}
      <div className="relative h-72 sm:h-96 overflow-hidden">
        <CityImage city={destination.city ?? ''} alt={destination.city} className="w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-t from-brand-900/80 via-brand-900/30 to-transparent" />
        <div className="absolute bottom-0 inset-x-0 p-6 sm:p-10 max-w-7xl mx-auto">
          <Link
            to="/destinations"
            className="inline-flex items-center gap-1.5 text-white/70 hover:text-white text-sm mb-4 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            {t('destinations.title')}
          </Link>
          <h1 className="font-display text-4xl sm:text-5xl font-bold text-white">{destination.city}</h1>
          <p className="text-white/80 flex items-center gap-2 mt-2">
            <MapPin className="w-4 h-4" />
            {destination.country}
          </p>
          <div className="flex gap-4 mt-4">
            <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/15 backdrop-blur text-white text-sm">
              <Heart className="w-4 h-4 text-sunset-400" />
              {t('destinations.familyScore')} {destination.family_friendliness_score.toFixed(0)}
            </span>
            <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/15 backdrop-blur text-white text-sm">
              <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
              {t('destinations.popularity')} {destination.popularity_score.toFixed(0)}
            </span>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={tab} onValueChange={handleTabChange}>
          <div className="sticky top-16 z-40 -mx-4 px-4 sm:mx-0 sm:px-0 py-3 mb-6 overflow-x-auto">
            <TabsList>
              {tabs.map(({ key, label, icon: Icon }) => (
                <TabsTrigger key={key} value={key}>
                  <Icon className="w-4 h-4" />
                  {label}
                </TabsTrigger>
              ))}
            </TabsList>
          </div>

          {error && (
            <div className="mb-6 px-4 py-3 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-300 text-sm">
              {error}
            </div>
          )}

          {/* Overview */}
          <TabsContent value="overview">
            <FadeIn>
              <p className="text-brand-700 dark:text-brand-200 text-lg leading-relaxed mb-8 max-w-3xl">
                {destination.description}
              </p>

              <div className="grid lg:grid-cols-2 gap-8">
                <div>
                  <h2 className="font-display text-2xl font-bold text-brand-900 dark:text-white mb-4 flex items-center gap-2">
                    <Ticket className="w-6 h-6 text-brand-500" />
                    {t('destinationDetail.attractions')}
                  </h2>
                  <div className="space-y-3">
                    {(attractionsQuery.data ?? []).map((a) => (
                      <div
                        key={a.id}
                        className="glass dark:bg-brand-900/50 dark:border-brand-800 rounded-xl p-4 flex justify-between items-start gap-4"
                      >
                        <div>
                          <h3 className="font-semibold text-brand-900 dark:text-white">{a.name}</h3>
                          <p className="text-xs text-brand-500 dark:text-brand-400 mt-0.5">
                            {a.category} · Ages {a.min_age}–{a.max_age}
                          </p>
                          {a.description && (
                            <p className="text-sm text-brand-600 dark:text-brand-300 mt-1">{a.description}</p>
                          )}
                        </div>
                        <span className="text-sm font-semibold text-brand-700 dark:text-brand-200 whitespace-nowrap">
                          {a.price === 0 ? t('common.free') : `€${a.price}`}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h2 className="font-display text-2xl font-bold text-brand-900 dark:text-white mb-4 flex items-center gap-2">
                    <Bed className="w-6 h-6 text-brand-500" />
                    {t('destinationDetail.hotels')}
                  </h2>
                  {hotelsQuery.isLoading && (
                    <div className="space-y-3">
                      <Skeleton className="h-28" />
                      <Skeleton className="h-28" />
                    </div>
                  )}
                  {hotelsQuery.isError && (
                    <p className="text-sm text-red-600 dark:text-red-300 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 rounded-xl px-4 py-3 mb-3">
                      {t('errors.genericLoadFailed')}
                    </p>
                  )}
                  {!hotelsQuery.isLoading && (hotelsQuery.data?.length ?? 0) > 0 && (
                    <div className="space-y-3">
                      {hotelsQuery.data!.map((h, i) => (
                        <HotelCard key={i} hotel={h} />
                      ))}
                    </div>
                  )}
                  {!hotelsQuery.isLoading && !hotelsQuery.isError && (hotelsQuery.data?.length ?? 0) === 0 && (
                    <p className="text-sm text-brand-500 dark:text-brand-400 text-center py-6">
                      {t('destinationDetail.noHotels')}
                    </p>
                  )}
                </div>
              </div>
            </FadeIn>
          </TabsContent>

          {/* Itinerary */}
          <TabsContent value="itinerary">
            <FadeIn>
              <div className="glass dark:bg-brand-900/50 dark:border-brand-800 rounded-2xl p-6 mb-8 max-w-lg">
                <h2 className="font-semibold text-brand-900 dark:text-white mb-4">
                  {t('destinationDetail.generateItinerary')}
                </h2>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <Label>{t('destinationDetail.duration')}</Label>
                    <Input
                      type="number"
                      value={duration}
                      onChange={(e) => setDuration(parseInt(e.target.value) || 1)}
                      min={1}
                      max={30}
                    />
                  </div>
                  <div>
                    <Label>{t('planner.budget')}</Label>
                    <Input
                      type="number"
                      value={itineraryBudget}
                      onChange={(e) => setItineraryBudget(parseFloat(e.target.value) || 0)}
                      min={100}
                    />
                  </div>
                </div>
                <Button className="w-full" onClick={generateItinerary} disabled={itineraryMutation.isPending}>
                  <Sparkles className="w-4 h-4" />
                  {itineraryMutation.isPending ? t('destinationDetail.generating') : t('destinationDetail.generate')}
                </Button>
              </div>

              {itinerary && (
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="font-display text-2xl font-bold text-brand-900 dark:text-white">
                      {t('destinationDetail.yourPlan', { days: duration })}
                    </h2>
                    <span className="flex items-center gap-1.5 text-brand-700 dark:text-brand-200 font-semibold">
                      <Euro className="w-4 h-4" />
                      €{itineraryCost.toFixed(0)} {t('destinationDetail.total')}
                    </span>
                  </div>
                  <div className="space-y-4">
                    {itinerary.map((day) => (
                      <div key={day.day_number} className="glass dark:bg-brand-900/50 dark:border-brand-800 rounded-2xl p-6">
                        <h3 className="font-display text-xl font-semibold text-brand-900 dark:text-white mb-1">
                          {day.title}
                        </h3>
                        {day.narrative && (
                          <p className="flex items-center gap-1.5 text-sm text-brand-500 dark:text-brand-400 italic mb-4">
                            <Sparkles className="w-3.5 h-3.5 shrink-0" />
                            {day.narrative}
                          </p>
                        )}
                        <div className="space-y-3 mt-4">
                          {day.items.map((item, i) => (
                            <div key={i} className="flex gap-4 items-start">
                              <div className="flex items-center gap-1.5 text-xs font-medium text-brand-500 dark:text-brand-300 bg-brand-50 dark:bg-brand-800 px-2.5 py-1 rounded-lg whitespace-nowrap">
                                <Clock className="w-3 h-3" />
                                {item.time}
                              </div>
                              <div className="flex-1">
                                <p className="font-medium text-brand-800 dark:text-brand-100">{item.activity}</p>
                                {item.description && (
                                  <p className="text-sm text-brand-600 dark:text-brand-300 mt-0.5">{item.description}</p>
                                )}
                              </div>
                              {item.estimated_cost > 0 && (
                                <span className="text-sm text-brand-600 dark:text-brand-300">€{item.estimated_cost}</span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </FadeIn>
          </TabsContent>

          {/* Kids activities — auto-filled from saved family */}
          <TabsContent value="activities">
            <FadeIn>
              <h2 className="font-display text-2xl font-bold text-brand-900 dark:text-white mb-2">
                {t('kids.title')}
              </h2>
              <p className="text-brand-600 dark:text-brand-300 mb-8 max-w-2xl">{t('kids.subtitle')}</p>

              {!isAuthenticated && (
                <div className="text-center py-16 glass dark:bg-brand-900/50 rounded-2xl">
                  <p className="text-brand-600 dark:text-brand-300 mb-4">{t('auth.loginRequiredDesc')}</p>
                  <Button onClick={() => navigate('/login', { state: { from: location } })}>
                    {t('auth.signIn')}
                  </Button>
                </div>
              )}

              {isAuthenticated && familyQuery.isLoading && (
                <div className="grid sm:grid-cols-2 gap-4">
                  <Skeleton className="h-40" />
                  <Skeleton className="h-40" />
                </div>
              )}

              {isAuthenticated && !familyQuery.isLoading && children.length === 0 && (
                <div className="text-center py-16 glass dark:bg-brand-900/50 rounded-2xl">
                  <Baby className="w-10 h-10 text-brand-300 dark:text-brand-600 mx-auto mb-4" />
                  <p className="text-brand-700 dark:text-brand-200 font-medium">{t('kids.noChildren')}</p>
                  <p className="text-brand-500 dark:text-brand-400 text-sm mt-1 max-w-sm mx-auto">
                    {t('kids.noChildrenCta')}
                  </p>
                  <Button className="mt-5" asChild>
                    <Link to="/family">{t('kids.goToFamily')}</Link>
                  </Button>
                </div>
              )}

              {isAuthenticated && children.length > 0 && (
                <div className="space-y-10">
                  {children.map((child, idx) => {
                    const query = childQueries[idx]
                    const activities = query?.data?.activities ?? []
                    return (
                      <div key={child.id}>
                        <h3 className="font-display text-xl font-semibold text-brand-900 dark:text-white mb-4 flex items-center gap-2">
                          <Baby className="w-5 h-5 text-sunset-500" />
                          {t('kids.activitiesFor', { name: child.name || `#${child.id}`, age: child.age })}
                        </h3>
                        {query?.isLoading && (
                          <div className="grid sm:grid-cols-2 gap-4">
                            <Skeleton className="h-32" />
                            <Skeleton className="h-32" />
                          </div>
                        )}
                        {!query?.isLoading && activities.length === 0 && (
                          <p className="text-sm text-brand-600 dark:text-brand-300 text-center py-8 glass dark:bg-brand-900/50 rounded-xl">
                            {t('kids.noMatches', { name: child.name || `#${child.id}` })}
                          </p>
                        )}
                        {!query?.isLoading && activities.length > 0 && (
                          <div className="grid sm:grid-cols-2 gap-4">
                            {activities.map((a) => (
                              <div key={a.id} className="glass dark:bg-brand-900/50 dark:border-brand-800 rounded-xl p-5">
                                <div className="flex justify-between items-start mb-2">
                                  <h4 className="font-semibold text-brand-900 dark:text-white">{a.name}</h4>
                                  <span className="text-xs font-bold px-2 py-1 rounded-full bg-brand-500/10 dark:bg-brand-400/10 text-brand-700 dark:text-brand-200">
                                    {a.match_score.toFixed(0)}% {t('kids.match')}
                                  </span>
                                </div>
                                <p className="text-xs text-brand-500 dark:text-brand-400 mb-2">{a.category}</p>
                                {a.description && (
                                  <p className="text-sm text-brand-600 dark:text-brand-300 mb-2">{a.description}</p>
                                )}
                                <p className="text-xs text-brand-500 dark:text-brand-400 italic">{a.reason}</p>
                                <p className="text-sm font-semibold text-brand-700 dark:text-brand-200 mt-2">
                                  {a.price === 0 ? t('common.free') : `€${a.price}`}
                                </p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </FadeIn>
          </TabsContent>

          {/* AI Trip Guide */}
          <TabsContent value="ai-guide">
            <FadeIn>
              <h2 className="font-display text-2xl font-bold text-brand-900 dark:text-white mb-2 flex items-center gap-2">
                <Sparkles className="w-6 h-6 text-brand-500" />
                {t('aiGuide.title')}
              </h2>
              <p className="text-brand-600 dark:text-brand-300 mb-6 max-w-2xl">{t('aiGuide.subtitle')}</p>

              {!aiGuideMutation.data && (
                <Button onClick={generateAiGuide} disabled={aiGuideMutation.isPending}>
                  <Sparkles className="w-4 h-4" />
                  {aiGuideMutation.isPending ? t('aiGuide.generating') : t('aiGuide.generate')}
                </Button>
              )}

              {aiGuideMutation.data && !aiGuideMutation.data.available && (
                <div className="text-center py-16 glass dark:bg-brand-900/50 rounded-2xl max-w-lg mx-auto">
                  <Sparkles className="w-10 h-10 text-brand-300 dark:text-brand-600 mx-auto mb-4" />
                  <p className="text-brand-700 dark:text-brand-200 font-medium">{t('aiGuide.unavailableTitle')}</p>
                  <p className="text-brand-500 dark:text-brand-400 text-sm mt-1">{t('aiGuide.unavailableDesc')}</p>
                </div>
              )}

              {aiGuideMutation.data?.available && (
                <div className="space-y-10 mt-8">
                  {(
                    [
                      ['attractions', t('aiGuide.attractions')],
                      ['restaurants', t('aiGuide.restaurants')],
                      ['hidden_gems', t('aiGuide.hiddenGems')],
                      ['local_tips', t('aiGuide.localTips')],
                      ['transportation_tips', t('aiGuide.transportationTips')],
                    ] as const
                  ).map(([key, label]) => {
                    const items = aiGuideMutation.data![key]
                    if (!items || items.length === 0) return null
                    return (
                      <div key={key}>
                        <h3 className="font-display text-xl font-semibold text-brand-900 dark:text-white mb-4">
                          {label}
                        </h3>
                        <div className="grid sm:grid-cols-2 gap-4">
                          {items.map((item, i) => (
                            <div
                              key={i}
                              className="glass dark:bg-brand-900/50 dark:border-brand-800 rounded-xl p-5"
                            >
                              <h4 className="font-semibold text-brand-900 dark:text-white mb-1.5">{item.title}</h4>
                              <p className="text-sm text-brand-600 dark:text-brand-300 mb-2">{item.description}</p>
                              {item.why_recommended && (
                                <p className="text-xs text-brand-500 dark:text-brand-400 italic">
                                  {item.why_recommended}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </FadeIn>
          </TabsContent>

          {/* Cheapest dates */}
          <TabsContent value="dates">
            <FadeIn>
              <h2 className="font-display text-2xl font-bold text-brand-900 dark:text-white mb-6">
                {t('dates.title')}
              </h2>

              <div className="glass dark:bg-brand-900/50 dark:border-brand-800 rounded-2xl p-6 mb-8 max-w-lg space-y-4">
                <div>
                  <Label>{t('planner.departingFrom')}</Label>
                  <OriginLocationInput value={datesOrigin} onChange={setDatesOrigin} />
                </div>
                <div>
                  <Label>{t('dates.travelers')}</Label>
                  <Input
                    type="number"
                    value={datesPartySize}
                    onChange={(e) => setDatesPartySize(Math.max(1, parseInt(e.target.value) || 1))}
                    min={1}
                    max={9}
                  />
                </div>
                <Button
                  className="w-full"
                  onClick={loadCheapestDates}
                  disabled={cheapestDatesMutation.isPending || !datesOrigin.trim()}
                >
                  {cheapestDatesMutation.isPending ? t('dates.loadingPrices') : t('dates.compare')}
                </Button>
                {!datesOrigin.trim() && (
                  <p className="text-xs text-brand-500 dark:text-brand-400">{t('dates.needsOrigin')}</p>
                )}
              </div>

              {datesOriginMessage && (
                <p className="text-sm text-brand-600 dark:text-brand-300 mb-4 px-4 py-3 rounded-xl bg-brand-50 dark:bg-brand-800/40 border border-brand-100 dark:border-brand-700">
                  {datesOriginMessage}
                </p>
              )}

              {cheapestDatesMutation.isPending && <LoadingSpinner message={t('dates.loadingPrices') ?? undefined} />}

              {datesSearched && !cheapestDatesMutation.isPending && cheapestPeriods.length > 0 && (
                <div className="grid sm:grid-cols-2 gap-4">
                  {cheapestPeriods.map((p, i) => (
                    <div
                      key={p.season}
                      className={`glass dark:bg-brand-900/50 dark:border-brand-800 rounded-2xl p-6 ${
                        i === 0 ? 'ring-2 ring-brand-400' : ''
                      }`}
                    >
                      {i === 0 && (
                        <span className="text-xs font-bold text-brand-500 dark:text-brand-300 uppercase tracking-wider">
                          {t('dates.bestValue')}
                        </span>
                      )}
                      <h3 className="font-display text-xl font-semibold text-brand-900 dark:text-white capitalize mt-1">
                        {p.season}
                      </h3>
                      <p className="text-sm text-brand-600 dark:text-brand-300 mb-4">
                        {MONTHS[p.month_start - 1]} – {MONTHS[p.month_end - 1]}
                      </p>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-brand-600 dark:text-brand-300">{t('dates.flights')}</span>
                          <span className="font-semibold text-brand-900 dark:text-white">
                            {p.avg_flight_price > 0 ? `€${p.avg_flight_price.toFixed(0)}` : '—'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-brand-600 dark:text-brand-300">{t('dates.accommodationPerNight')}</span>
                          <span className="font-semibold text-brand-900 dark:text-white">
                            €{p.avg_accommodation_price.toFixed(0)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-brand-600 dark:text-brand-300">{t('dates.weatherScore')}</span>
                          <span className="font-semibold text-brand-900 dark:text-white">
                            {p.weather_score.toFixed(0)}%
                          </span>
                        </div>
                        <div className="flex justify-between pt-2 border-t border-brand-100 dark:border-brand-700">
                          <span className="font-medium text-brand-800 dark:text-brand-100">{t('dates.totalPrice')}</span>
                          <span className="font-bold text-brand-900 dark:text-white">€{p.estimated_total.toFixed(0)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </FadeIn>
          </TabsContent>

          {/* Budget */}
          <TabsContent value="budget">
            <FadeIn>
              {members.length === 0 ? (
                <div className="text-center py-16 glass dark:bg-brand-900/50 rounded-2xl">
                  <UsersIcon className="w-10 h-10 text-brand-300 dark:text-brand-600 mx-auto mb-4" />
                  <p className="text-brand-700 dark:text-brand-200 font-medium">{t('family.empty')}</p>
                  <p className="text-brand-500 dark:text-brand-400 text-sm mt-1">{t('family.emptyCta')}</p>
                  <Button className="mt-5" asChild>
                    <Link to="/family">{t('kids.goToFamily')}</Link>
                  </Button>
                </div>
              ) : !budgetResult ? (
                <LoadingSpinner message={t('common.loading') ?? undefined} />
              ) : (
                <div>
                  <div
                    className={`glass dark:bg-brand-900/50 rounded-2xl p-6 mb-8 ${
                      budgetResult.within_budget ? 'ring-2 ring-emerald-400' : 'ring-2 ring-sunset-400'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-brand-600 dark:text-brand-300">{t('budget.currentEstimate')}</p>
                        <p className="text-3xl font-bold text-brand-900 dark:text-white">
                          €{budgetResult.current_estimate.toFixed(0)}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-brand-600 dark:text-brand-300">{t('budget.yourBudget')}</p>
                        <p className="text-3xl font-bold text-brand-900 dark:text-white">
                          €{budgetResult.budget.toFixed(0)}
                        </p>
                      </div>
                    </div>
                    <p
                      className={`mt-3 text-sm font-medium ${
                        budgetResult.within_budget ? 'text-emerald-600' : 'text-sunset-600'
                      }`}
                    >
                      {budgetResult.within_budget ? `✓ ${t('budget.withinBudget')}` : `⚠ ${t('budget.overBudget')}`}
                    </p>
                  </div>

                  {budgetResult.alternatives.length > 0 && (
                    <div>
                      <h2 className="font-display text-xl font-bold text-brand-900 dark:text-white mb-4">
                        {t('budget.waysToSave')}
                      </h2>
                      <div className="space-y-3">
                        {budgetResult.alternatives.map((alt, i) => (
                          <div
                            key={i}
                            className="glass dark:bg-brand-900/50 dark:border-brand-800 rounded-xl p-5 flex justify-between items-center gap-4"
                          >
                            <div>
                              <p className="font-medium text-brand-900 dark:text-white">{alt.description}</p>
                              <Badge variant="muted" className="mt-1 capitalize">
                                {alt.type.replace('_', ' ')}
                              </Badge>
                            </div>
                            <div className="text-right whitespace-nowrap">
                              <p className="text-sm font-bold text-emerald-600">
                                {t('budget.save', { amount: alt.estimated_savings.toFixed(0) })}
                              </p>
                              <p className="text-xs text-brand-600 dark:text-brand-300">
                                {t('budget.newTotal', { amount: alt.new_total.toFixed(0) })}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </FadeIn>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
