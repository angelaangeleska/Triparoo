import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import PlannerPage from './PlannerPage'

const mutateAsync = {
  create: vi.fn(),
  update: vi.fn(),
  delete: vi.fn(),
  recommend: vi.fn(),
}

vi.mock('../api/hooks', async () => {
  const actual = await vi.importActual<typeof import('../api/hooks')>('../api/hooks')
  return {
    ...actual,
    useFamilyMembers: () => ({
      data: [
        { id: 1, user_id: 1, age: 35, gender: 'male', interests: [], name: 'Alex' },
        { id: 3, user_id: 1, age: 11, gender: 'female', interests: ['disney'], name: 'Mia' },
      ],
      isLoading: false,
    }),
    useCreateFamilyMember: () => ({ mutateAsync: mutateAsync.create, isPending: false }),
    useUpdateFamilyMember: () => ({ mutateAsync: mutateAsync.update, isPending: false }),
    useDeleteFamilyMember: () => ({ mutateAsync: mutateAsync.delete, isPending: false }),
    useRecommend: () => ({ mutateAsync: mutateAsync.recommend, isPending: false }),
  }
})

vi.mock('../api/client', () => ({
  api: { resolveOrigin: vi.fn() },
  ApiError: class ApiError extends Error {},
}))

function renderPlanner() {
  return render(
    <MemoryRouter>
      <PlannerPage />
    </MemoryRouter>
  )
}

describe('PlannerPage family sync', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mutateAsync.update.mockImplementation(({ id }: { id: number }) => Promise.resolve({ id }))
    mutateAsync.delete.mockResolvedValue(undefined)
    mutateAsync.recommend.mockResolvedValue({ recommendations: [], origin_message: '' })
  })

  it('auto-fills the saved family members instead of asking to re-enter them', () => {
    renderPlanner()
    expect(screen.getByText('Alex')).toBeInTheDocument()
    expect(screen.getByText('Mia')).toBeInTheDocument()
  })

  it('removes a member locally and syncs the deletion + remaining member before searching', async () => {
    const user = userEvent.setup()
    renderPlanner()

    const removeButtons = screen.getAllByText('Remove member')
    await user.click(removeButtons[0])
    expect(screen.queryByText('Alex')).not.toBeInTheDocument()
    expect(screen.getByText('Mia')).toBeInTheDocument()

    await user.click(screen.getByText('Get recommendations'))

    await waitFor(() => expect(mutateAsync.delete).toHaveBeenCalledWith(1))
    expect(mutateAsync.update).toHaveBeenCalledWith(
      expect.objectContaining({ id: 3, data: expect.objectContaining({ age: 11 }) })
    )
    await waitFor(() => expect(mutateAsync.recommend).toHaveBeenCalledTimes(1))
    const [request] = mutateAsync.recommend.mock.calls[0]
    expect(request.members).toEqual([{ age: 11, gender: 'female', interests: ['disney'] }])
  })
})
