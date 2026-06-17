import { useState } from 'react'
import { Bed, ExternalLink, Star, Wifi } from 'lucide-react'
import type { AccommodationSummary } from '../../types'

function formatMoney(amount: number, currency = 'USD') {
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

interface Props {
  hotel: AccommodationSummary
}

export default function HotelCard({ hotel }: Props) {
  const [imageFailed, setImageFailed] = useState(false)
  const primarySource = hotel.booking_sources[0] ?? null
  const bookingUrl = primarySource?.url || hotel.google_url
  const showImage = Boolean(hotel.image_url) && !imageFailed

  return (
    <div className="rounded-xl border border-brand-100 bg-white/80 overflow-hidden">
      <div className="flex gap-0 min-h-[7rem]">
        <div className="w-28 shrink-0 relative bg-brand-50">
          {showImage ? (
            <img
              src={hotel.image_url}
              alt={hotel.name}
              referrerPolicy="no-referrer"
              loading="lazy"
              decoding="async"
              onError={() => setImageFailed(true)}
              className="absolute inset-0 w-full h-full object-cover"
            />
          ) : (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-1 text-brand-300 bg-gradient-to-br from-brand-50 to-sand-100">
              <Bed className="w-7 h-7" />
              <span className="text-[10px] font-medium uppercase tracking-wide">No photo</span>
            </div>
          )}
        </div>

        <div className="flex-1 p-3 min-w-0 space-y-2">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="font-semibold text-brand-900 text-sm truncate">{hotel.name}</p>
              <p className="text-xs text-brand-500">
                {hotel.hotel_class || hotel.type}
                {hotel.rating && (
                  <span className="ml-2 inline-flex items-center gap-0.5 text-amber-600">
                    <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
                    {hotel.rating.toFixed(1)}
                    {hotel.reviews_count && (
                      <span className="text-brand-400 ml-1">({hotel.reviews_count.toLocaleString()})</span>
                    )}
                  </span>
                )}
              </p>
            </div>
            <div className="text-right shrink-0">
              <p className="font-bold text-brand-900 text-sm">
                {formatMoney(hotel.price_per_night, hotel.currency)}
              </p>
              <p className="text-xs text-brand-500">/ night</p>
            </div>
          </div>

          {hotel.amenities.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {hotel.amenities.slice(0, 4).map((a) => (
                <span key={a} className="inline-flex items-center gap-0.5 text-xs px-2 py-0.5 rounded-full bg-brand-50 text-brand-600 border border-brand-100">
                  <Wifi className="w-2.5 h-2.5" />
                  {a}
                </span>
              ))}
            </div>
          )}

          <div className="flex flex-wrap items-center gap-2">
            {hotel.booking_sources.slice(0, 3).map((src) => (
              <a
                key={src.name}
                href={src.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg bg-brand-500 text-white font-medium hover:bg-brand-600 transition-colors"
              >
                {formatMoney(src.total_price, src.currency)} on {src.name}
                <ExternalLink className="w-3 h-3" />
              </a>
            ))}
            {hotel.booking_sources.length === 0 && bookingUrl && (
              <a
                href={bookingUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg bg-brand-500 text-white font-medium hover:bg-brand-600 transition-colors"
              >
                View on Google Hotels
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
