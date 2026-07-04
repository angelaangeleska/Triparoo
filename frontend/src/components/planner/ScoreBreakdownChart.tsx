import type { ScoreBreakdown } from '../../types'

const FACTORS: { key: keyof ScoreBreakdown; label: string; color: string }[] = [
  { key: 'child_age', label: 'Child Age Fit', color: 'bg-sunset-500' },
  { key: 'budget', label: 'Budget Match', color: 'bg-brand-500' },
  { key: 'season', label: 'Season', color: 'bg-brand-400' },
  { key: 'popularity', label: 'Popularity', color: 'bg-brand-300' },
  { key: 'family_friendly', label: 'Family Friendly', color: 'bg-emerald-500' },
  { key: 'activity', label: 'Activities', color: 'bg-amber-500' },
  { key: 'weather', label: 'Weather', color: 'bg-sky-500' },
]

interface Props {
  breakdown: ScoreBreakdown
  compact?: boolean
}

export default function ScoreBreakdownChart({ breakdown, compact = false }: Props) {
  if (compact) {
    return (
      <div className="grid sm:grid-cols-2 gap-x-4 gap-y-2">
        {FACTORS.map(({ key, label, color }) => (
          <div key={key} className="flex items-center gap-2 min-w-0">
            <span className="text-xs text-brand-600 font-medium w-24 shrink-0 truncate">{label}</span>
            <div className="flex-1 h-1.5 bg-brand-100 rounded-full overflow-hidden min-w-0">
              <div
                className={`h-full rounded-full ${color}`}
                style={{ width: `${Math.min(breakdown[key], 100)}%` }}
              />
            </div>
            <span className="text-xs text-brand-800 font-semibold w-6 text-right shrink-0">
              {breakdown[key].toFixed(0)}
            </span>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {FACTORS.map(({ key, label, color }) => (
        <div key={key}>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-brand-600 font-medium">{label}</span>
            <span className="text-brand-800 font-semibold">{breakdown[key].toFixed(0)}</span>
          </div>
          <div className="h-2 bg-brand-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${color} transition-all duration-700`}
              style={{ width: `${Math.min(breakdown[key], 100)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}
