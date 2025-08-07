/**
 * @jest-environment jsdom
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import ProfilePage from '../page'
import { useAuth } from '@/contexts/auth-context'
import { useI18n } from '@/contexts/i18n-context'

// Mock the contexts
jest.mock('@/contexts/auth-context')
jest.mock('@/contexts/i18n-context')

// Mock fetch
global.fetch = jest.fn()

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>
const mockUseI18n = useI18n as jest.MockedFunction<typeof useI18n>

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
})

describe('ProfilePage', () => {
  const mockUser = {
    id: '1',
    email: 'test@example.com',
    name: 'Test User',
    plan: 'FREE'
  }

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks()
    
    // Setup default mock returns
    mockUseAuth.mockReturnValue({
      user: mockUser,
      token: 'fake-token',
      isAuthenticated: true,
      isLoading: false,
      login: jest.fn(),
      logout: jest.fn(),
      loadUser: jest.fn(),
      updateUserPreferences: jest.fn(),
      updateProfile: jest.fn(),
      setPassword: jest.fn(),
      changePassword: jest.fn(),
      deleteAccount: jest.fn(),
    })

    mockUseI18n.mockReturnValue({
      t: (key: string) => key,
      language: 'zh',
      setLanguage: jest.fn(),
    })

    mockLocalStorage.getItem.mockReturnValue('fake-token')
    
    // Mock successful fetch responses
    ;(global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => null, // No profile initially
    })
  })

  it('renders profile page with correct title', () => {
    render(<ProfilePage />)
    expect(screen.getByText('教練履歷')).toBeInTheDocument()
  })

  it('shows edit button when not editing', () => {
    render(<ProfilePage />)
    expect(screen.getByText('編輯')).toBeInTheDocument()
  })

  it('switches to edit mode when edit button is clicked', () => {
    render(<ProfilePage />)
    
    const editButton = screen.getByText('編輯')
    fireEvent.click(editButton)
    
    expect(screen.getByText('取消')).toBeInTheDocument()
    expect(screen.getByText('儲存')).toBeInTheDocument()
  })

  it('loads coach profile on mount', async () => {
    const mockProfile = {
      id: '1',
      user_id: '1',
      display_name: 'Test Coach',
      public_email: 'coach@example.com',
      country: 'USA',
      coaching_languages: ['english', 'spanish'],
      communication_tools: { zoom: true, line: false },
      certifications: ['ACC', 'PCC'],
      specialties: ['Leadership'],
      is_public: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z'
    }

    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockProfile,
    }).mockResolvedValueOnce({
      ok: true,
      json: async () => [], // Empty coaching plans
    })

    render(<ProfilePage />)

    await waitFor(() => {
      expect(screen.getByDisplayValue('Test Coach')).toBeInTheDocument()
      expect(screen.getByDisplayValue('coach@example.com')).toBeInTheDocument()
      expect(screen.getByDisplayValue('USA')).toBeInTheDocument()
    })
  })

  it('makes correct API calls on mount', async () => {
    render(<ProfilePage />)

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/coach-profile/', {
        headers: {
          'Authorization': 'Bearer fake-token',
          'Content-Type': 'application/json'
        }
      })
      
      expect(global.fetch).toHaveBeenCalledWith('/api/coach-profile/plans', {
        headers: {
          'Authorization': 'Bearer fake-token',
          'Content-Type': 'application/json'
        }
      })
    })
  })

  it('handles form input changes', async () => {
    render(<ProfilePage />)
    
    // Switch to edit mode
    const editButton = screen.getByText('編輯')
    fireEvent.click(editButton)

    // Find the display name input and change it
    const displayNameInput = screen.getByPlaceholderText('請輸入您的公開顯示名稱')
    fireEvent.change(displayNameInput, { target: { value: 'New Coach Name' } })
    
    expect(displayNameInput).toHaveValue('New Coach Name')
  })

  it('handles language selection', async () => {
    render(<ProfilePage />)
    
    // Switch to edit mode
    const editButton = screen.getByText('編輯')
    fireEvent.click(editButton)

    // Find and click English checkbox
    const englishCheckbox = screen.getByLabelText('English', { exact: false })
    fireEvent.click(englishCheckbox)
    
    expect(englishCheckbox).toBeChecked()
  })

  it('handles communication tools toggle', async () => {
    render(<ProfilePage />)
    
    // Switch to edit mode
    const editButton = screen.getByText('編輯')
    fireEvent.click(editButton)

    // Find Zoom toggle (it's a hidden checkbox)
    const zoomToggle = screen.getByRole('checkbox', { hidden: true })
    fireEvent.click(zoomToggle)
    
    // The checkbox should be checked after click
    expect(zoomToggle).toBeChecked()
  })

  it('saves coach profile when save button is clicked', async () => {
    ;(global.fetch as jest.Mock)
      .mockResolvedValueOnce({ ok: true, json: async () => null }) // Initial profile load
      .mockResolvedValueOnce({ ok: true, json: async () => [] }) // Initial plans load
      .mockResolvedValueOnce({ // Save response
        ok: true,
        json: async () => ({
          id: '1',
          display_name: 'Saved Coach',
          user_id: '1',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z'
        })
      })

    // Mock window.alert
    window.alert = jest.fn()

    render(<ProfilePage />)
    
    // Switch to edit mode
    const editButton = screen.getByText('編輯')
    fireEvent.click(editButton)

    // Change display name
    const displayNameInput = screen.getByPlaceholderText('請輸入您的公開顯示名稱')
    fireEvent.change(displayNameInput, { target: { value: 'Saved Coach' } })

    // Click save
    const saveButton = screen.getByText('儲存')
    fireEvent.click(saveButton)

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/coach-profile/', {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer fake-token',
          'Content-Type': 'application/json'
        },
        body: expect.stringContaining('"display_name":"Saved Coach"')
      })
    })

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith('教練履歷已儲存成功！')
    })
  })

  it('shows coaching plans modal when add plan button is clicked', async () => {
    render(<ProfilePage />)
    
    const addPlanButton = screen.getByText('新增方案')
    fireEvent.click(addPlanButton)
    
    expect(screen.getByText('新增教練方案')).toBeInTheDocument()
    expect(screen.getByText('建立方案')).toBeInTheDocument()
  })

  it('creates coaching plan when form is submitted', async () => {
    const mockCreatedPlan = {
      id: '1',
      title: 'Test Plan',
      plan_type: 'single_session',
      price: 100,
      duration_minutes: 60,
      coach_profile_id: '1',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z'
    }

    ;(global.fetch as jest.Mock)
      .mockResolvedValueOnce({ ok: true, json: async () => null }) // Initial profile load
      .mockResolvedValueOnce({ ok: true, json: async () => [] }) // Initial plans load
      .mockResolvedValueOnce({ // Create plan response
        ok: true,
        json: async () => mockCreatedPlan
      })

    // Mock window.alert
    window.alert = jest.fn()

    render(<ProfilePage />)
    
    // Open modal
    const addPlanButton = screen.getByText('新增方案')
    fireEvent.click(addPlanButton)
    
    // Fill form
    const titleInput = screen.getByPlaceholderText('例如：一對一教練諮詢')
    fireEvent.change(titleInput, { target: { value: 'Test Plan' } })
    
    const priceInput = screen.getByDisplayValue('0')
    fireEvent.change(priceInput, { target: { value: '100' } })
    
    // Submit
    const createButton = screen.getByText('建立方案')
    fireEvent.click(createButton)

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/coach-profile/plans', {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer fake-token',
          'Content-Type': 'application/json'
        },
        body: expect.stringContaining('"title":"Test Plan"')
      })
    })

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith('教練方案已建立成功！')
    })
  })

  it('displays coaching plans when they exist', async () => {
    const mockPlans = [
      {
        id: '1',
        title: 'Single Session',
        plan_type: 'single_session',
        price: 150,
        duration_minutes: 60,
        number_of_sessions: 1,
        currency: 'NTD',
        is_active: true,
        max_participants: 1,
        price_per_session: 150,
        total_duration_minutes: 60,
        coach_profile_id: '1',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      },
      {
        id: '2',
        title: '4-Session Package',
        plan_type: 'package',
        price: 500,
        duration_minutes: 90,
        number_of_sessions: 4,
        currency: 'NTD',
        is_active: true,
        max_participants: 1,
        price_per_session: 125,
        total_duration_minutes: 360,
        coach_profile_id: '1',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      }
    ]

    ;(global.fetch as jest.Mock)
      .mockResolvedValueOnce({ ok: true, json: async () => null }) // Initial profile load
      .mockResolvedValueOnce({ ok: true, json: async () => mockPlans }) // Plans load

    render(<ProfilePage />)

    await waitFor(() => {
      expect(screen.getByText('Single Session')).toBeInTheDocument()
      expect(screen.getByText('4-Session Package')).toBeInTheDocument()
      expect(screen.getByText('NTD 150')).toBeInTheDocument()
      expect(screen.getByText('NTD 500')).toBeInTheDocument()
    })
  })

  it('shows empty state when no coaching plans exist', async () => {
    ;(global.fetch as jest.Mock)
      .mockResolvedValueOnce({ ok: true, json: async () => null }) // Initial profile load
      .mockResolvedValueOnce({ ok: true, json: async () => [] }) // Empty plans

    render(<ProfilePage />)

    await waitFor(() => {
      expect(screen.getByText('尚未設定任何教練方案')).toBeInTheDocument()
      expect(screen.getByText('點擊「新增方案」建立您的第一個教練方案')).toBeInTheDocument()
    })
  })

  it('handles public/private toggle', async () => {
    render(<ProfilePage />)
    
    // Switch to edit mode
    const editButton = screen.getByText('編輯')
    fireEvent.click(editButton)

    // Find the public toggle (hidden checkbox in the public settings section)
    const publicToggles = screen.getAllByRole('checkbox', { hidden: true })
    const publicToggle = publicToggles[publicToggles.length - 1] // Last toggle should be the public setting
    
    fireEvent.click(publicToggle)
    expect(publicToggle).toBeChecked()
  })

  it('handles cancel editing', async () => {
    render(<ProfilePage />)
    
    // Switch to edit mode
    const editButton = screen.getByText('編輯')
    fireEvent.click(editButton)
    
    // Click cancel
    const cancelButton = screen.getByText('取消')
    fireEvent.click(cancelButton)
    
    // Should be back to view mode
    expect(screen.getByText('編輯')).toBeInTheDocument()
    expect(screen.queryByText('取消')).not.toBeInTheDocument()
  })

  it('shows loading state initially', () => {
    render(<ProfilePage />)
    
    // The edit button should not be visible during loading
    // Instead, the page should be rendered but in a non-editable state
    const inputs = screen.getAllByRole('textbox')
    inputs.forEach(input => {
      expect(input).toBeDisabled()
    })
  })
})