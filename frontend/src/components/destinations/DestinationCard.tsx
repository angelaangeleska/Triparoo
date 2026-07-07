import { Link } from 'react-router-dom'
import { Heart, MapPin, Plane, Star } from 'lucide-react'
import type { Destination } from '../../types'
import CityImage from '../ui/CityImage'

interface Props {
  destination: Destination
}

export default function DestinationCard({ destination }: Props) {
  const hasLivePrices = destination.flight_price != null || destination.hotel_price != null

  return (
    <Link
      to={`/destinations/${destination.id}`}
      className="group block glass rounded-2xl overflow-hidden shadow-soft hover:shadow-card transition-all duration-300 hover:-translate-y-1"
    >
      <div className="relative h-52 overflow-hidden">
        {destination.thumbnail ? (
          <img
            src={destination.thumbnail}
            alt={destination.city}
            className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
          />
        ) : (
          <CityImage
            city={destination.city || ''}
            alt={destination.city}
            className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
          />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-brand-900/70 via-transparent to-transparent" />
        {destination.source === 'serpapi' && (
          <span className="absolute top-3 right-3 px-2 py-1 rounded-full bg-white/90 text-brand-700 text-xs font-medium">
            Live prices
          </span>
        )}
        <div className="absolute bottom-4 left-4 right-4">
          <h3 className="font-display text-2xl font-semibold text-white">{destination.city}</h3>
          <p className="text-white/80 text-sm flex items-center gap-1 mt-0.5">
            <MapPin className="w-3.5 h-3.5" />
            {destination.country}
          </p>
        </div>
      </div>
      <div className="p-5">
        <p className="text-sm text-brand-600 line-clamp-2 leading-relaxed mb-4">
          {destination.description}
        </p>
        {hasLivePrices && (
          <div className="flex flex-wrap gap-2 mb-4 text-xs">
            {destination.flight_price != null && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-brand-50 text-brand-700 border border-brand-100">
                <Plane className="w-3 h-3" />
                Flights from €{Math.round(destination.flight_price)}
              </span>
            )}
            {destination.hotel_price != null && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-brand-50 text-brand-700 border border-brand-100">
                Stays from €{Math.round(destination.hotel_price)}/night
              </span>
            )}
          </div>
        )}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-sm">
            <Heart className="w-4 h-4 text-sunset-500" />
            <span className="font-semibold text-brand-800">{destination.family_friendliness_score.toFixed(0)}</span>
            <span className="text-brand-500">family score</span>
          </div>
          <div className="flex items-center gap-1 text-sm text-brand-600">
            <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
            {destination.popularity_score.toFixed(0)}
          </div>
        </div>
      </div>
    </Link>
  )
}
