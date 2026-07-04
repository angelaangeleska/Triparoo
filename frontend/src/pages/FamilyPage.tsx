import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Plus, Users } from 'lucide-react'
import { toast } from 'sonner'
import {
  useCreateFamilyMember,
  useDeleteFamilyMember,
  useFamilyMembers,
  useUpdateFamilyMember,
} from '../api/hooks'
import type { FamilyMember, FamilyMemberInput } from '../types'
import FamilyMemberCard from '../components/family/FamilyMemberCard'
import FamilyMemberForm from '../components/family/FamilyMemberForm'
import { Button } from '../components/ui/Button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/Dialog'
import { Skeleton } from '../components/ui/Skeleton'
import FadeIn from '../components/ui/FadeIn'

export default function FamilyPage() {
  const { t } = useTranslation()
  const { data: members, isLoading } = useFamilyMembers()
  const createMember = useCreateFamilyMember()
  const updateMember = useUpdateFamilyMember()
  const deleteMember = useDeleteFamilyMember()

  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<FamilyMember | null>(null)

  const openCreate = () => {
    setEditing(null)
    setDialogOpen(true)
  }

  const openEdit = (member: FamilyMember) => {
    setEditing(member)
    setDialogOpen(true)
  }

  const handleSubmit = (data: FamilyMemberInput) => {
    if (editing) {
      updateMember.mutate(
        { id: editing.id, data },
        {
          onSuccess: () => {
            toast.success(t('common.save'))
            setDialogOpen(false)
          },
          onError: () => toast.error(t('errors.genericLoadFailed')),
        }
      )
    } else {
      createMember.mutate(data, {
        onSuccess: () => {
          toast.success(t('common.save'))
          setDialogOpen(false)
        },
        onError: () => toast.error(t('errors.genericLoadFailed')),
      })
    }
  }

  const handleDelete = (member: FamilyMember) => {
    if (!window.confirm(t('family.confirmDelete'))) return
    deleteMember.mutate(member.id, {
      onSuccess: () => toast.success(t('common.delete')),
      onError: () => toast.error(t('errors.genericLoadFailed')),
    })
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <FadeIn>
        <div className="flex items-center justify-between flex-wrap gap-4 mb-10">
          <div>
            <h1 className="font-display text-4xl font-bold text-brand-900 dark:text-white mb-2">
              {t('family.title')}
            </h1>
            <p className="text-brand-600 dark:text-brand-300 max-w-xl">{t('family.subtitle')}</p>
          </div>
          <Button onClick={openCreate}>
            <Plus className="w-4 h-4" /> {t('family.addMember')}
          </Button>
        </div>
      </FadeIn>

      {isLoading && (
        <div className="grid sm:grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      )}

      {!isLoading && members?.length === 0 && (
        <FadeIn>
          <div className="text-center py-20 rounded-2xl bg-white/60 dark:bg-brand-900/40">
            <Users className="w-10 h-10 text-brand-300 dark:text-brand-600 mx-auto mb-4" />
            <p className="text-brand-700 dark:text-brand-200 font-medium">{t('family.empty')}</p>
            <p className="text-brand-500 dark:text-brand-400 text-sm mt-1">{t('family.emptyCta')}</p>
          </div>
        </FadeIn>
      )}

      {!isLoading && members && members.length > 0 && (
        <div className="grid sm:grid-cols-2 gap-4">
          {members.map((member, i) => (
            <FadeIn key={member.id} delay={i * 0.05}>
              <FamilyMemberCard member={member} onEdit={() => openEdit(member)} onDelete={() => handleDelete(member)} />
            </FadeIn>
          ))}
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? t('family.editMember') : t('family.addMember')}</DialogTitle>
          </DialogHeader>
          <FamilyMemberForm
            defaultValues={editing ?? undefined}
            onSubmit={handleSubmit}
            onCancel={() => setDialogOpen(false)}
            submitting={createMember.isPending || updateMember.isPending}
          />
        </DialogContent>
      </Dialog>
    </div>
  )
}
