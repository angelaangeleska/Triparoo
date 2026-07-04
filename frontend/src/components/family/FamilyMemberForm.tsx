import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useTranslation } from 'react-i18next'
import { Baby, Minus, Plus } from 'lucide-react'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { Label } from '../ui/Label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/Select'
import { INTEREST_OPTIONS, type FamilyMemberInput } from '../../types'

const schema = z.object({
  name: z.string().optional(),
  age: z.number().int().min(0, 'Age must be 0 or more').max(120, 'Age must be 120 or less'),
  gender: z.string().optional(),
  relation_type: z.string().optional(),
  interests: z.array(z.string()),
})

type FormValues = z.infer<typeof schema>

interface Props {
  defaultValues?: Partial<FamilyMemberInput>
  onSubmit: (data: FamilyMemberInput) => void
  onCancel?: () => void
  submitting?: boolean
}

export default function FamilyMemberForm({ defaultValues, onSubmit, onCancel, submitting }: Props) {
  const { t } = useTranslation()
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: defaultValues?.name ?? '',
      age: defaultValues?.age ?? 8,
      gender: defaultValues?.gender ?? '',
      relation_type: defaultValues?.relation_type ?? '',
      interests: defaultValues?.interests ?? [],
    },
  })

  const age = watch('age')
  const interests = watch('interests')
  const gender = watch('gender')

  const toggleInterest = (interest: string) => {
    setValue(
      'interests',
      interests.includes(interest) ? interests.filter((i) => i !== interest) : [...interests, interest],
      { shouldDirty: true }
    )
  }

  const submit = handleSubmit((data) => {
    onSubmit({
      name: data.name || undefined,
      age: data.age,
      gender: data.gender || undefined,
      relation_type: data.relation_type || undefined,
      interests: data.interests,
    })
  })

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="name">{t('family.name')}</Label>
          <Input id="name" {...register('name')} placeholder="Mia" />
        </div>
        <div>
          <Label htmlFor="relation_type">{t('family.relation')}</Label>
          <Input id="relation_type" {...register('relation_type')} placeholder="Daughter" />
        </div>
      </div>

      <div className="flex items-end gap-4 flex-wrap">
        <div>
          <Label className="flex items-center gap-1.5">
            <Baby className="w-4 h-4" /> {t('planner.age')}
          </Label>
          <div className="flex items-center gap-1">
            <Button
              type="button"
              variant="secondary"
              size="icon"
              className="h-9 w-9"
              onClick={() => setValue('age', Math.max(0, age - 1))}
            >
              <Minus className="w-3.5 h-3.5" />
            </Button>
            <Input type="number" className="w-20 text-center" {...register('age', { valueAsNumber: true })} />
            <Button
              type="button"
              variant="secondary"
              size="icon"
              className="h-9 w-9"
              onClick={() => setValue('age', age + 1)}
            >
              <Plus className="w-3.5 h-3.5" />
            </Button>
          </div>
          {errors.age && <p className="text-xs text-red-500 mt-1">{errors.age.message}</p>}
        </div>

        <div className="min-w-[10rem]">
          <Label>{t('planner.gender')}</Label>
          <Select value={gender || 'none'} onValueChange={(v) => setValue('gender', v === 'none' ? '' : v)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">{t('planner.genderNone')}</SelectItem>
              <SelectItem value="male">{t('planner.genderMale')}</SelectItem>
              <SelectItem value="female">{t('planner.genderFemale')}</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {age < 18 && (
        <div>
          <Label>{t('planner.interests')}</Label>
          <div className="flex flex-wrap gap-2">
            {INTEREST_OPTIONS.map((interest) => (
              <button
                type="button"
                key={interest}
                onClick={() => toggleInterest(interest)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                  interests.includes(interest)
                    ? 'bg-brand-500 text-white'
                    : 'bg-brand-100 text-brand-700 hover:bg-brand-200 dark:bg-brand-800 dark:text-brand-200'
                }`}
              >
                {t(`interests.${interest}`)}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-2 justify-end pt-2">
        {onCancel && (
          <Button type="button" variant="ghost" onClick={onCancel}>
            {t('common.cancel')}
          </Button>
        )}
        <Button type="submit" disabled={submitting}>
          {t('common.save')}
        </Button>
      </div>
    </form>
  )
}
