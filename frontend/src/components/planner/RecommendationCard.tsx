import { Link } from 'react-router-dom'
import { ArrowRight, Euro, MapPin, Star, TrendingUp } from 'lucide-react'
import type { DestinationRecommendation } from '../../types'
import { CITY_IMAGES, DEFAULT_CITY_IMAGE } from '../../types'
import { normalizeFlightSummary } from '../../utils/flight'
import FlightTicketCard from './FlightTicketCard'
import ScoreBreakdownChart from './ScoreBreakdownChart'

interface Props {
  rec: DestinationRecommendation
  rank: number
}

export default function RecommendationCard({ rec, rank }: Props) {
  const image = CITY_IMAGES[rec.city] || DEFAULT_CITY_IMAGE
  const flight = normalizeFlightSummary(rec.flight)

  return (
    <article className="glass rounded-2xl overflow-hidden shadow-card hover:shadow-glow transition-all duration-300 group">
      <div className="grid md:grid-cols-5 gap-0">
        <div className="md:col-span-2 relative h-48 md:h-auto min-h-[200px] overflow-hidden">
          <img
            src={image}
            alt={rec.city}
            className="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-brand-900/60 to-transparent" />
          <div className="absolute top-4 left-4 w-10 h-10 rounded-xl bg-white/90 backdrop-blur flex items-center justify-center font-display text-lg font-bold text-brand-700 shadow-soft">
            #{rank}
          </div>
          <div className="absolute bottom-4 left-4">
            <h3 className="font-display text-2xl font-semibold text-white">{rec.city}</h3>
            <p className="text-white/80 text-sm flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5" />
              {rec.country}
            </p>
          </div>
        </div>

        <div className="md:col-span-3 p-6 space-y-5">
          <div className="flex flex-wrap gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-500/10 text-brand-700 text-sm font-semibold">
              <TrendingUp className="w-4 h-4" />
              Score {rec.final_score.toFixed(1)}
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-sunset-500/10 text-sunset-600 text-sm font-semibold">
              <Euro className="w-4 h-4" />
              €{rec.estimated_total_cost.toFixed(0)} est.
            </div>
          </div>

          {flight ? (
            <FlightTicketCard flight={flight} />
          ) : rec.flight_cost > 0 ? (
            <div className="rounded-xl border border-brand-100 bg-brand-50/50 px-4 py-3 text-sm text-brand-600">
              Flights estimated at €{rec.flight_cost.toFixed(0)} for your party
            </div>
          ) : null}

          <div className="flex flex-wrap gap-2 text-xs text-brand-600">
            {rec.flight_cost > 0 && (
              <span className="px-2.5 py-1 rounded-lg bg-sand-100">Flights €{rec.flight_cost.toFixed(2)}</span>
            )}
            <span className="px-2.5 py-1 rounded-lg bg-sand-100">Stay €{rec.accommodation_cost.toFixed(0)}</span>
            <span className="px-2.5 py-1 rounded-lg bg-sand-100">Activities €{rec.activity_cost.toFixed(0)}</span>
          </div>

          <p className="text-brand-700 text-sm leading-relaxed">{rec.explanation}</p>

          {rec.suggested_attractions.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-brand-500 uppercase tracking-wider mb-2">Suggested for your family</p>
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

          <div className="grid sm:grid-cols-2 gap-4 pt-2">
            <ScoreBreakdownChart breakdown={rec.score_breakdown} />
          </div>

          <Link
            to={`/destinations/${rec.destination_id}`}
            className="inline-flex items-center gap-2 text-sm font-semibold text-brand-600 hover:text-brand-800 transition-colors group/link"
          >
            Explore {rec.city}
            <ArrowRight className="w-4 h-4 group-hover/link:translate-x-1 transition-transform" />
          </Link>
        </div>
      </div>
    </article>
  )
}
