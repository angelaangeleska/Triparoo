import { useCallback, useEffect, useRef, useState } from 'react'
import { MapPin, Plane, Search, X } from 'lucide-react'
import { api } from '../../api/client'
import type { AirportSearchResult } from '../../types'

const MATCH_LABELS: Record<string, { label: string; className: string }> = {
  direct: { label: 'In city', className: 'bg-brand-500/10 text-brand-700' },
  iata: { label: 'IATA match', className: 'bg-brand-500/10 text-brand-700' },
  closest: { label: 'Nearest', className: 'bg-sunset-500/10 text-sunset-600' },
  country: { label: 'Country', className: 'bg-violet-500/10 text-violet-700' },
}

interface Props {
  value: number | ''
  onChange: (airportId: number | '', label?: string) => void
  placeholder?: string
}

export default function AirportSearchInput({
  value,
  onChange,
  placeholder = 'Search by city, country, or airport code (e.g. Paris, France, CDG)',
}: Props) {
  const [query, setQuery] = useState('')
  const [selectedLabel, setSelectedLabel] = useState('')
  const [results, setResults] = useState<AirportSearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout>>()

  const search = useCallback(async (q: string) => {
    if (q.trim().length < 2) {
      setResults([])
      return
    }
    setLoading(true)
    try {
      const data = await api.searchAirports(q.trim())
      setResults(data)
      setOpen(true)
    } catch {
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (!query || (value && selectedLabel === query)) return

    debounceRef.current = setTimeout(() => search(query), 300)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [query, search, value, selectedLabel])

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const selectAirport = (airport: AirportSearchResult) => {
    const label = `${airport.iata_code} — ${airport.name} (${airport.city_name}, ${airport.country_name})`
    setSelectedLabel(label)
    setQuery(label)
    onChange(airport.id, label)
    setOpen(false)
  }

  const clear = () => {
    setQuery('')
    setSelectedLabel('')
    onChange('', undefined)
    setResults([])
    setOpen(false)
  }

  return (
    <div ref={containerRef} className="relative">
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            if (value) onChange('')
            setOpen(true)
          }}
          onFocus={() => query.length >= 2 && setOpen(true)}
          placeholder={placeholder}
          className="w-full pl-11 pr-10 py-3 rounded-xl border border-brand-200 bg-white/80 focus:outline-none focus:ring-2 focus:ring-brand-400"
        />
        {(query || value) && (
          <button
            type="button"
            onClick={clear}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-brand-400 hover:text-brand-600"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {open && (loading || results.length > 0 || query.length >= 2) && (
        <div className="absolute z-50 mt-2 w-full glass rounded-2xl shadow-card border border-brand-100 overflow-hidden max-h-80 overflow-y-auto">
          {loading && (
            <div className="px-4 py-3 text-sm text-brand-500">Searching airports...</div>
          )}
          {!loading && results.length === 0 && query.length >= 2 && (
            <div className="px-4 py-3 text-sm text-brand-500">
              No airports found. Try a city (e.g. Lyon), country (e.g. France), or IATA code (e.g. CDG).
            </div>
          )}
          {!loading &&
            results.map((airport) => {
              const badge = MATCH_LABELS[airport.match_type] || MATCH_LABELS.direct
              return (
                <button
                  key={`${airport.id}-${airport.match_type}-${airport.distance_km}`}
                  type="button"
                  onClick={() => selectAirport(airport)}
                  className="w-full text-left px-4 py-3 hover:bg-brand-50 border-b border-brand-50 last:border-0 transition-colors"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3 min-w-0">
                      <div className="w-9 h-9 rounded-lg bg-brand-500/10 flex items-center justify-center shrink-0 mt-0.5">
                        <Plane className="w-4 h-4 text-brand-600" />
                      </div>
                      <div className="min-w-0">
                        <p className="font-semibold text-brand-900 truncate">
                          {airport.iata_code} — {airport.name}
                        </p>
                        <p className="text-sm text-brand-600 flex items-center gap-1 mt-0.5">
                          <MapPin className="w-3 h-3 shrink-0" />
                          {airport.city_name}, {airport.country_name}
                        </p>
                        {airport.note && (
                          <p className="text-xs text-brand-500 mt-1">{airport.note}</p>
                        )}
                      </div>
                    </div>
                    <span className={`text-xs font-medium px-2 py-1 rounded-full shrink-0 ${badge.className}`}>
                      {badge.label}
                      {airport.distance_km != null && airport.match_type === 'closest'
                        ? ` · ${airport.distance_km} km`
                        : ''}
                    </span>
                  </div>
                </button>
              )
            })}
        </div>
      )}

      <p className="text-xs text-brand-500 mt-1.5">
        Type a city (Lyon), country (France), or airport code (CDG). Closest airports are suggested when none exist locally.
      </p>
    </div>
  )
}
