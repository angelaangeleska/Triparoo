import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Globe, Search } from 'lucide-react'
import { useDestinations } from '../api/hooks'
import DestinationCard from '../components/destinations/DestinationCard'
import { Input } from '../components/ui/Input'
import { Skeleton } from '../components/ui/Skeleton'
import FadeIn from '../components/ui/FadeIn'

export default function DestinationsPage() {
  const { t } = useTranslation()
  const { data: destinations, isLoading } = useDestinations()
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return (destinations ?? []).filter(
      (d) =>
        d.city?.toLowerCase().includes(q) ||
        d.country?.toLowerCase().includes(q) ||
        d.description?.toLowerCase().includes(q)
    )
  }, [destinations, search])

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <FadeIn>
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-brand-500/10 dark:bg-brand-400/10 text-brand-700 dark:text-brand-200 text-sm font-medium mb-4">
            <Globe className="w-4 h-4" />
            {t('home.badge')}
          </div>
          <h1 className="font-display text-4xl sm:text-5xl font-bold text-brand-900 dark:text-white mb-3">
            {t('destinations.title')}
          </h1>
          <p className="text-brand-600 dark:text-brand-300 text-lg max-w-xl mx-auto">{t('destinations.subtitle')}</p>
        </div>
      </FadeIn>

      <FadeIn delay={0.1}>
        <div className="relative max-w-md mx-auto mb-10">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-brand-400 z-10" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('destinations.searchPlaceholder') ?? ''}
            className="pl-12 h-12 rounded-2xl shadow-soft"
          />
        </div>
      </FadeIn>

      {isLoading ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-72" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 text-brand-600 dark:text-brand-300">{t('destinations.noResults')}</div>
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
