import { useTranslation } from 'react-i18next'
import { Baby, Edit2, Trash2, User } from 'lucide-react'
import { Card, CardContent } from '../ui/Card'
import { Button } from '../ui/Button'
import { Badge } from '../ui/Badge'
import type { FamilyMember } from '../../types'

interface Props {
  member: FamilyMember
  onEdit: () => void
  onDelete: () => void
}

export default function FamilyMemberCard({ member, onEdit, onDelete }: Props) {
  const { t } = useTranslation()
  const isChild = member.age < 18

  return (
    <Card className="hover:shadow-glow transition-shadow">
      <CardContent className="p-5 flex items-start gap-4">
        <div
          className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full ${
            isChild
              ? 'bg-sunset-500/15 text-sunset-600 dark:bg-sunset-400/20 dark:text-sunset-300'
              : 'bg-brand-500/15 text-brand-600 dark:bg-brand-400/20 dark:text-brand-300'
          }`}
        >
          {isChild ? <Baby className="w-5 h-5" /> : <User className="w-5 h-5" />}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <h3 className="font-semibold text-brand-900 dark:text-white truncate">
              {member.name || t('family.member')}
            </h3>
            <div className="flex gap-1 shrink-0">
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onEdit} aria-label={t('common.edit')}>
                <Edit2 className="w-3.5 h-3.5" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/40"
                onClick={onDelete}
                aria-label={t('common.delete')}
              >
                <Trash2 className="w-3.5 h-3.5" />
              </Button>
            </div>
          </div>
          <p className="text-sm text-brand-600 dark:text-brand-300">
            {member.age} {t('common.years')}
            {member.relation_type ? ` · ${member.relation_type}` : ''}
          </p>
          {member.interests.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-2">
              {member.interests.map((i) => (
                <Badge key={i} variant="muted">
                  {t(`interests.${i}`)}
                </Badge>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
