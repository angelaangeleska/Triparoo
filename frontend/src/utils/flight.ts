import type { FlightLegSummary, FlightSummary } from '../types'

/** Accept both new nested flight payloads and legacy flat summaries from older APIs. */
export function normalizeFlightSummary(raw: unknown): FlightSummary | null {
  if (!raw || typeof raw !== 'object') return null

  const data = raw as Record<string, unknown>

  if (data.outbound && typeof data.outbound === 'object') {
    const flight = data as unknown as FlightSummary
    return {
      ...flight,
      alternatives: flight.alternatives ?? [],
      currency: flight.currency || 'EUR',
      party_size: flight.party_size || 1,
      trip_type: flight.trip_type || (flight.return_flight ? 'round_trip' : 'one_way'),
    }
  }

  // Legacy flat shape
  if (typeof data.airline === 'string' && typeof data.departure_date === 'string') {
    const price = Number(data.price) || 0
    const pricePerPerson = Number(data.price_per_person) || price
    const leg: FlightLegSummary = {
      airline: String(data.airline),
      airline_code: String(data.origin_iata || 'XX').slice(0, 2),
      flight_number: String(data.origin_iata || '—'),
      origin_iata: String(data.origin_iata || ''),
      origin_airport: String(data.origin_city || data.origin_iata || ''),
      origin_city: String(data.origin_city || ''),
      destination_iata: String(data.destination_iata || ''),
      destination_airport: String(data.destination_city || data.destination_iata || ''),
      destination_city: String(data.destination_city || ''),
      departure_date: String(data.departure_date),
      arrival_date: String(data.departure_date),
      duration_minutes: 0,
      duration: '—',
      cabin_class: 'Economy',
      stops: 0,
      stops_label: 'Direct',
      price,
      price_per_person: pricePerPerson,
      currency: 'EUR',
      seats_remaining: Number(data.seats_remaining) || 0,
      baggage: '',
      direction: 'outbound',
      source: String(data.source || 'legacy'),
    }
    return {
      currency: 'EUR',
      total_price: price,
      total_price_per_person: pricePerPerson,
      party_size: 1,
      trip_type: 'one_way',
      outbound: leg,
      return_flight: null,
      alternatives: [],
      source: leg.source,
    }
  }

  return null
}
