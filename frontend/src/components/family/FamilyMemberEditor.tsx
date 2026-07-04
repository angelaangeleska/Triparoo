import { Baby, Minus, Plus, Trash2, User } from 'lucide-react'
import { INTEREST_OPTIONS } from '../../types'
import { isKid, useFamily } from '../../context/FamilyContext'
import NumericInput from '../ui/NumericInput'

export default function FamilyMemberEditor() {
  const { members, addMember, removeMember, updateMember, toggleInterest } = useFamily()

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-brand-900 flex items-center gap-2">
          <User className="w-5 h-5 text-brand-500" />
          Family members
        </h2>
        <button
          type="button"
          onClick={addMember}
          className="flex items-center gap-1.5 text-sm font-medium text-brand-600 hover:text-brand-800 px-3 py-1.5 rounded-lg hover:bg-brand-50 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add member
        </button>
      </div>

      {members.map((member, i) => (
        <div key={i} className="p-4 rounded-2xl bg-white/60 border border-brand-100">
          <div className="flex items-start gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <Baby className="w-4 h-4 text-brand-400" />
              <label className="text-sm text-brand-600">Age</label>
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => updateMember(i, 'age', Math.max(0, member.age - 1))}
                  className="w-8 h-8 rounded-lg bg-brand-100 hover:bg-brand-200 flex items-center justify-center"
                >
                  <Minus className="w-3.5 h-3.5" />
                </button>
                <NumericInput
                  integer
                  value={member.age}
                  onChange={(age) => updateMember(i, 'age', age)}
                  className="w-16 text-center py-1.5 rounded-lg border border-brand-200 bg-white font-semibold"
                  min={0}
                  max={120}
                />
                <button
                  type="button"
                  onClick={() => updateMember(i, 'age', member.age + 1)}
                  className="w-8 h-8 rounded-lg bg-brand-100 hover:bg-brand-200 flex items-center justify-center"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
              </div>
              {isKid(member) && (
                <span className="text-xs font-medium text-brand-500 bg-brand-50 px-2 py-0.5 rounded-full">
                  Kid
                </span>
              )}
            </div>

            <div>
              <label className="text-sm text-brand-600 block mb-1">Gender (optional)</label>
              <select
                value={member.gender || ''}
                onChange={(e) => updateMember(i, 'gender', e.target.value || '')}
                className="px-3 py-1.5 rounded-lg border border-brand-200 bg-white text-sm"
              >
                <option value="">—</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
              </select>
            </div>

            {members.length > 1 && (
              <button
                type="button"
                onClick={() => removeMember(i)}
                className="ml-auto p-2 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>

          {isKid(member) && (
            <div className="mt-3">
              <label className="text-xs text-brand-500 font-medium mb-2 block">
                Interests {member.interests.length > 0 && `(${member.interests.length} selected)`}
              </label>
              <div className="flex flex-wrap gap-2">
                {INTEREST_OPTIONS.map((interest) => (
                  <button
                    key={interest}
                    type="button"
                    onClick={() => toggleInterest(i, interest)}
                    className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                      member.interests.includes(interest)
                        ? 'bg-brand-500 text-white'
                        : 'bg-brand-100 text-brand-700 hover:bg-brand-200'
                    }`}
                  >
                    {interest.replace('_', ' ')}
                  </button>
                ))}
              </div>
              {member.interests.length === 0 && (
                <p className="text-xs text-brand-500 mt-2">
                  Select at least one interest so we can suggest kid-friendly activities.
                </p>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
