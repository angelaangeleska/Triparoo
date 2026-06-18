import { useEffect, useRef, useState } from 'react'
import { MapPin, Search } from 'lucide-react'
import { api } from '../../api/client'
import type { ResolvedOrigin } from '../../types'

interface Props {
  value: string
  onChange: (location: string) => void
}

export default function OriginLocationInput({ value, onChange }: Props) {
  const [query, setQuery] = useState(value)
  const [resolved, setResolved] = useState<ResolvedOrigin | null>(null)
  const [loading, setLoading] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout>>()

  useEffect(() => {
    setQuery(value)
  }, [value])

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (query.trim().length < 2) {
      setResolved(null)
      return
    }

    debounceRef.current = setTimeout(async () => {
      setLoading(true)
      try {
        const result = await api.resolveOrigin(query.trim())
        setResolved(result)
      } catch {
        setResolved(null)
      } finally {
        setLoading(false)
      }
    }, 400)

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [query])

  return (
    <div>
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-brand-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            onChange(e.target.value)
          }}
          placeholder="City or country — e.g. Skopje, France, Macedonia"
          className="w-full pl-11 pr-4 py-3 rounded-xl border border-brand-200 bg-white/80 focus:outline-none focus:ring-2 focus:ring-brand-400"
        />
      </div>

      {loading && (
        <p className="text-xs text-brand-500 mt-2 flex items-center gap-1.5">
          <MapPin className="w-3.5 h-3.5 animate-pulse" />
          Looking up flights near {query}...
        </p>
      )}

      {!loading && resolved && query.trim().length >= 2 && (
        <div className="mt-2 px-4 py-3 rounded-xl bg-brand-50 border border-brand-100">
          <p className="text-sm text-brand-800 font-medium">{resolved.message}</p>
          <p className="text-xs text-brand-500 mt-1">
            No need to pick an airport — we handle that automatically.
          </p>
        </div>
      )}

      {!loading && !resolved && query.trim().length >= 2 && (
        <p className="text-xs text-brand-500 mt-2">
          Type a city (Skopje, Lyon) or country (France, Macedonia). Airports are chosen automatically.
        </p>
      )}
    </div>
  )
}
