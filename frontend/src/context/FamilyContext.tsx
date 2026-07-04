import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import type { TripMember } from '../types'

const STORAGE_KEY = 'triparoo_family_members'

export const DEFAULT_FAMILY_MEMBERS: TripMember[] = [
  { age: 35, interests: [] },
  { age: 33, interests: [] },
  { age: 11, gender: 'female', interests: ['disney', 'science'] },
]

export function isKid(member: TripMember): boolean {
  return member.age < 18
}

function loadMembers(): TripMember[] {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return DEFAULT_FAMILY_MEMBERS
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed) || parsed.length === 0) return DEFAULT_FAMILY_MEMBERS
    return parsed as TripMember[]
  } catch {
    return DEFAULT_FAMILY_MEMBERS
  }
}

interface FamilyContextType {
  members: TripMember[]
  kids: TripMember[]
  setMembers: (members: TripMember[]) => void
  addMember: () => void
  removeMember: (index: number) => void
  updateMember: (index: number, field: keyof TripMember, value: string | number | string[]) => void
  toggleInterest: (memberIndex: number, interest: string) => void
}

const FamilyContext = createContext<FamilyContextType | null>(null)

export function FamilyProvider({ children }: { children: ReactNode }) {
  const [members, setMembersState] = useState<TripMember[]>(loadMembers)

  const kids = useMemo(() => members.filter(isKid), [members])

  useEffect(() => {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(members))
  }, [members])

  const setMembers = useCallback((next: TripMember[]) => {
    setMembersState(next.length > 0 ? next : DEFAULT_FAMILY_MEMBERS)
  }, [])

  const addMember = useCallback(() => {
    setMembersState((prev) => [...prev, { age: 30, interests: [] }])
  }, [])

  const removeMember = useCallback((index: number) => {
    setMembersState((prev) => (prev.length > 1 ? prev.filter((_, i) => i !== index) : prev))
  }, [])

  const updateMember = useCallback(
    (index: number, field: keyof TripMember, value: string | number | string[]) => {
      setMembersState((prev) =>
        prev.map((m, i) => (i === index ? { ...m, [field]: value } : m)),
      )
    },
    [],
  )

  const toggleInterest = useCallback((memberIndex: number, interest: string) => {
    setMembersState((prev) =>
      prev.map((m, i) => {
        if (i !== memberIndex) return m
        const next = m.interests.includes(interest)
          ? m.interests.filter((x) => x !== interest)
          : [...m.interests, interest]
        return { ...m, interests: next }
      }),
    )
  }, [])

  return (
    <FamilyContext.Provider
      value={{ members, kids, setMembers, addMember, removeMember, updateMember, toggleInterest }}
    >
      {children}
    </FamilyContext.Provider>
  )
}

export function useFamily() {
  const ctx = useContext(FamilyContext)
  if (!ctx) throw new Error('useFamily must be used within FamilyProvider')
  return ctx
}
