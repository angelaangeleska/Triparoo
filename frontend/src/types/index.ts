export interface User {
  id: number
  email: string
  username: string
  first_name?: string
  last_name?: string
  is_active: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface TripMember {
  age: number
  gender?: string
  interests: string[]
}

export interface Destination {
  id: number
  city_id: number
  description?: string
  family_friendliness_score: number
  popularity_score: number
  city?: string
  country?: string
}

export interface Airport {
  id: number
  name: string
  iata_code: string
  city_id: number
  city_name?: string
}

export interface ResolvedOrigin {
  query: string
  location_type: string
  display_name: string
  primary_airport_id?: number
  airport_count: number
  message: string
}

export interface AirportSearchResult {
  id: number
  name: string
  iata_code: string
  city_name: string
  country_name: string
  match_type: 'direct' | 'closest' | 'country' | 'iata'
  distance_km?: number
  note?: string
}

export interface Attraction {
  id: number
  destination_id: number
  name: string
  category: string
  description?: string
  min_age: number
  max_age: number
  price: number
  family_friendly: boolean
  tags: string[]
}

export interface Accommodation {
  id: number
  destination_id: number
  name: string
  type: string
  rating?: number
  price_per_night: number
  family_friendly: boolean
  max_guests: number
}

export interface ScoreBreakdown {
  child_age: number
  budget: number
  season: number
  popularity: number
  family_friendly: number
  activity: number
  weather: number
}

export interface FlightLegSummary {
  airline: string
  airline_code: string
  flight_number: string
  origin_iata: string
  origin_airport: string
  origin_city: string
  destination_iata: string
  destination_airport: string
  destination_city: string
  departure_date: string
  arrival_date: string
  duration_minutes: number
  duration: string
  cabin_class: string
  stops: number
  stops_label: string
  price: number
  price_per_person: number
  currency: string
  seats_remaining: number
  baggage: string
  direction: string
  source: string
  fare_note?: string
}

export interface FlightSummary {
  currency: string
  total_price: number
  total_price_per_person: number
  party_size: number
  trip_type: 'one_way' | 'round_trip'
  outbound: FlightLegSummary
  return_flight?: FlightLegSummary | null
  alternatives: FlightLegSummary[]
  source: string
}

export interface BookingSource {
  name: string
  price_per_night: number
  total_price: number
  currency: string
  url: string
}

export interface AccommodationSummary {
  name: string
  type: string
  hotel_class: string
  rating?: number | null
  reviews_count?: number | null
  price_per_night: number
  total_price: number
  currency: string
  family_friendly: boolean
  image_url: string
  google_url: string
  booking_sources: BookingSource[]
  amenities: string[]
  check_in_time: string
  check_out_time: string
  source: string
}

export interface DestinationRecommendation {
  destination_id: number
  city: string
  country: string
  rule_score: number
  llm_score: number
  final_score: number
  estimated_total_cost: number
  flight_cost: number
  accommodation_cost: number
  activity_cost: number
  flight?: FlightSummary | null
  accommodation?: AccommodationSummary | null
  score_breakdown: ScoreBreakdown
  explanation: string
  suggested_attractions: {
    id: number
    name: string
    category: string
    price: number
    min_age: number
    max_age: number
  }[]
}

export interface ItineraryDay {
  day_number: number
  title: string
  items: {
    time: string
    activity: string
    description?: string
    estimated_cost: number
  }[]
}

export interface ChildActivity {
  id: number
  name: string
  category: string
  description?: string
  price: number
  match_score: number
  reason: string
}

export interface CheapestPeriod {
  season: string
  month_start: number
  month_end: number
  avg_flight_price: number
  avg_accommodation_price: number
  estimated_total: number
  weather_score: number
}

export interface BudgetAlternative {
  type: string
  description: string
  estimated_savings: number
  new_total: number
}

export const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]

export const INTEREST_OPTIONS = [
  'disney', 'science', 'museum', 'art', 'outdoor', 'beach', 'history', 'animals', 'theme_park',
]

export { DEFAULT_CITY_IMAGE, getCityImage, HERO_IMAGE } from '../utils/cityImages'
