import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import { Baby, Euro, Link as LinkIcon, Plane, Plus, Search, Sparkles, User } from 'lucide-react'
import { Link } from 'react-router-dom'
import { ApiError } from '../api/client'
import {
  toTripMember,
  useCreateFamilyMember,
  useDeleteFamilyMember,
  useFamilyMembers,
  useRecommend,
  useUpdateFamilyMember,
} from '../api/hooks'
import type { DestinationRecommendation, FamilyMemberInput } from '../types'
import { MONTHS } from '../types'
import RecommendationCard from '../components/planner/RecommendationCard'
import OriginLocationInput from '../components/planner/OriginLocationInput'
import FamilyMemberForm from '../components/family/FamilyMemberForm'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import FadeIn from '../components/ui/FadeIn'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Label } from '../components/ui/Label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/Select'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/Dialog'
import { Skeleton } from '../components/ui/Skeleton'

interface EditableMember extends FamilyMemberInput {
  id?: number
}

export default function PlannerPage() {
  const { t } = useTranslation()
  const familyQuery = useFamilyMembers()
  const createMember = useCreateFamilyMember()
  const updateMember = useUpdateFamilyMember()
  const deleteMember = useDeleteFamilyMember()
  const recommendMutation = useRecommend()

  const [members, setMembers] = useState<EditableMember[]>([])
  const [initialized, setInitialized] = useState(false)
  const [pendingDeletes, setPendingDeletes] = useState<number[]>([])
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingIndex, setEditingIndex] = useState<number | null>(null)

  const [budget, setBudget] = useState(1500)
  const [preferredMonth, setPreferredMonth] = useState(8)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [originLocation, setOriginLocation] = useState('')
  const [recommendations, setRecommendations] = useState<DestinationRecommendation[]>([])
  const [originMessage, setOriginMessage] = useState('')
  const [error, setError] = useState('')
  const [searched, setSearched] = useState(false)

  useEffect(() => {
    if (!initialized && familyQuery.data) {
      setMembers(
        familyQuery.data.map((m) => ({
          id: m.id,
          age: m.age,
          gender: m.gender,
          interests: m.interests,
          name: m.name,
          relation_type: m.relation_type,
        }))
      )
      setInitialized(true)
    }
  }, [familyQuery.data, initialized])

  const openAddMember = () => {
    setEditingIndex(null)
    setDialogOpen(true)
  }

  const openEditMember = (index: number) => {
    setEditingIndex(index)
    setDialogOpen(true)
  }

  const removeMember = (index: number) => {
    const member = members[index]
    if (member.id) setPendingDeletes((prev) => [...prev, member.id!])
    setMembers((prev) => prev.filter((_, i) => i !== index))
  }

  const handleMemberFormSubmit = (data: FamilyMemberInput) => {
    if (editingIndex === null) {
      setMembers((prev) => [...prev, data])
    } else {
      setMembers((prev) => prev.map((m, i) => (i === editingIndex ? { ...data, id: m.id } : m)))
    }
    setDialogOpen(false)
  }

  /** Persists local add/edit/remove changes back to the saved family profile before searching. */
  const syncFamily = async (): Promise<EditableMember[]> => {
    await Promise.all(pendingDeletes.map((id) => deleteMember.mutateAsync(id)))
    setPendingDeletes([])

    return Promise.all(
      members.map(async (m) => {
        const payload: FamilyMemberInput = {
          age: m.age,
          gender: m.gender,
          interests: m.interests,
          name: m.name,
          relation_type: m.relation_type,
        }
        if (m.id) {
          await updateMember.mutateAsync({ id: m.id, data: payload })
          return m
        }
        const created = await createMember.mutateAsync(payload)
        return { ...m, id: created.id }
      })
    )
  }

  const handleSearch = async () => {
    if (members.length === 0) {
      toast.error(t('planner.noSavedFamily'))
      return
    }
    setError('')
    setSearched(true)
    try {
      const synced = await syncFamily()
      setMembers(synced)
      const res = await recommendMutation.mutateAsync({
        members: synced.map(toTripMember),
        budget,
        preferred_month: preferredMonth,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        origin_location: originLocation.trim() || undefined,
      })
      setRecommendations(res.recommendations)
      setOriginMessage(res.origin_message || '')
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Search failed'
      setError(message)
      toast.error(message)
    }
  }

  const familyLoading = familyQuery.isLoading
  const loading = recommendMutation.isPending

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <FadeIn>
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-brand-500/10 dark:bg-brand-400/10 text-brand-700 dark:text-brand-200 text-sm font-medium mb-4">
            <Sparkles className="w-4 h-4" />
            {t('planner.badge')}
          </div>
          <h1 className="font-display text-4xl sm:text-5xl font-bold text-brand-900 dark:text-white mb-3">
            {t('planner.title')}
          </h1>
          <p className="text-brand-600 dark:text-brand-300 text-lg max-w-xl mx-auto">{t('planner.subtitle')}</p>
        </div>
      </FadeIn>

      <FadeIn delay={0.1}>
        <div className="glass dark:bg-brand-900/50 dark:border-brand-800 rounded-3xl shadow-card p-6 sm:p-8 mb-10">
          {/* Family members */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-brand-900 dark:text-white flex items-center gap-2">
                <User className="w-5 h-5 text-brand-500" />
                {t('planner.familyMembers')}
              </h2>
              <Button variant="ghost" size="sm" onClick={openAddMember}>
                <Plus className="w-4 h-4" />
                {t('planner.addMember')}
              </Button>
            </div>

            {familyLoading && (
              <div className="space-y-3">
                <Skeleton className="h-16" />
                <Skeleton className="h-16" />
              </div>
            )}

            {!familyLoading && members.length === 0 && (
              <p className="text-sm text-brand-500 dark:text-brand-400 bg-brand-50 dark:bg-brand-800/40 rounded-xl px-4 py-3">
                {t('planner.noSavedFamily')}{' '}
                <Link
                  to="/family"
                  className="font-semibold text-brand-700 dark:text-brand-200 underline underline-offset-2"
                >
                  <LinkIcon className="w-3 h-3 inline -mt-0.5 mr-0.5" />
                  {t('planner.familyPageLink')}
                </Link>
                .
              </p>
            )}

            {!familyLoading && members.length > 0 && (
              <div className="space-y-3">
                {members.map((member, i) => (
                  <div
                    key={member.id ?? `new-${i}`}
                    className="w-full flex items-center gap-3 p-4 rounded-2xl bg-white/60 dark:bg-brand-800/40 border border-brand-100 dark:border-brand-700 hover:border-brand-300 dark:hover:border-brand-500 transition-colors"
                  >
                    <button
                      type="button"
                      onClick={() => openEditMember(i)}
                      className="flex items-center gap-3 flex-1 min-w-0 text-left"
                    >
                      <div
                        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${
                          member.age < 18
                            ? 'bg-sunset-500/15 text-sunset-600'
                            : 'bg-brand-500/15 text-brand-600 dark:text-brand-300'
                        }`}
                      >
                        {member.age < 18 ? <Baby className="w-4 h-4" /> : <User className="w-4 h-4" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-brand-900 dark:text-white truncate">
                          {member.name || `${member.age} ${t('common.years')}`}
                        </p>
                        {member.interests.length > 0 && (
                          <p className="text-xs text-brand-500 dark:text-brand-400 truncate">
                            {member.interests.map((i2) => t(`interests.${i2}`)).join(', ')}
                          </p>
                        )}
                      </div>
                    </button>
                    <button
                      type="button"
                      onClick={() => removeMember(i)}
                      className="text-xs font-medium text-red-400 hover:text-red-600 px-2 py-1 rounded-lg hover:bg-red-50 dark:hover:bg-red-950/40 shrink-0"
                    >
                      {t('planner.removeMember')}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Budget & dates */}
          <div className="grid sm:grid-cols-2 gap-6 mb-8">
            <div>
              <Label className="flex items-center gap-2">
                <Euro className="w-4 h-4" />
                {t('planner.budget')}
              </Label>
              <Input
                type="number"
                value={budget}
                onChange={(e) => setBudget(parseFloat(e.target.value) || 0)}
                min={100}
                className="font-semibold text-lg"
              />
            </div>

            <div>
              <Label>{t('planner.preferredMonth')}</Label>
              <Select value={String(preferredMonth)} onValueChange={(v) => setPreferredMonth(parseInt(v))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MONTHS.map((m, i) => (
                    <SelectItem key={m} value={String(i + 1)}>
                      {m}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>{t('planner.startDate')}</Label>
              <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            </div>

            <div>
              <Label>{t('planner.endDate')}</Label>
              <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
            </div>

            <div className="sm:col-span-2">
              <Label className="flex items-center gap-2">
                <Plane className="w-4 h-4" />
                {t('planner.departingFrom')}
              </Label>
              <OriginLocationInput value={originLocation} onChange={setOriginLocation} />
            </div>
          </div>

          {error && (
            <div className="mb-4 px-4 py-3 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-300 text-sm">
              {error}
            </div>
          )}

          <Button size="lg" className="w-full" onClick={handleSearch} disabled={loading || budget <= 0}>
            <Search className="w-5 h-5" />
            {loading ? t('planner.finding') : t('planner.getRecommendations')}
          </Button>
        </div>
      </FadeIn>

      {loading && <LoadingSpinner message={t('planner.analyzing')} />}

      {!loading && searched && recommendations.length === 0 && !error && (
        <FadeIn>
          <div className="text-center py-16 glass dark:bg-brand-900/50 rounded-2xl">
            <p className="text-brand-600 dark:text-brand-300">{t('planner.noResults')}</p>
          </div>
        </FadeIn>
      )}

      {!loading && recommendations.length > 0 && (
        <div className="space-y-6">
          <FadeIn>
            <h2 className="font-display text-2xl font-bold text-brand-900 dark:text-white">
              {t('planner.topDestinations', { count: recommendations.length })}
            </h2>
            {originMessage && (
              <p className="text-brand-600 dark:text-brand-300 text-sm mt-2 flex items-center gap-2">
                <Plane className="w-4 h-4" />
                {originMessage}
              </p>
            )}
          </FadeIn>
          {recommendations.map((rec, i) => (
            <FadeIn key={rec.destination_id} delay={i * 0.08}>
              <RecommendationCard
                rec={rec}
                rank={i + 1}
                startDate={startDate || undefined}
                endDate={endDate || undefined}
                partySize={members.length}
                originLocation={originLocation.trim() || undefined}
              />
            </FadeIn>
          ))}
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingIndex === null ? t('family.addMember') : t('family.editMember')}</DialogTitle>
          </DialogHeader>
          <FamilyMemberForm
            defaultValues={editingIndex !== null ? members[editingIndex] : undefined}
            onSubmit={handleMemberFormSubmit}
            onCancel={() => setDialogOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </div>
  )
}
