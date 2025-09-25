/**
 * @jest-environment jsdom
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { SessionPage } from '../app/dashboard/sessions/[id]/page'

// Mock the API client
jest.mock('../lib/api', () => ({
  apiClient: {
    updateSegmentContent: jest.fn(),
    updateSegmentRoles: jest.fn(),
  }
}))

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    back: jest.fn(),
  }),
  useParams: () => ({
    id: 'test-session-id'
  }),
  useSearchParams: () => new URLSearchParams(),
}))

// Mock i18n
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: {
      changeLanguage: jest.fn(),
    },
  }),
}))

const mockTranscript = {
  session_id: 'test-session-id',
  title: 'Test Session',
  segments: [
    {
      id: 'segment-1',
      speaker_id: 1,
      speaker_name: 'Speaker 1',
      start_sec: 0.0,
      end_sec: 5.0,
      content: 'Hello, welcome to the session.',
    },
    {
      id: 'segment-2',
      speaker_id: 2,
      speaker_name: 'Speaker 2',
      start_sec: 5.5,
      end_sec: 10.0,
      content: 'Thank you for having me.',
    }
  ],
  role_assignments: {
    1: 'coach',
    2: 'client'
  },
  segment_roles: {}
}

describe('Segment Editing Functionality', () => {
  const mockUpdateSegmentContent = jest.fn()
  const mockUpdateSegmentRoles = jest.fn()

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks()

    // Setup API client mocks
    require('../lib/api').apiClient.updateSegmentContent = mockUpdateSegmentContent
    require('../lib/api').apiClient.updateSegmentRoles = mockUpdateSegmentRoles

    mockUpdateSegmentContent.mockResolvedValue({ success: true })
    mockUpdateSegmentRoles.mockResolvedValue({ success: true })
  })

  test('should enter edit mode when edit button is clicked', async () => {
    render(<SessionPage transcript={mockTranscript} />)

    const editButton = screen.getByText(/sessions.editTranscript/)
    fireEvent.click(editButton)

    // Should show text areas for editing
    expect(screen.getByDisplayValue('Hello, welcome to the session.')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Thank you for having me.')).toBeInTheDocument()

    // Should show save and cancel buttons
    expect(screen.getByText(/sessions.saveChanges/)).toBeInTheDocument()
    expect(screen.getByText(/sessions.cancelEdit/)).toBeInTheDocument()
  })

  test('should update segment content when typing in textarea', async () => {
    render(<SessionPage transcript={mockTranscript} />)

    // Enter edit mode
    const editButton = screen.getByText(/sessions.editTranscript/)
    fireEvent.click(editButton)

    // Find and update the first segment
    const firstSegmentTextarea = screen.getByDisplayValue('Hello, welcome to the session.')
    fireEvent.change(firstSegmentTextarea, {
      target: { value: 'Hello, welcome to our coaching session.' }
    })

    expect(firstSegmentTextarea).toHaveValue('Hello, welcome to our coaching session.')
  })

  test('should save segment content changes when save button is clicked', async () => {
    render(<SessionPage transcript={mockTranscript} />)

    // Enter edit mode
    const editButton = screen.getByText(/sessions.editTranscript/)
    fireEvent.click(editButton)

    // Update segment content
    const firstSegmentTextarea = screen.getByDisplayValue('Hello, welcome to the session.')
    fireEvent.change(firstSegmentTextarea, {
      target: { value: 'Updated content for segment 1' }
    })

    // Save changes
    const saveButton = screen.getByText(/sessions.saveChanges/)
    fireEvent.click(saveButton)

    await waitFor(() => {
      expect(mockUpdateSegmentContent).toHaveBeenCalledWith(
        'test-session-id',
        {
          'segment-1': 'Updated content for segment 1'
        }
      )
    })
  })

  test('should not call API when no segment content changes are made', async () => {
    render(<SessionPage transcript={mockTranscript} />)

    // Enter edit mode
    const editButton = screen.getByText(/sessions.editTranscript/)
    fireEvent.click(editButton)

    // Save without making changes
    const saveButton = screen.getByText(/sessions.saveChanges/)
    fireEvent.click(saveButton)

    await waitFor(() => {
      // Should not call updateSegmentContent since no changes were made
      expect(mockUpdateSegmentContent).not.toHaveBeenCalled()
    })
  })

  test('should save multiple segment content changes', async () => {
    render(<SessionPage transcript={mockTranscript} />)

    // Enter edit mode
    const editButton = screen.getByText(/sessions.editTranscript/)
    fireEvent.click(editButton)

    // Update both segments
    const firstSegmentTextarea = screen.getByDisplayValue('Hello, welcome to the session.')
    const secondSegmentTextarea = screen.getByDisplayValue('Thank you for having me.')

    fireEvent.change(firstSegmentTextarea, {
      target: { value: 'Updated first segment' }
    })
    fireEvent.change(secondSegmentTextarea, {
      target: { value: 'Updated second segment' }
    })

    // Save changes
    const saveButton = screen.getByText(/sessions.saveChanges/)
    fireEvent.click(saveButton)

    await waitFor(() => {
      expect(mockUpdateSegmentContent).toHaveBeenCalledWith(
        'test-session-id',
        {
          'segment-1': 'Updated first segment',
          'segment-2': 'Updated second segment'
        }
      )
    })
  })

  test('should handle empty segment content updates', async () => {
    render(<SessionPage transcript={mockTranscript} />)

    // Enter edit mode
    const editButton = screen.getByText(/sessions.editTranscript/)
    fireEvent.click(editButton)

    // Clear the first segment content
    const firstSegmentTextarea = screen.getByDisplayValue('Hello, welcome to the session.')
    fireEvent.change(firstSegmentTextarea, {
      target: { value: '' }
    })

    // Save changes
    const saveButton = screen.getByText(/sessions.saveChanges/)
    fireEvent.click(saveButton)

    await waitFor(() => {
      expect(mockUpdateSegmentContent).toHaveBeenCalledWith(
        'test-session-id',
        {
          'segment-1': ''
        }
      )
    })
  })

  test('should cancel editing and reset changes', async () => {
    render(<SessionPage transcript={mockTranscript} />)

    // Enter edit mode
    const editButton = screen.getByText(/sessions.editTranscript/)
    fireEvent.click(editButton)

    // Make changes
    const firstSegmentTextarea = screen.getByDisplayValue('Hello, welcome to the session.')
    fireEvent.change(firstSegmentTextarea, {
      target: { value: 'This change should be discarded' }
    })

    // Cancel editing
    const cancelButton = screen.getByText(/sessions.cancelEdit/)
    fireEvent.click(cancelButton)

    // Should exit edit mode without saving
    expect(mockUpdateSegmentContent).not.toHaveBeenCalled()

    // Re-enter edit mode to check if changes were discarded
    fireEvent.click(screen.getByText(/sessions.editTranscript/))
    expect(screen.getByDisplayValue('Hello, welcome to the session.')).toBeInTheDocument()
  })

  test('should handle API errors gracefully', async () => {
    // Mock API failure
    mockUpdateSegmentContent.mockRejectedValue(new Error('API Error'))

    // Mock console.error to suppress error output in test
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})

    // Mock window.alert
    const alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => {})

    render(<SessionPage transcript={mockTranscript} />)

    // Enter edit mode and make changes
    const editButton = screen.getByText(/sessions.editTranscript/)
    fireEvent.click(editButton)

    const firstSegmentTextarea = screen.getByDisplayValue('Hello, welcome to the session.')
    fireEvent.change(firstSegmentTextarea, {
      target: { value: 'Updated content' }
    })

    // Save changes (should fail)
    const saveButton = screen.getByText(/sessions.saveChanges/)
    fireEvent.click(saveButton)

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Failed to save transcript changes:', expect.any(Error))
      expect(alertSpy).toHaveBeenCalled()
    })

    consoleSpy.mockRestore()
    alertSpy.mockRestore()
  })

  test('should preserve segment ordering during editing', async () => {
    render(<SessionPage transcript={mockTranscript} />)

    // Enter edit mode
    const editButton = screen.getByText(/sessions.editTranscript/)
    fireEvent.click(editButton)

    // Get all textareas
    const textareas = screen.getAllByRole('textbox')

    // First textarea should contain the first segment content
    expect(textareas[0]).toHaveValue('Hello, welcome to the session.')
    // Second textarea should contain the second segment content
    expect(textareas[1]).toHaveValue('Thank you for having me.')
  })

  test('should update local transcript state after successful save', async () => {
    render(<SessionPage transcript={mockTranscript} />)

    // Enter edit mode
    const editButton = screen.getByText(/sessions.editTranscript/)
    fireEvent.click(editButton)

    // Update content
    const firstSegmentTextarea = screen.getByDisplayValue('Hello, welcome to the session.')
    fireEvent.change(firstSegmentTextarea, {
      target: { value: 'Locally updated content' }
    })

    // Save changes
    const saveButton = screen.getByText(/sessions.saveChanges/)
    fireEvent.click(saveButton)

    await waitFor(() => {
      expect(mockUpdateSegmentContent).toHaveBeenCalled()
    })

    // After save, should exit edit mode and show updated content
    await waitFor(() => {
      expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
      expect(screen.getByText('Locally updated content')).toBeInTheDocument()
    })
  })

  test('should handle segments without IDs using fallback', async () => {
    const transcriptWithoutIds = {
      ...mockTranscript,
      segments: [
        {
          speaker_id: 1,
          speaker_name: 'Speaker 1',
          start_sec: 0.0,
          end_sec: 5.0,
          content: 'Segment without ID',
        }
      ]
    }

    render(<SessionPage transcript={transcriptWithoutIds} />)

    // Enter edit mode
    const editButton = screen.getByText(/sessions.editTranscript/)
    fireEvent.click(editButton)

    // Update the segment
    const segmentTextarea = screen.getByDisplayValue('Segment without ID')
    fireEvent.change(segmentTextarea, {
      target: { value: 'Updated segment without ID' }
    })

    // Save changes
    const saveButton = screen.getByText(/sessions.saveChanges/)
    fireEvent.click(saveButton)

    await waitFor(() => {
      // Should use fallback ID format: speaker_id-start_sec
      expect(mockUpdateSegmentContent).toHaveBeenCalledWith(
        'test-session-id',
        {
          '1-0': 'Updated segment without ID'
        }
      )
    })
  })

  test('should handle very long content in segments', async () => {
    const longContent = 'A'.repeat(5000)
    const transcriptWithLongContent = {
      ...mockTranscript,
      segments: [
        {
          id: 'long-segment',
          speaker_id: 1,
          speaker_name: 'Speaker 1',
          start_sec: 0.0,
          end_sec: 5.0,
          content: longContent,
        }
      ]
    }

    render(<SessionPage transcript={transcriptWithLongContent} />)

    // Enter edit mode
    const editButton = screen.getByText(/sessions.editTranscript/)
    fireEvent.click(editButton)

    // Should render long content correctly
    const textarea = screen.getByDisplayValue(longContent)
    expect(textarea).toBeInTheDocument()

    // Update with even longer content
    const veryLongContent = 'B'.repeat(10000)
    fireEvent.change(textarea, {
      target: { value: veryLongContent }
    })

    expect(textarea).toHaveValue(veryLongContent)

    // Save changes
    const saveButton = screen.getByText(/sessions.saveChanges/)
    fireEvent.click(saveButton)

    await waitFor(() => {
      expect(mockUpdateSegmentContent).toHaveBeenCalledWith(
        'test-session-id',
        {
          'long-segment': veryLongContent
        }
      )
    })
  })
})