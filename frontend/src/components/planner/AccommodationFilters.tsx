import { useEffect, useState } from 'react'
import { Filter, X } from 'lucide-react'
import { api } from '../../api/client'
import type { AccommodationFilterOptions, AccommodationSearchFilters } from '../../types'

interface Props {
  value: AccommodationSearchFilters
  onChange: (filters: AccommodationSearchFilters) => void
  onApply: () => void
  loading?: boolean
}

function toggleItem(list: string[], id: string): string[] {
  return list.includes(id) ? list.filter((x) => x !== id) : [...list, id]
}

function toggleStar(list: number[], star: number): number[] {
  return list.includes(star) ? list.filter((x) => x !== star) : [...list, star]
}

export default function AccommodationFilters({ value, onChange, onApply, loading }: Props) {
  const [options, setOptions] = useState<AccommodationFilterOptions | null>(null)
  const [open, setOpen] = useState(true)

  useEffect(() => {
    api.accommodationFilters().then(setOptions).catch(() => setOptions(null))
  }, [])

  const activeCount =
    value.property_types.length +
    value.amenities.length +
    value.hotel_class.length +
    (value.min_rating ? 1 : 0) +
    (value.free_cancellation ? 1 : 0) +
    (value.stay_kind === 'vacation_rental' ? 1 : 0)

  const clearAll = () => {
    onChange({
      stay_kind: 'hotel',
      property_types: [],
      amenities: [],
      hotel_class: [],
      min_rating: null,
      free_cancellation: false,
    })
  }

  if (!options) return null

  return (
    <div className="glass rounded-2xl p-4 mb-4 border border-brand-100">
      <div className="flex items-center justify-between gap-3 mb-3">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="flex items-center gap-2 text-brand-900 font-semibold"
        >
          <Filter className="w-4 h-4 text-brand-500" />
          Filters
          {activeCount > 0 && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-brand-500 text-white">{activeCount}</span>
          )}
        </button>
        <div className="flex items-center gap-2">
          {activeCount > 0 && (
            <button type="button" onClick={clearAll} className="text-xs text-brand-500 hover:text-brand-700 flex items-center gap-1">
              <X className="w-3 h-3" />
              Clear
            </button>
          )}
          <button
            type="button"
            onClick={onApply}
            disabled={loading}
            className="text-sm px-3 py-1.5 rounded-lg bg-brand-500 text-white font-medium hover:bg-brand-600 disabled:opacity-60"
          >
            {loading ? 'Searching...' : 'Apply'}
          </button>
        </div>
      </div>

      {open && (
        <div className="space-y-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-500 mb-2">Stay type</p>
            <div className="flex flex-wrap gap-2">
              {options.stay_kinds.map((kind) => (
                <label
                  key={kind.id}
                  className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-xl border text-sm cursor-pointer transition-colors ${
                    value.stay_kind === kind.id
                      ? 'border-brand-500 bg-brand-50 text-brand-800'
                      : 'border-brand-200 bg-white text-brand-700 hover:bg-brand-50'
                  }`}
                >
                  <input
                    type="radio"
                    name="stay_kind"
                    className="sr-only"
                    checked={value.stay_kind === kind.id}
                    onChange={() => onChange({ ...value, stay_kind: kind.id, property_types: kind.id === 'vacation_rental' ? [] : value.property_types })}
                  />
                  {kind.label}
                </label>
              ))}
            </div>
          </div>

          {value.stay_kind === 'hotel' && (
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-brand-500 mb-2">Property type</p>
              <div className="flex flex-wrap gap-2">
                {options.property_types.map((pt) => (
                  <label
                    key={pt.id}
                    className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-xl border text-sm cursor-pointer transition-colors ${
                      value.property_types.includes(pt.id)
                        ? 'border-brand-500 bg-brand-50 text-brand-800'
                        : 'border-brand-200 bg-white text-brand-700 hover:bg-brand-50'
                    }`}
                  >
                    <input
                      type="checkbox"
                      className="rounded border-brand-300 text-brand-500 focus:ring-brand-400"
                      checked={value.property_types.includes(pt.id)}
                      onChange={() => onChange({ ...value, property_types: toggleItem(value.property_types, pt.id) })}
                    />
                    {pt.label}
                  </label>
                ))}
              </div>
            </div>
          )}

          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-500 mb-2">Amenities</p>
            <div className="flex flex-wrap gap-2">
              {options.amenities.map((am) => (
                <label
                  key={am.id}
                  className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-xl border text-sm cursor-pointer transition-colors ${
                    value.amenities.includes(am.id)
                      ? 'border-brand-500 bg-brand-50 text-brand-800'
                      : 'border-brand-200 bg-white text-brand-700 hover:bg-brand-50'
                  }`}
                >
                  <input
                    type="checkbox"
                    className="rounded border-brand-300 text-brand-500 focus:ring-brand-400"
                    checked={value.amenities.includes(am.id)}
                    onChange={() => onChange({ ...value, amenities: toggleItem(value.amenities, am.id) })}
                  />
                  {am.label}
                </label>
              ))}
            </div>
          </div>

          {value.stay_kind === 'hotel' && (
            <>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-brand-500 mb-2">Star rating</p>
                <div className="flex flex-wrap gap-2">
                  {options.hotel_classes.map((hc) => (
                    <label
                      key={hc.id}
                      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-xl border text-sm cursor-pointer transition-colors ${
                        value.hotel_class.includes(hc.id)
                          ? 'border-brand-500 bg-brand-50 text-brand-800'
                          : 'border-brand-200 bg-white text-brand-700 hover:bg-brand-50'
                      }`}
                    >
                      <input
                        type="checkbox"
                        className="rounded border-brand-300 text-brand-500 focus:ring-brand-400"
                        checked={value.hotel_class.includes(hc.id)}
                        onChange={() => onChange({ ...value, hotel_class: toggleStar(value.hotel_class, hc.id) })}
                      />
                      {hc.label}
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-brand-500 mb-2">Guest rating</p>
                  <select
                    value={value.min_rating ?? ''}
                    onChange={(e) =>
                      onChange({
                        ...value,
                        min_rating: e.target.value ? Number(e.target.value) : null,
                      })
                    }
                    className="px-3 py-2 rounded-xl border border-brand-200 bg-white text-sm text-brand-800"
                  >
                    <option value="">Any</option>
                    {options.min_ratings.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.label}
                      </option>
                    ))}
                  </select>
                </div>
                <label className="inline-flex items-center gap-2 text-sm text-brand-700 cursor-pointer mt-5">
                  <input
                    type="checkbox"
                    className="rounded border-brand-300 text-brand-500 focus:ring-brand-400"
                    checked={value.free_cancellation}
                    onChange={(e) => onChange({ ...value, free_cancellation: e.target.checked })}
                  />
                  Free cancellation
                </label>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
