import { useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight,
  ChevronDown,
  Euro,
  MapPin,
  Star,
  TrendingUp,
} from 'lucide-react'
import type { DestinationRecommendation } from '../../types'
import { normalizeFlightSummary } from '../../utils/flight'
import CityImage from '../ui/CityImage'
import FlightTicketCard from './FlightTicketCard'
import HotelCard from './HotelCard'
import ScoreBreakdownChart from './ScoreBreakdownChart'

interface Props {
  rec: DestinationRecommendation
  rank: number
  budget?: number
  startDate?: string
  endDate?: string
  partySize?: number
  originLocation?: string
}

function CollapsibleSection({
  title,
  defaultOpen = false,
  children,
}: {
  title: string
  defaultOpen?: boolean
  children: ReactNode
}) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <div className="rounded-xl border border-brand-100 overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between gap-2 px-4 py-2.5 bg-brand-50/60 text-sm font-semibold text-brand-700 hover:bg-brand-50 transition-colors"
      >
        {title}
        <ChevronDown className={`w-4 h-4 shrink-0 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && <div className="p-4 space-y-4 border-t border-brand-100">{children}</div>}
    </div>
  )
}

export default function RecommendationCard({
  rec,
  rank,
  budget,
  startDate,
  endDate,
  partySize,
  originLocation,
}: Props) {
  const flight = normalizeFlightSummary(rec.flight)

  return (
    <article className="glass rounded-2xl overflow-hidden shadow-card hover:shadow-glow transition-all duration-300 group">
      <div className="relative h-40 sm:h-44 overflow-hidden">
        <CityImage
          city={rec.city}
          alt={rec.city}
          className="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-brand-900/75 via-brand-900/20 to-transparent" />
        <div className="absolute top-3 left-3 w-9 h-9 rounded-lg bg-white/90 backdrop-blur flex items-center justify-center font-display text-sm font-bold text-brand-700 shadow-soft">
          #{rank}
        </div>
        <div className="absolute bottom-3 left-4 right-4 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h3 className="font-display text-xl sm:text-2xl font-semibold text-white">{rec.city}</h3>
            <p className="text-white/85 text-sm flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5" />
              {rec.country}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/90 text-brand-700 text-xs font-semibold">
              <TrendingUp className="w-3.5 h-3.5" />
              {rec.final_score.toFixed(1)}
            </span>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/90 text-sunset-600 text-xs font-semibold">
              <Euro className="w-3.5 h-3.5" />
              {rec.estimated_total_cost.toFixed(0)} total
            </span>
          </div>
        </div>
      </div>

      <div className="p-4 sm:p-5 space-y-4">
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="rounded-lg bg-sand-50 px-2 py-2">
            <p className="text-[10px] uppercase tracking-wide text-brand-500 font-medium">Flights</p>
            <p className="text-sm font-semibold text-brand-900">
              {rec.flight_cost > 0 ? `€${rec.flight_cost.toFixed(0)}` : '—'}
            </p>
          </div>
          <div className="rounded-lg bg-sand-50 px-2 py-2">
            <p className="text-[10px] uppercase tracking-wide text-brand-500 font-medium">Stay</p>
            <p className="text-sm font-semibold text-brand-900">€{rec.accommodation_cost.toFixed(0)}</p>
          </div>
          <div className="rounded-lg bg-sand-50 px-2 py-2">
            <p className="text-[10px] uppercase tracking-wide text-brand-500 font-medium">Activities</p>
            <p className="text-sm font-semibold text-brand-900">€{rec.activity_cost.toFixed(0)}</p>
          </div>
        </div>

        <div className="grid xl:grid-cols-2 gap-4 items-start">
          <div className="min-w-0">
            {flight ? (
              <FlightTicketCard flight={flight} />
            ) : rec.flight_cost > 0 ? (
              <div className="rounded-xl border border-brand-100 bg-brand-50/50 px-4 py-3 text-sm text-brand-600 h-full">
                Flights from €{rec.flight_cost.toFixed(0)} for your party
              </div>
            ) : (
              <div className="rounded-xl border border-dashed border-brand-200 bg-brand-50/30 px-4 py-3 text-sm text-brand-500 h-full">
                Enter a departure city to include flight prices in this estimate.
              </div>
            )}
          </div>

          {rec.accommodation ? (
            <div className="min-w-0 space-y-1.5">
              <p className="text-xs font-semibold text-brand-500 uppercase tracking-wider">
                Top hotel pick
              </p>
              <HotelCard hotel={rec.accommodation} />
            </div>
          ) : (
            <div className="hidden xl:block" />
          )}
        </div>

        <p className="text-brand-700 text-sm leading-relaxed line-clamp-2">{rec.explanation}</p>

        <CollapsibleSection title="Score breakdown & suggested activities">
          <ScoreBreakdownChart breakdown={rec.score_breakdown} compact />
          {rec.suggested_attractions.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-brand-500 uppercase tracking-wider mb-2">
                Suggested for your family
              </p>
              <div className="flex flex-wrap gap-2">
                {rec.suggested_attractions.map((a) => (
                  <span
                    key={a.id}
                    className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-sand-100 text-brand-800 text-xs font-medium"
                  >
                    <Star className="w-3 h-3 text-sunset-500" />
                    {a.name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </CollapsibleSection>

        <Link
          to={`/destinations/${rec.destination_id}`}
          state={{ startDate, endDate, partySize, originLocation, budget }}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-brand-500 text-white text-sm font-semibold hover:bg-brand-600 transition-colors"
        >
          Explore {rec.city}
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    </article>
  )
}
