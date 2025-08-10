import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import AudioAnalysisPage from '../page'
import { apiClient } from '@/lib/api'

// Mock the API client
jest.mock('@/lib/api', () => ({
  apiClient: {
    createTranscriptionSession: jest.fn(),
    getUploadUrl: jest.fn(),
    uploadToGCS: jest.fn(),
    confirmUpload: jest.fn(),
    startTranscription: jest.fn(),
    getTranscriptionSession: jest.fn(),
    exportTranscript: jest.fn(),
  },
  downloadBlob: jest.fn(),
}))

// Mock the i18n context
jest.mock('@/contexts/i18n-context', () => ({
  useI18n: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'audio.title': 'Audio Transcription',
        'audio.subtitle': 'Upload and transcribe your audio files',
        'audio.upload_text': 'Upload Audio File',
        'audio.upload_subtext': 'Drag and drop your audio file here',
        'audio.file_info': 'Supported formats: MP3, WAV, M4A, OGG - Max size: 1GB',
        'audio.session_title': 'Session Title',
        'audio.session_title_placeholder': 'Enter session title...',
        'audio.language_selection': 'Language',
        'audio.language_auto': 'Auto Detect',
        'audio.language_zh_tw': 'Traditional Chinese',
        'audio.language_zh_cn': 'Simplified Chinese',
        'audio.language_en': 'English',
        'audio.upload_btn': 'Start Upload & Transcription',
        'audio.invalid_format': 'Invalid file format. Supported: MP3, WAV, M4A, OGG',
        'audio.file_too_large': 'File size exceeds 1GB limit',
        'audio.upload_error': 'Upload failed. Please try again.',
        'audio.status_uploading': 'Uploading...',
        'audio.status_processing': 'Processing...',
        'audio.status_completed': 'Completed',
        'audio.status_failed': 'Failed',
        'audio.retry': 'Retry',
        'audio.new_upload': 'New Upload',
        'audio.auto_delete_warning': 'Files will be automatically deleted after 24 hours for privacy',
        'audio.instructions': 'Instructions',
        'audio.instruction1': 'Select an audio file (MP3, WAV, M4A, OGG)',
        'audio.instruction2': 'Maximum file size: 1GB',
        'audio.instruction3': 'Maximum duration: 120 minutes',
        'audio.instruction4': 'Files are automatically deleted after 24 hours',
        'audio.instruction5': 'Processing typically takes 15-30 minutes',
        'audio.estimated_time': 'Estimated time',
        'menu.experimental': 'Experimental',
      }
      return translations[key] || key
    }
  })
}))

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>

describe('AudioAnalysisPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  test('renders audio analysis page correctly', () => {
    render(<AudioAnalysisPage />)
    
    expect(screen.getByText('Audio Transcription')).toBeInTheDocument()
    expect(screen.getByText('Upload and transcribe your audio files')).toBeInTheDocument()
    expect(screen.getByText('Drag and drop your audio file here')).toBeInTheDocument()
  })

  test('shows file format validation error for invalid files', async () => {
    const user = userEvent.setup()
    render(<AudioAnalysisPage />)
    
    // Create a fake PDF file
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })
    
    // Get the file input using query selector since it's hidden
    const container = screen.getByText('Drag and drop your audio file here').closest('div')
    const input = container?.querySelector('input[type="file"]') as HTMLInputElement
    expect(input).toBeInTheDocument()
    
    await user.upload(input, file)
    
    await waitFor(() => {
      expect(screen.getByText('Invalid file format. Supported: MP3, WAV, M4A, OGG')).toBeInTheDocument()
    })
  })

  test('shows file size validation error for large files', async () => {
    const user = userEvent.setup()
    render(<AudioAnalysisPage />)
    
    // Create a fake large file (>1GB)
    const largeFile = Object.defineProperty(
      new File(['content'], 'test.mp3', { type: 'audio/mpeg' }),
      'size',
      { value: 1024 * 1024 * 1024 + 1 } // 1GB + 1 byte
    )
    
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement
    
    await user.upload(input, largeFile)
    
    await waitFor(() => {
      expect(screen.getByText('File size exceeds 1GB limit')).toBeInTheDocument()
    })
  })

  test('accepts valid audio file and shows upload form', async () => {
    const user = userEvent.setup()
    render(<AudioAnalysisPage />)
    
    // Create a valid MP3 file
    const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' })
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement
    
    await user.upload(input, file)
    
    await waitFor(() => {
      expect(screen.getByText('test.mp3')).toBeInTheDocument()
      expect(screen.getByLabelText(/session title/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/language/i)).toBeInTheDocument()
    })
  })

  test('upload button is disabled without session title', async () => {
    const user = userEvent.setup()
    render(<AudioAnalysisPage />)
    
    // Upload a valid file
    const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' })
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement
    
    await user.upload(input, file)
    
    await waitFor(() => {
      const uploadButton = screen.getByRole('button', { name: /start upload/i })
      expect(uploadButton).toBeDisabled()
    })
  })

  test('successful upload flow', async () => {
    const user = userEvent.setup()
    
    // Mock API responses
    mockApiClient.createTranscriptionSession.mockResolvedValue({ id: 'session-123' })
    mockApiClient.getUploadUrl.mockResolvedValue({ upload_url: 'https://gcs-upload-url' })
    mockApiClient.uploadToGCS.mockResolvedValue(undefined)
    mockApiClient.confirmUpload.mockResolvedValue({ 
      file_exists: true, 
      ready_for_transcription: true,
      message: 'Upload successful' 
    })
    mockApiClient.startTranscription.mockResolvedValue({ task_id: 'task-456' })
    mockApiClient.getTranscriptionSession.mockResolvedValue({ 
      status: 'completed', 
      segments_count: 10,
      stt_cost_usd: '0.50' 
    })
    
    render(<AudioAnalysisPage />)
    
    // Upload a valid file
    const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' })
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement
    
    await user.upload(input, file)
    
    // Fill in session title
    await waitFor(() => {
      expect(screen.getByLabelText(/session title/i)).toBeInTheDocument()
    })
    
    const titleInput = screen.getByLabelText(/session title/i)
    await user.type(titleInput, 'Test Session')
    
    // Start upload
    const uploadButton = screen.getByRole('button', { name: /start upload/i })
    expect(uploadButton).not.toBeDisabled()
    
    await user.click(uploadButton)
    
    // Verify API calls were made
    await waitFor(() => {
      expect(mockApiClient.createTranscriptionSession).toHaveBeenCalledWith({
        title: 'Test Session',
        language: 'zh-TW'
      })
    })
    
    expect(mockApiClient.getUploadUrl).toHaveBeenCalledWith('session-123', 'test.mp3')
    expect(mockApiClient.confirmUpload).toHaveBeenCalledWith('session-123')
    expect(mockApiClient.startTranscription).toHaveBeenCalledWith('session-123')
  })

  test('handles upload errors gracefully', async () => {
    const user = userEvent.setup()
    
    // Mock API error
    mockApiClient.createTranscriptionSession.mockRejectedValue(new Error('API Error'))
    
    render(<AudioAnalysisPage />)
    
    // Upload a valid file
    const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' })
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement
    
    await user.upload(input, file)
    
    // Fill in session title
    await waitFor(() => {
      expect(screen.getByLabelText(/session title/i)).toBeInTheDocument()
    })
    
    const titleInput = screen.getByLabelText(/session title/i)
    await user.type(titleInput, 'Test Session')
    
    // Start upload
    const uploadButton = screen.getByRole('button', { name: /start upload/i })
    await user.click(uploadButton)
    
    // Wait for error to appear
    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeInTheDocument()
    })
    
    // Should show retry button
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
  })

  test('can reset upload after error', async () => {
    const user = userEvent.setup()
    render(<AudioAnalysisPage />)
    
    // Upload a valid file
    const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' })
    const input = screen.getByRole('textbox', { hidden: true }) as HTMLInputElement
    
    await user.upload(input, file)
    
    // Wait for file to be selected and remove button to appear
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /移除/i })).toBeInTheDocument()
    })
    
    // Simulate failed state by clicking remove button
    const removeButton = screen.getByRole('button', { name: /移除/i })
    await user.click(removeButton)
    
    // Should return to initial state
    await waitFor(() => {
      expect(screen.getByText('Drag and drop your audio file here')).toBeInTheDocument()
      expect(screen.queryByText('test.mp3')).not.toBeInTheDocument()
    })
  })
})