import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import DestinationDetailPage from './DestinationDetailPage'

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({ isAuthenticated: true, loading: false }),
}))

const savedChild = { id: 3, user_id: 1, age: 11, gender: 'female', interests: ['disney'], name: 'Mia' }

vi.mock('../api/hooks', async () => {
  const actual = await vi.importActual<typeof import('../api/hooks')>('../api/hooks')
  return {
    ...actual,
    useDestination: () => ({
      data: {
        id: 4,
        city_id: 4,
        description: 'Mediterranean beaches and Gaudí architecture.',
        family_friendliness_score: 88,
        popularity_score: 89,
        city: 'Barcelona',
        country: 'Spain',
      },
      isLoading: false,
    }),
    useAttractions: () => ({ data: [], isLoading: false }),
    useFamilyMembers: () => ({ data: [savedChild], isLoading: false }),
    useHotels: () => ({ data: [], isLoading: false, isError: false }),
    useItinerary: () => ({ mutateAsync: vi.fn(), isPending: false }),
    useChildActivitiesForChildren: () => [
      {
        data: {
          activities: [
            {
              id: 14,
              name: 'Barcelona Aquarium',
              category: 'museum',
              description: "One of Europe's largest aquariums.",
              price: 25,
              match_score: 100,
              reason: 'Age-appropriate; Matches: disney',
            },
          ],
        },
        isLoading: false,
      },
    ],
    useAiGuide: () => ({ mutateAsync: vi.fn(), isPending: false, data: undefined }),
    useCheapestDates: () => ({ mutateAsync: vi.fn(), isPending: false }),
    useBudgetOptimize: () => ({ mutateAsync: vi.fn(), isPending: false }),
  }
})

function renderDetailPage() {
  return render(
    <MemoryRouter initialEntries={['/destinations/4']}>
      <Routes>
        <Route path="/destinations/:id" element={<DestinationDetailPage />} />
      </Routes>
    </MemoryRouter>
  )
}

describe('DestinationDetailPage Kids tab', () => {
  it('auto-fills activities for the saved child with no age/interest form', async () => {
    const user = userEvent.setup()
    renderDetailPage()

    await user.click(screen.getByRole('tab', { name: /Kids/i }))

    await waitFor(() => expect(screen.getByText(/Activities for Mia/)).toBeInTheDocument())
    expect(screen.getByText('Barcelona Aquarium')).toBeInTheDocument()
    expect(screen.queryByLabelText(/child's age/i)).not.toBeInTheDocument()
    expect(screen.queryByPlaceholderText(/age/i)).not.toBeInTheDocument()
  })
})
