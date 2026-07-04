import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { Calendar, Euro, History, Sparkles, Users } from 'lucide-react'
import { useTripHistory } from '../api/hooks'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardContent } from '../components/ui/Card'
import { Skeleton } from '../components/ui/Skeleton'
import FadeIn from '../components/ui/FadeIn'

export default function MyTripsPage() {
  const { t, i18n } = useTranslation()
  const { data: trips, isLoading } = useTripHistory()

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <FadeIn>
        <div className="mb-10">
          <h1 className="font-display text-4xl font-bold text-brand-900 dark:text-white mb-2 flex items-center gap-3">
            <History className="w-8 h-8 text-brand-500" />
            {t('trips.title')}
          </h1>
          <p className="text-brand-600 dark:text-brand-300 max-w-xl">{t('trips.subtitle')}</p>
        </div>
      </FadeIn>

      {isLoading && (
        <div className="space-y-4">
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
        </div>
      )}

      {!isLoading && trips?.length === 0 && (
        <FadeIn>
          <div className="text-center py-20 rounded-2xl bg-white/60 dark:bg-brand-900/40">
            <History className="w-10 h-10 text-brand-300 dark:text-brand-600 mx-auto mb-4" />
            <p className="text-brand-700 dark:text-brand-200 font-medium">{t('trips.empty')}</p>
            <p className="text-brand-500 dark:text-brand-400 text-sm mt-1">{t('trips.emptyCta')}</p>
            <Button className="mt-5" asChild>
              <Link to="/planner">{t('trips.goToPlanner')}</Link>
            </Button>
          </div>
        </FadeIn>
      )}

      {!isLoading && trips && trips.length > 0 && (
        <div className="space-y-4">
          {trips.map((trip, i) => {
            const ranked = [...trip.recommendations].sort((a, b) => b.final_score - a.final_score)
            const topPick = ranked[0]
            const remaining = ranked.length - 1

            return (
              <FadeIn key={trip.id} delay={i * 0.05}>
                <Card>
                  <CardContent className="p-6">
                    <div className="flex flex-wrap items-center gap-3 text-sm text-brand-500 dark:text-brand-400 mb-4">
                      <span className="flex items-center gap-1.5">
                        <Calendar className="w-4 h-4" />
                        {t('trips.searchedOn', {
                          date: new Date(trip.created_at).toLocaleDateString(i18n.resolvedLanguage),
                        })}
                      </span>
                      <span className="flex items-center gap-1.5">
                        <Users className="w-4 h-4" />
                        {t('trips.travelers', { count: trip.members.length })}
                      </span>
                      {trip.budget && (
                        <span className="flex items-center gap-1.5">
                          <Euro className="w-4 h-4" />
                          {trip.budget}
                        </span>
                      )}
                    </div>

                    {topPick && (
                      <div className="rounded-xl bg-brand-50/70 dark:bg-brand-800/40 border border-brand-100 dark:border-brand-700 p-4">
                        <p className="text-xs font-semibold text-brand-500 dark:text-brand-300 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                          <Sparkles className="w-3.5 h-3.5" />
                          {t('trips.topPick')}
                        </p>
                        <h3 className="font-display text-xl font-semibold text-brand-900 dark:text-white">
                          {topPick.explanation.city}, {topPick.explanation.country}
                        </h3>
                        {topPick.explanation.text && (
                          <p className="text-sm text-brand-600 dark:text-brand-300 mt-1">{topPick.explanation.text}</p>
                        )}
                        <div className="flex flex-wrap gap-1.5 mt-3">
                          {topPick.explanation.highlights?.map((h) => (
                            <Badge key={h} variant="accent">
                              {h}
                            </Badge>
                          ))}
                        </div>
                        {topPick.entity_id && (
                          <Link
                            to={`/destinations/${topPick.entity_id}`}
                            className="inline-block mt-3 text-sm font-semibold text-brand-600 dark:text-brand-300 hover:underline"
                          >
                            {t('destinations.explore', { city: topPick.explanation.city })}
                          </Link>
                        )}
                      </div>
                    )}

                    {remaining > 0 && (
                      <p className="text-xs text-brand-500 dark:text-brand-400 mt-3">
                        {t('trips.otherOptions', { count: remaining })}
                      </p>
                    )}
                  </CardContent>
                </Card>
              </FadeIn>
            )
          })}
        </div>
      )}
    </div>
  )
}
