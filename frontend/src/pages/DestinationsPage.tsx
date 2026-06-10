import { useEffect, useState } from 'react'
import { Globe, Search } from 'lucide-react'
import { api } from '../api/client'
import type { Destination } from '../types'
import DestinationCard from '../components/destinations/DestinationCard'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import FadeIn from '../components/ui/FadeIn'

export default function DestinationsPage() {
  const [destinations, setDestinations] = useState<Destination[]>([])
  const [filtered, setFiltered] = useState<Destination[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.destinations()
      .then((data) => {
        setDestinations(data)
        setFiltered(data)
      })
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    const q = search.toLowerCase()
    setFiltered(
      destinations.filter(
        (d) =>
          d.city?.toLowerCase().includes(q) ||
          d.country?.toLowerCase().includes(q) ||
          d.description?.toLowerCase().includes(q),
      ),
    )
  }, [search, destinations])

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <FadeIn>
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-brand-500/10 text-brand-700 text-sm font-medium mb-4">
            <Globe className="w-4 h-4" />
            European Destinations
          </div>
          <h1 className="font-display text-4xl sm:text-5xl font-bold text-brand-900 mb-3">
            Explore destinations
          </h1>
          <p className="text-brand-600 text-lg max-w-xl mx-auto">
            Hand-picked family-friendly cities across Europe with attractions, accommodations, and seasonal insights.
          </p>
        </div>
      </FadeIn>

      <FadeIn delay={0.1}>
        <div className="relative max-w-md mx-auto mb-10">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-brand-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search cities or countries..."
            className="w-full pl-12 pr-4 py-3.5 rounded-2xl border border-brand-200 bg-white/80 shadow-soft focus:outline-none focus:ring-2 focus:ring-brand-400"
          />
        </div>
      </FadeIn>

      {loading ? (
        <LoadingSpinner message="Loading destinations..." />
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 text-brand-600">
          No destinations match your search.
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map((dest, i) => (
            <FadeIn key={dest.id} delay={i * 0.05}>
              <DestinationCard destination={dest} />
            </FadeIn>
          ))}
        </div>
      )}
    </div>
  )
}
