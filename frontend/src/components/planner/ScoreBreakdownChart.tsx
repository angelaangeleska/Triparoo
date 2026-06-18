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
}

export default function ScoreBreakdownChart({ breakdown }: Props) {
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
