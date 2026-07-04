import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './client'
import type { FamilyMember, FamilyMemberInput, TripMember } from '../types'

export function useDestinations() {
  return useQuery({ queryKey: ['destinations'], queryFn: api.destinations })
}

export function useTripHistory() {
  return useQuery({ queryKey: ['trip-history'], queryFn: api.tripHistory })
}

export function useDestination(id: number) {
  return useQuery({
    queryKey: ['destination', id],
    queryFn: () => api.destination(id),
    enabled: Number.isFinite(id) && id > 0,
  })
}

export function useAttractions(destinationId?: number) {
  return useQuery({
    queryKey: ['attractions', destinationId],
    queryFn: () => api.attractions(destinationId),
    enabled: Number.isFinite(destinationId) && (destinationId ?? 0) > 0,
  })
}

export function useHotels(
  city: string,
  checkIn: string,
  checkOut: string,
  adults: number,
  children: number,
  country: string
) {
  return useQuery({
    queryKey: ['hotels', city, checkIn, checkOut, adults, children, country],
    queryFn: () => api.searchHotels(city, checkIn, checkOut, adults, children, country),
    enabled: Boolean(city),
    retry: false,
  })
}

export function useRecommend() {
  return useMutation({ mutationFn: api.recommend })
}

export function useCheapestDates() {
  return useMutation({ mutationFn: api.cheapestDates })
}

export function useItinerary() {
  return useMutation({ mutationFn: api.itinerary })
}

export function useChildActivities() {
  return useMutation({ mutationFn: api.childActivities })
}

/**
 * Fetches age/interest-matched activities for every saved child at once, in parallel —
 * powers the Kids tab auto-fill (no re-entering ages/interests already saved in the family profile).
 */
export function useChildActivitiesForChildren(destinationId: number, children: FamilyMember[]) {
  return useQueries({
    queries: children.map((child) => ({
      queryKey: ['child-activities', destinationId, child.id, child.age, child.interests.join(',')],
      queryFn: () =>
        api.childActivities({
          destination_id: destinationId,
          age: child.age,
          gender: child.gender,
          interests: child.interests,
        }),
      enabled: Number.isFinite(destinationId) && destinationId > 0,
    })),
  })
}

export function useBudgetOptimize() {
  return useMutation({ mutationFn: api.budgetOptimize })
}

export function useAiGuide() {
  return useMutation({ mutationFn: api.aiGuide })
}

export function useFamilyMembers(enabled = true) {
  return useQuery({ queryKey: ['family-members'], queryFn: api.familyMembers, enabled })
}

export function useCreateFamilyMember() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: FamilyMemberInput) => api.createFamilyMember(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['family-members'] }),
  })
}

export function useUpdateFamilyMember() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: FamilyMemberInput }) => api.updateFamilyMember(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['family-members'] }),
  })
}

export function useDeleteFamilyMember() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.deleteFamilyMember(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['family-members'] }),
  })
}

/** Converts a saved FamilyMember into the lighter TripMember shape trip-planner endpoints expect. */
export function toTripMember(member: { age: number; gender?: string; interests: string[] }): TripMember {
  return { age: member.age, gender: member.gender, interests: member.interests }
}
