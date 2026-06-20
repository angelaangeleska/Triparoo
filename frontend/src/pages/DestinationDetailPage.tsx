import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
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
  Wallet,
} from 'lucide-react'
import { api, ApiError } from '../api/client'
import { useAuth } from '../context/AuthContext'
import type {
  AccommodationSummary,
  Attraction,
  BudgetAlternative,
  CheapestPeriod,
  ChildActivity,
  Destination,
  ItineraryDay,
  TripMember,
} from '../types'
import HotelCard from '../components/planner/HotelCard'
import OriginLocationInput from '../components/planner/OriginLocationInput'
import { INTEREST_OPTIONS, MONTHS } from '../types'
import CityImage from '../components/ui/CityImage'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import FadeIn from '../components/ui/FadeIn'

type Tab = 'overview' | 'itinerary' | 'activities' | 'dates' | 'budget'

export default function DestinationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const tripState = location.state as {
    startDate?: string
    endDate?: string
    partySize?: number
    originLocation?: string
  } | null

  const [destination, setDestination] = useState<Destination | null>(null)
  const [attractions, setAttractions] = useState<Attraction[]>([])
  const [hotels, setHotels] = useState<AccommodationSummary[]>([])
  const [hotelsLoading, setHotelsLoading] = useState(false)
  const [tab, setTab] = useState<Tab>('overview')
  const [loading, setLoading] = useState(true)

  // Itinerary state
  const [duration, setDuration] = useState(5)
  const [itineraryBudget, setItineraryBudget] = useState(1500)
  const [itinerary, setItinerary] = useState<ItineraryDay[] | null>(null)
  const [itineraryCost, setItineraryCost] = useState(0)
  const [itineraryLoading, setItineraryLoading] = useState(false)

  // Child activities state
  const [childAge, setChildAge] = useState(11)
  const [childInterests, setChildInterests] = useState<string[]>(['disney'])
  const [childActivities, setChildActivities] = useState<ChildActivity[]>([])
  const [childActivitiesSearched, setChildActivitiesSearched] = useState(false)
  const [childActivitiesLoading, setChildActivitiesLoading] = useState(false)

  // Cheapest dates
  const [cheapestPeriods, setCheapestPeriods] = useState<CheapestPeriod[]>([])
  const [datesOrigin, setDatesOrigin] = useState(tripState?.originLocation || '')
  const [datesPartySize, setDatesPartySize] = useState(tripState?.partySize ?? 3)
  const [datesOriginMessage, setDatesOriginMessage] = useState('')
  const [datesLoading, setDatesLoading] = useState(false)
  const [datesSearched, setDatesSearched] = useState(false)

  // Budget
  const [budgetResult, setBudgetResult] = useState<{
    current_estimate: number
    budget: number
    within_budget: boolean
    alternatives: BudgetAlternative[]
  } | null>(null)

  const [error, setError] = useState('')
  const [hotelsError, setHotelsError] = useState('')

  const destId = parseInt(id || '0')
  function localDateOffset(days: number): string {
    const d = new Date()
    d.setDate(d.getDate() + days)
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    return `${y}-${m}-${day}`
  }

  const defaultMembers: TripMember[] = [
    { age: 35, interests: [] },
    { age: 33, interests: [] },
    { age: 11, gender: 'female', interests: ['disney'] },
  ]

  useEffect(() => {
    if (!destId) return
    Promise.all([api.destination(destId), api.attractions(destId)])
      .then(([dest, att]) => {
        setDestination(dest)
        setAttractions(att)
        // Load hotels once we know the city name
        const city = dest.city
        const country = dest.country
        if (!city) return
        const checkIn = tripState?.startDate || localDateOffset(30)
        const checkOut = tripState?.endDate || localDateOffset(35)
        const adults = tripState?.partySize ?? 2
        setHotelsLoading(true)
        setHotelsError('')
        api.searchHotels(city, checkIn, checkOut, adults, 0, country || '')
          .then(setHotels)
          .catch((err) => {
            console.error('Hotels error:', err)
            setHotelsError(err instanceof ApiError ? err.message : 'Could not load hotels')
          })
          .finally(() => setHotelsLoading(false))
      })
      .catch(() => setError('Destination not found'))
      .finally(() => setLoading(false))
  }, [destId])

  const requireAuth = () => {
    if (!isAuthenticated) {
      navigate('/login')
      return false
    }
    return true
  }

  const generateItinerary = async () => {
    if (!requireAuth()) return
    setItineraryLoading(true)
    setError('')
    try {
      const res = await api.itinerary({
        destination_id: destId,
        members: defaultMembers,
        duration_days: duration,
        budget: itineraryBudget,
      })
      setItinerary(res.days)
      setItineraryCost(res.total_estimated_cost)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to generate itinerary')
    } finally {
      setItineraryLoading(false)
    }
  }

  const loadChildActivities = async () => {
    if (!requireAuth()) return
    if (childInterests.length === 0) return
    setError('')
    setChildActivitiesLoading(true)
    setChildActivitiesSearched(true)
    try {
      const res = await api.childActivities({
        destination_id: destId,
        age: childAge,
        interests: childInterests,
      })
      setChildActivities(res.activities)
    } catch (err) {
      setChildActivities([])
      setError(err instanceof ApiError ? err.message : 'Failed to load activities')
    } finally {
      setChildActivitiesLoading(false)
    }
  }

  const loadCheapestDates = async () => {
    if (!requireAuth()) return
    if (!datesOrigin.trim()) {
      setError('Enter your departure city or country to see flight prices.')
      return
    }
    setError('')
    setDatesLoading(true)
    setDatesSearched(true)
    try {
      const res = await api.cheapestDates({
        destination_id: destId,
        party_size: datesPartySize,
        origin_location: datesOrigin.trim(),
      })
      setCheapestPeriods(res.cheapest_periods)
      setDatesOriginMessage(res.origin_message || '')
    } catch (err) {
      setCheapestPeriods([])
      setError(err instanceof ApiError ? err.message : 'Failed to load dates')
    } finally {
      setDatesLoading(false)
    }
  }

  const loadBudget = async () => {
    if (!requireAuth()) return
    setError('')
    try {
      const res = await api.budgetOptimize({
        destination_id: destId,
        origin_location: datesOrigin.trim() || tripState?.originLocation || undefined,
        members: defaultMembers,
        budget: 1500,
        start_date: tripState?.startDate || localDateOffset(30),
        end_date: tripState?.endDate || localDateOffset(37),
      })
      setBudgetResult(res)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to optimize budget')
    }
  }

  const tabs: { key: Tab; label: string; icon: typeof MapPin }[] = [
    { key: 'overview', label: 'Overview', icon: MapPin },
    { key: 'itinerary', label: 'Itinerary', icon: Calendar },
    { key: 'activities', label: 'Kids', icon: Baby },
    { key: 'dates', label: 'Best Dates', icon: Sun },
    { key: 'budget', label: 'Budget', icon: Wallet },
  ]

  if (loading) return <LoadingSpinner fullScreen />
  if (!destination) {
    return (
      <div className="text-center py-24">
        <p className="text-brand-600 mb-4">{error || 'Destination not found'}</p>
        <Link to="/destinations" className="text-brand-700 font-medium hover:underline">← Back to destinations</Link>
      </div>
    )
  }

  return (
    <div>
      {/* Hero banner */}
      <div className="relative h-72 sm:h-96 overflow-hidden">
        <CityImage
          city={destination.city}
          alt={destination.city}
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-brand-900/80 via-brand-900/30 to-transparent" />
        <div className="absolute bottom-0 inset-x-0 p-6 sm:p-10 max-w-7xl mx-auto">
          <Link to="/destinations" className="inline-flex items-center gap-1.5 text-white/70 hover:text-white text-sm mb-4 transition-colors">
            <ArrowLeft className="w-4 h-4" />
            All destinations
          </Link>
          <h1 className="font-display text-4xl sm:text-5xl font-bold text-white">{destination.city}</h1>
          <p className="text-white/80 flex items-center gap-2 mt-2">
            <MapPin className="w-4 h-4" />
            {destination.country}
          </p>
          <div className="flex gap-4 mt-4">
            <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/15 backdrop-blur text-white text-sm">
              <Heart className="w-4 h-4 text-sunset-400" />
              Family score {destination.family_friendliness_score.toFixed(0)}
            </span>
            <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/15 backdrop-blur text-white text-sm">
              <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
              Popularity {destination.popularity_score.toFixed(0)}
            </span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="sticky top-16 z-40 glass border-b border-brand-100 shadow-soft">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex gap-1 overflow-x-auto py-2 scrollbar-hide">
            {tabs.map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => {
                  setTab(key)
                  if (key === 'dates' && !datesSearched && datesOrigin.trim()) loadCheapestDates()
                  if (key === 'budget' && !budgetResult) loadBudget()
                }}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
                  tab === key
                    ? 'bg-brand-500 text-white shadow-soft'
                    : 'text-brand-600 hover:bg-brand-50'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 px-4 py-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm">{error}</div>
        )}

        {/* Overview */}
        {tab === 'overview' && (
          <FadeIn>
            <p className="text-brand-700 text-lg leading-relaxed mb-8 max-w-3xl">{destination.description}</p>

            <div className="grid lg:grid-cols-2 gap-8">
              <div>
                <h2 className="font-display text-2xl font-bold text-brand-900 mb-4 flex items-center gap-2">
                  <Ticket className="w-6 h-6 text-brand-500" />
                  Top Attractions
                </h2>
                <div className="space-y-3">
                  {attractions.map((a) => (
                    <div key={a.id} className="glass rounded-xl p-4 flex justify-between items-start gap-4">
                      <div>
                        <h3 className="font-semibold text-brand-900">{a.name}</h3>
                        <p className="text-xs text-brand-500 mt-0.5">{a.category} · Ages {a.min_age}–{a.max_age}</p>
                        {a.description && <p className="text-sm text-brand-600 mt-1">{a.description}</p>}
                      </div>
                      <span className="text-sm font-semibold text-brand-700 whitespace-nowrap">
                        {a.price === 0 ? 'Free' : `€${a.price}`}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h2 className="font-display text-2xl font-bold text-brand-900 mb-4 flex items-center gap-2">
                  <Bed className="w-6 h-6 text-brand-500" />
                  Hotels
                </h2>
                {hotelsLoading && <LoadingSpinner message="Finding hotels..." />}
                {hotelsError && (
                  <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-3 mb-3">
                    {hotelsError}
                  </p>
                )}
                {!hotelsLoading && hotels.length > 0 && (
                  <div className="space-y-3">
                    {hotels.map((h, i) => <HotelCard key={i} hotel={h} />)}
                  </div>
                )}
                {!hotelsLoading && !hotelsError && hotels.length === 0 && (
                  <p className="text-sm text-brand-500 text-center py-6">No hotels found for these dates.</p>
                )}
              </div>
            </div>
          </FadeIn>
        )}

        {/* Itinerary */}
        {tab === 'itinerary' && (
          <FadeIn>
            <div className="glass rounded-2xl p-6 mb-8 max-w-lg">
              <h2 className="font-semibold text-brand-900 mb-4">Generate your itinerary</h2>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="text-sm text-brand-600 mb-1 block">Duration (days)</label>
                  <input type="number" value={duration} onChange={(e) => setDuration(parseInt(e.target.value) || 1)} min={1} max={30}
                    className="w-full px-3 py-2 rounded-xl border border-brand-200 bg-white" />
                </div>
                <div>
                  <label className="text-sm text-brand-600 mb-1 block">Budget (EUR)</label>
                  <input type="number" value={itineraryBudget} onChange={(e) => setItineraryBudget(parseFloat(e.target.value) || 0)} min={100}
                    className="w-full px-3 py-2 rounded-xl border border-brand-200 bg-white" />
                </div>
              </div>
              <button onClick={generateItinerary} disabled={itineraryLoading}
                className="w-full py-3 bg-brand-500 text-white font-semibold rounded-xl hover:bg-brand-600 disabled:opacity-60 flex items-center justify-center gap-2">
                <Sparkles className="w-4 h-4" />
                {itineraryLoading ? 'Generating...' : 'Generate itinerary'}
              </button>
            </div>

            {itinerary && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h2 className="font-display text-2xl font-bold text-brand-900">Your {duration}-day plan</h2>
                  <span className="flex items-center gap-1.5 text-brand-700 font-semibold">
                    <Euro className="w-4 h-4" />
                    €{itineraryCost.toFixed(0)} total
                  </span>
                </div>
                <div className="space-y-4">
                  {itinerary.map((day) => (
                    <div key={day.day_number} className="glass rounded-2xl p-6">
                      <h3 className="font-display text-xl font-semibold text-brand-900 mb-4">{day.title}</h3>
                      <div className="space-y-3">
                        {day.items.map((item, i) => (
                          <div key={i} className="flex gap-4 items-start">
                            <div className="flex items-center gap-1.5 text-xs font-medium text-brand-500 bg-brand-50 px-2.5 py-1 rounded-lg whitespace-nowrap">
                              <Clock className="w-3 h-3" />
                              {item.time}
                            </div>
                            <div className="flex-1">
                              <p className="font-medium text-brand-800">{item.activity}</p>
                              {item.description && <p className="text-sm text-brand-600 mt-0.5">{item.description}</p>}
                            </div>
                            {item.estimated_cost > 0 && (
                              <span className="text-sm text-brand-600">€{item.estimated_cost}</span>
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
        )}

        {/* Child activities */}
        {tab === 'activities' && (
          <FadeIn>
            <div className="glass rounded-2xl p-6 mb-8 max-w-lg">
              <h2 className="font-semibold text-brand-900 mb-4 flex items-center gap-2">
                <Baby className="w-5 h-5 text-brand-500" />
                Find activities for your child
              </h2>
              <div className="mb-4">
                <label className="text-sm text-brand-600 mb-1 block">Child's age</label>
                <input type="number" value={childAge} onChange={(e) => setChildAge(parseInt(e.target.value) || 0)} min={0} max={17}
                  className="w-full px-3 py-2 rounded-xl border border-brand-200 bg-white" />
              </div>
              <div className="mb-4">
                <label className="text-xs text-brand-500 font-medium mb-2 block">
                  Interests {childInterests.length > 0 && <span className="text-brand-400">({childInterests.length} selected)</span>}
                </label>
                <div className="flex flex-wrap gap-2">
                  {INTEREST_OPTIONS.map((interest) => (
                    <button key={interest} onClick={() => {
                      setChildActivities([])
                      setChildActivitiesSearched(false)
                      setChildInterests(
                        childInterests.includes(interest)
                          ? childInterests.filter(x => x !== interest)
                          : [...childInterests, interest]
                      )
                    }} className={`px-3 py-1 rounded-full text-xs font-medium ${
                      childInterests.includes(interest) ? 'bg-brand-500 text-white' : 'bg-brand-100 text-brand-700'
                    }`}>
                      {interest.replace('_', ' ')}
                    </button>
                  ))}
                </div>
                {childInterests.length === 0 && (
                  <p className="text-xs text-brand-500 mt-2">Select at least one interest to filter activities.</p>
                )}
              </div>
              <button onClick={loadChildActivities} disabled={childInterests.length === 0 || childActivitiesLoading}
                className="w-full py-3 bg-brand-500 text-white font-semibold rounded-xl hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed">
                {childActivitiesLoading ? 'Searching...' : 'Find matching activities'}
              </button>
            </div>

            {childActivitiesLoading && <LoadingSpinner message="Finding activities..." />}

            {childActivitiesSearched && !childActivitiesLoading && childActivities.length === 0 && (
              <p className="text-sm text-brand-600 text-center py-8 glass rounded-xl">
                No activities match {childInterests.map((i) => i.replace('_', ' ')).join(', ')} for this destination.
                Try another interest or age.
              </p>
            )}

            <div className="grid sm:grid-cols-2 gap-4">
              {childActivities.map((a) => (
                <div key={a.id} className="glass rounded-xl p-5">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-semibold text-brand-900">{a.name}</h3>
                    <span className="text-xs font-bold px-2 py-1 rounded-full bg-brand-500/10 text-brand-700">
                      {a.match_score.toFixed(0)}% match
                    </span>
                  </div>
                  <p className="text-xs text-brand-500 mb-2">{a.category}</p>
                  {a.description && <p className="text-sm text-brand-600 mb-2">{a.description}</p>}
                  <p className="text-xs text-brand-500 italic">{a.reason}</p>
                  <p className="text-sm font-semibold text-brand-700 mt-2">{a.price === 0 ? 'Free' : `€${a.price}`}</p>
                </div>
              ))}
            </div>
          </FadeIn>
        )}

        {/* Cheapest dates */}
        {tab === 'dates' && (
          <FadeIn>
            <h2 className="font-display text-2xl font-bold text-brand-900 mb-6">Best times to visit</h2>

            <div className="glass rounded-2xl p-6 mb-8 max-w-lg space-y-4">
              <div>
                <label className="text-sm text-brand-600 mb-2 block">Departing from</label>
                <OriginLocationInput value={datesOrigin} onChange={setDatesOrigin} />
              </div>
              <div>
                <label className="text-sm text-brand-600 mb-1 block">Travelers</label>
                <input
                  type="number"
                  value={datesPartySize}
                  onChange={(e) => setDatesPartySize(Math.max(1, parseInt(e.target.value) || 1))}
                  min={1}
                  max={9}
                  className="w-full px-3 py-2 rounded-xl border border-brand-200 bg-white"
                />
              </div>
              <button
                onClick={loadCheapestDates}
                disabled={datesLoading || !datesOrigin.trim()}
                className="w-full py-3 bg-brand-500 text-white font-semibold rounded-xl hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {datesLoading ? 'Loading live prices...' : 'Compare seasons'}
              </button>
              {!datesOrigin.trim() && (
                <p className="text-xs text-brand-500">Flight prices need your departure city or country.</p>
              )}
            </div>

            {datesOriginMessage && (
              <p className="text-sm text-brand-600 mb-4 px-4 py-3 rounded-xl bg-brand-50 border border-brand-100">
                {datesOriginMessage}
              </p>
            )}

            {datesLoading && <LoadingSpinner message="Fetching live flight and hotel prices..." />}

            {datesSearched && !datesLoading && cheapestPeriods.length > 0 && (
              <div className="grid sm:grid-cols-2 gap-4">
                {cheapestPeriods.map((p, i) => (
                  <div key={p.season} className={`glass rounded-2xl p-6 ${i === 0 ? 'ring-2 ring-brand-400' : ''}`}>
                    {i === 0 && <span className="text-xs font-bold text-brand-500 uppercase tracking-wider">Best value</span>}
                    <h3 className="font-display text-xl font-semibold text-brand-900 capitalize mt-1">{p.season}</h3>
                    <p className="text-sm text-brand-600 mb-4">
                      {MONTHS[p.month_start - 1]} – {MONTHS[p.month_end - 1]}
                    </p>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-brand-600">Flights (party)</span>
                        <span className="font-semibold">
                          {p.avg_flight_price > 0 ? `€${p.avg_flight_price.toFixed(0)}` : '—'}
                        </span>
                      </div>
                      <div className="flex justify-between"><span className="text-brand-600">Accommodation/night</span><span className="font-semibold">€{p.avg_accommodation_price.toFixed(0)}</span></div>
                      <div className="flex justify-between"><span className="text-brand-600">Weather score</span><span className="font-semibold">{p.weather_score.toFixed(0)}%</span></div>
                      <div className="flex justify-between pt-2 border-t border-brand-100"><span className="font-medium text-brand-800">Total price</span><span className="font-bold text-brand-900">€{p.estimated_total.toFixed(0)}</span></div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {datesSearched && !datesLoading && cheapestPeriods.length === 0 && (
              <p className="text-sm text-brand-600 text-center py-8 glass rounded-xl">
                Could not load seasonal prices. Check your departure city and try again.
              </p>
            )}
          </FadeIn>
        )}

        {/* Budget */}
        {tab === 'budget' && (
          <FadeIn>
            {!budgetResult ? (
              <LoadingSpinner message="Calculating budget options..." />
            ) : (
              <div>
                <div className={`glass rounded-2xl p-6 mb-8 ${budgetResult.within_budget ? 'ring-2 ring-emerald-400' : 'ring-2 ring-sunset-400'}`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-brand-600">Current estimate</p>
                      <p className="text-3xl font-bold text-brand-900">€{budgetResult.current_estimate.toFixed(0)}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-brand-600">Your budget</p>
                      <p className="text-3xl font-bold text-brand-900">€{budgetResult.budget.toFixed(0)}</p>
                    </div>
                  </div>
                  <p className={`mt-3 text-sm font-medium ${budgetResult.within_budget ? 'text-emerald-600' : 'text-sunset-600'}`}>
                    {budgetResult.within_budget ? '✓ Within budget' : '⚠ Over budget — see alternatives below'}
                  </p>
                </div>

                {budgetResult.alternatives.length > 0 && (
                  <div>
                    <h2 className="font-display text-xl font-bold text-brand-900 mb-4">Ways to save</h2>
                    <div className="space-y-3">
                      {budgetResult.alternatives.map((alt, i) => (
                        <div key={i} className="glass rounded-xl p-5 flex justify-between items-center gap-4">
                          <div>
                            <p className="font-medium text-brand-900">{alt.description}</p>
                            <p className="text-xs text-brand-500 capitalize mt-0.5">{alt.type.replace('_', ' ')}</p>
                          </div>
                          <div className="text-right whitespace-nowrap">
                            <p className="text-sm font-bold text-emerald-600">Save €{alt.estimated_savings.toFixed(0)}</p>
                            <p className="text-xs text-brand-600">New total: €{alt.new_total.toFixed(0)}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </FadeIn>
        )}
      </div>
    </div>
  )
}
