import { Check, Euro } from 'lucide-react'
import type { TripBudgetResult } from '../../types'

interface Props {
  result: TripBudgetResult
  compact?: boolean
}

export default function SelectedTripBudget({ result, compact }: Props) {
  const overBy = Math.max(0, result.current_estimate - result.budget)

  return (
    <div
      className={`rounded-2xl border p-4 sm:p-5 ${
        result.within_budget
          ? 'border-emerald-200 bg-emerald-50/60'
          : 'border-sunset-200 bg-sunset-50/60'
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-brand-500">Trip total</p>
          <p className="text-2xl sm:text-3xl font-bold text-brand-900 flex items-center gap-1">
            <Euro className="w-5 h-5" />
            {result.current_estimate.toFixed(0)}
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-brand-500">Budget</p>
          <p className="text-lg font-semibold text-brand-800">€{result.budget.toFixed(0)}</p>
        </div>
      </div>

      {!compact && (
        <div className="grid grid-cols-3 gap-2 mb-3 text-center text-sm">
          <div className="rounded-xl bg-white/70 px-2 py-2">
            <p className="text-[10px] uppercase tracking-wide text-brand-500">Flights</p>
            <p className="font-semibold text-brand-900">
              {result.flight_cost > 0 ? `€${result.flight_cost.toFixed(0)}` : '—'}
            </p>
          </div>
          <div className="rounded-xl bg-white/70 px-2 py-2 ring-1 ring-brand-300">
            <p className="text-[10px] uppercase tracking-wide text-brand-500">Stay</p>
            <p className="font-semibold text-brand-900">€{result.accommodation_cost.toFixed(0)}</p>
          </div>
          <div className="rounded-xl bg-white/70 px-2 py-2">
            <p className="text-[10px] uppercase tracking-wide text-brand-500">Activities</p>
            <p className="font-semibold text-brand-900">€{result.activity_cost.toFixed(0)}</p>
          </div>
        </div>
      )}

      {result.selected_accommodation && (
        <p className="text-sm text-brand-700 mb-2 flex items-center gap-1.5">
          <Check className="w-4 h-4 text-emerald-600 shrink-0" />
          <span className="truncate">{result.selected_accommodation.name}</span>
          <span className="text-brand-500 shrink-0">
            · €{result.selected_accommodation.total_price.toFixed(0)} ({result.nights} nights)
          </span>
        </p>
      )}

      <p className={`text-sm font-medium ${result.within_budget ? 'text-emerald-700' : 'text-sunset-700'}`}>
        {result.within_budget
          ? 'This stay fits your budget.'
          : `Over budget by €${overBy.toFixed(0)} — try a cheaper option below.`}
      </p>
    </div>
  )
}
