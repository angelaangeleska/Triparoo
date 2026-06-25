import type {
  Accommodation,
  AccommodationSummary,
  Airport,
  AirportSearchResult,
  Attraction,
  BudgetAlternative,
  CheapestPeriod,
  ChildActivity,
  Destination,
  DestinationRecommendation,
  ItineraryDay,
  ResolvedOrigin,
  TripMember,
  User,
} from '../types'

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1'

function formatApiError(detail: unknown): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'object' && item !== null && 'msg' in item) {
          const field = 'loc' in item && Array.isArray(item.loc) ? item.loc.at(-1) : null
          return field ? `${field}: ${item.msg}` : String(item.msg)
        }
        return JSON.stringify(item)
      })
      .join('. ')
  }
  if (detail && typeof detail === 'object') return JSON.stringify(detail)
  return 'Something went wrong. Please try again.'
}

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

function getToken(): string | null {
  return localStorage.getItem('access_token')
}

function clearSession() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  window.dispatchEvent(new CustomEvent('auth:session-expired'))
}

async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) return false

  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
    if (!res.ok) return false
    const data = (await res.json()) as { access_token: string; refresh_token: string }
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    return true
  } catch {
    return false
  }
}

function friendlyAuthMessage(status: number, detail: string): string {
  if (status === 401) {
    if (detail.toLowerCase().includes('invalid token') || detail.toLowerCase().includes('not authenticated')) {
      return 'Your session expired. Please sign in again.'
    }
    return 'Please sign in to continue.'
  }
  return detail
}

async function request<T>(path: string, options: RequestInit = {}, allowRefresh = true): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  let res: Response
  try {
    res = await fetch(`${API_BASE}${path}`, { ...options, headers })
  } catch {
    throw new ApiError('Cannot reach the API. Is the backend running on port 8000?', 0)
  }

  if (res.status === 401 && allowRefresh && !path.startsWith('/auth/')) {
    const refreshed = await refreshAccessToken()
    if (refreshed) {
      return request<T>(path, options, false)
    }
    clearSession()
    const body = await res.json().catch(() => ({ detail: 'Not authenticated' }))
    const detail = formatApiError(body.detail ?? body)
    throw new ApiError(friendlyAuthMessage(401, detail), 401)
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    const detail = formatApiError(body.detail ?? body)
    throw new ApiError(friendlyAuthMessage(res.status, detail), res.status)
  }

  if (res.status === 204) return undefined as T
  return res.json()
}

export type CheapestDestinationResult = {
  destination_id: number
  city: string
  country: string
  estimated_total_cost: number
  flight_cost: number
  accommodation_cost: number
  activity_cost: number
  nights: number
}

export const api = {
  register: (data: { email: string; username: string; password: string; first_name?: string; last_name?: string }) =>
    request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),

  login: (email: string, password: string) =>
    request<{ access_token: string; refresh_token: string }>('/auth/login/json', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  me: () => request<User>('/auth/me'),

  destinations: () => request<Destination[]>('/destinations'),

  destination: (id: number) => request<Destination>(`/destinations/${id}`),

  airports: () => request<Airport[]>('/airports'),

  searchAirports: (q: string) =>
    request<AirportSearchResult[]>(`/airports/search?q=${encodeURIComponent(q)}`),

  resolveOrigin: (q: string) =>
    request<ResolvedOrigin>(`/trip-planner/resolve-origin?q=${encodeURIComponent(q)}`),

  attractions: (destinationId?: number) =>
    request<Attraction[]>(`/attractions${destinationId ? `?destination_id=${destinationId}` : ''}`),

  accommodations: (destinationId?: number) =>
    request<Accommodation[]>(`/accommodations${destinationId ? `?destination_id=${destinationId}` : ''}`),

  searchHotels: (city: string, checkIn: string, checkOut: string, adults = 2, children = 0, country = '') =>
    request<AccommodationSummary[]>(
      `/trip-planner/hotels?city=${encodeURIComponent(city)}&check_in=${checkIn}&check_out=${checkOut}&adults=${adults}&children=${children}${country ? `&country=${encodeURIComponent(country)}` : ''}`
    ),

  recommend: (data: {
    members: TripMember[]
    budget: number
    start_date?: string
    end_date?: string
    origin_location?: string
    origin_airport_id?: number
    preferred_month?: number
  }) =>
    request<{ origin_message?: string; recommendations: DestinationRecommendation[] }>(
      '/trip-planner/recommend',
      { method: 'POST', body: JSON.stringify(data) },
    ),

  cheapestDestinations: (data: {
    origin_airport_id: number
    budget: number
    start_date: string
    end_date: string
    party_size: number
  }) =>
    request<{ results: CheapestDestinationResult[] }>('/trip-planner/cheapest-destinations', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  cheapestDates: (data: {
    destination_id: number
    origin_location?: string
    origin_airport_id?: number
    party_size: number
  }) =>
    request<{
      destination_id: number
      city: string
      country: string
      cheapest_periods: CheapestPeriod[]
      origin_message?: string
    }>('/trip-planner/cheapest-dates', { method: 'POST', body: JSON.stringify(data) }),

  itinerary: (data: {
    destination_id: number
    members: TripMember[]
    duration_days: number
    budget: number
    start_date?: string
  }) =>
    request<{
      destination_id: number
      city: string
      country: string
      total_estimated_cost: number
      days: ItineraryDay[]
    }>('/trip-planner/itinerary', { method: 'POST', body: JSON.stringify(data) }),

  childActivities: (data: {
    destination_id: number
    age: number
    gender?: string
    interests: string[]
  }) =>
    request<{ activities: ChildActivity[] }>('/trip-planner/child-activities', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  budgetOptimize: (data: {
    destination_id: number
    origin_location?: string
    origin_airport_id?: number
    members: TripMember[]
    budget: number
    start_date: string
    end_date: string
  }) =>
    request<{
      current_estimate: number
      budget: number
      within_budget: boolean
      alternatives: BudgetAlternative[]
    }>('/trip-planner/budget-optimize', { method: 'POST', body: JSON.stringify(data) }),
    
    chat: (data: {
    message: string
    history: { role: string; content: string }[]
  }) =>
    request<{ response: string }>('/chat', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
}

export { ApiError }
