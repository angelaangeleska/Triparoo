import { Calendar, Clock, Plane } from 'lucide-react'
import type { FlightLegSummary, FlightSummary } from '../../types'

function formatDateTime(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}

function formatMoney(amount: number, currency = 'EUR') {
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

function FlightLeg({ leg, label }: { leg: FlightLegSummary; label: string }) {
  return (
    <div className="rounded-xl border border-brand-100 bg-white/80 p-4 space-y-3">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-bold uppercase tracking-wider text-brand-500">{label}</span>
        <span className="text-xs px-2 py-0.5 rounded-full bg-brand-100 text-brand-700 font-medium">
          {leg.stops_label}
        </span>
      </div>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-brand-900 text-lg">{leg.airline}</p>
          <p className="text-sm text-brand-600 mt-0.5">
            {leg.airline_code} · {leg.flight_number} · {leg.cabin_class}
          </p>
        </div>
        <div className="text-right">
          <p className="font-display text-xl font-bold text-brand-800">{formatMoney(leg.price, leg.currency)}</p>
          <p className="text-xs text-brand-500">
            {leg.fare_note || `${formatMoney(leg.price_per_person, leg.currency)} / person`}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-[1fr_auto_1fr] gap-2 items-center">
        <div className="min-w-0">
          <p className="text-2xl font-bold text-brand-900">{leg.origin_iata}</p>
          <p className="text-sm text-brand-700 truncate">{leg.origin_city}</p>
          <p className="text-xs text-brand-500 truncate" title={leg.origin_airport}>{leg.origin_airport}</p>
        </div>
        <div className="flex flex-col items-center text-brand-400 px-2 shrink-0">
          <Plane className="w-5 h-5 rotate-90" />
          <span className="text-xs font-medium text-brand-500 mt-1 whitespace-nowrap">{leg.duration}</span>
        </div>
        <div className="min-w-0 text-right">
          <p className="text-2xl font-bold text-brand-900">{leg.destination_iata}</p>
          <p className="text-sm text-brand-700 truncate">{leg.destination_city}</p>
          <p className="text-xs text-brand-500 truncate" title={leg.destination_airport}>{leg.destination_airport}</p>
        </div>
      </div>

      <div className="grid sm:grid-cols-2 gap-2 text-sm text-brand-700">
        <p className="flex items-start gap-2 min-w-0">
          <Calendar className="w-4 h-4 text-brand-400 shrink-0 mt-0.5" />
          <span className="min-w-0">
            <span className="text-brand-500 text-xs block">Departs</span>
            <span className="break-words">{formatDateTime(leg.departure_date)}</span>
          </span>
        </p>
        <p className="flex items-start gap-2 min-w-0">
          <Clock className="w-4 h-4 text-brand-400 shrink-0 mt-0.5" />
          <span className="min-w-0">
            <span className="text-brand-500 text-xs block">Arrives</span>
            <span className="break-words">{formatDateTime(leg.arrival_date)}</span>
          </span>
        </p>
      </div>

    </div>
  )
}

interface Props {
  flight: FlightSummary
}

export default function FlightTicketCard({ flight }: Props) {
  if (!flight?.outbound) return null

  const alternatives = flight.alternatives ?? []

  return (
    <div className="rounded-2xl border border-brand-200 bg-gradient-to-br from-brand-50 via-white to-sand-50 p-4 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-brand-500 uppercase tracking-wider">
          <Plane className="w-4 h-4" />
          Flight details
          {(flight.source === 'db' || flight.source === 'amadeus' || flight.source === 'serpapi') && (
            <span
              className={`normal-case px-2 py-0.5 rounded-full font-bold ${
                flight.source === 'db'
                  ? 'bg-brand-100 text-brand-700'
                  : 'bg-emerald-100 text-emerald-700'
              }`}
            >
              {flight.source === 'db' ? 'Cached prices' : 'Live prices'}
            </span>
          )}
        </div>
        <div className="text-right">
          <p className="font-display text-2xl font-bold text-brand-900">
            {formatMoney(flight.total_price, flight.currency)}
          </p>
          <p className="text-xs text-brand-600">
            {formatMoney(flight.total_price_per_person, flight.currency)} / person · {flight.party_size} travelers ·{' '}
            {flight.trip_type === 'round_trip' ? 'Round trip' : 'One way'}
          </p>
        </div>
      </div>

      <FlightLeg leg={flight.outbound} label="Outbound" />
      {flight.return_flight && <FlightLeg leg={flight.return_flight} label="Return" />}

      {alternatives.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-brand-500 uppercase tracking-wider">Other outbound options</p>
          <div className="space-y-2">
            {alternatives.map((alt) => (
              <div
                key={`${alt.flight_number}-${alt.departure_date}`}
                className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-white/70 border border-brand-100 px-3 py-2 text-sm"
              >
                <div>
                  <span className="font-medium text-brand-900">{alt.airline}</span>
                  <span className="text-brand-600 ml-2">
                    {alt.flight_number} · {formatDateTime(alt.departure_date)}
                  </span>
                </div>
                <span className="font-semibold text-brand-800">{formatMoney(alt.price, alt.currency)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
