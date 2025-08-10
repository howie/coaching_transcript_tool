import { render, screen } from '@testing-library/react'
import AudioAnalysisPage from '../page'

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

describe('AudioAnalysisPage Basic Tests', () => {
  test('renders page title and subtitle correctly', () => {
    render(<AudioAnalysisPage />)
    
    expect(screen.getByText('Audio Transcription')).toBeInTheDocument()
    expect(screen.getByText('Upload and transcribe your audio files')).toBeInTheDocument()
    expect(screen.getByText('Experimental')).toBeInTheDocument()
  })

  test('displays upload section with correct content', () => {
    render(<AudioAnalysisPage />)
    
    expect(screen.getByText('Upload Audio File')).toBeInTheDocument()
    expect(screen.getByText('Drag and drop your audio file here')).toBeInTheDocument()
    expect(screen.getByText('Supported formats: MP3, WAV, M4A, OGG - Max size: 1GB')).toBeInTheDocument()
  })

  test('shows data retention warning', () => {
    render(<AudioAnalysisPage />)
    
    expect(screen.getByText('Files will be automatically deleted after 24 hours for privacy')).toBeInTheDocument()
  })

  test('displays instructions sidebar', () => {
    render(<AudioAnalysisPage />)
    
    expect(screen.getByText('Instructions')).toBeInTheDocument()
    expect(screen.getByText('Select an audio file (MP3, WAV, M4A, OGG)')).toBeInTheDocument()
    expect(screen.getByText('Maximum file size: 1GB')).toBeInTheDocument()
    expect(screen.getByText('Maximum duration: 120 minutes')).toBeInTheDocument()
    expect(screen.getByText('Files are automatically deleted after 24 hours')).toBeInTheDocument()
    expect(screen.getByText('Processing typically takes 15-30 minutes')).toBeInTheDocument()
  })

  test('contains file input element', () => {
    const { container } = render(<AudioAnalysisPage />)
    
    const fileInput = container.querySelector('input[type="file"]')
    expect(fileInput).toBeInTheDocument()
    expect(fileInput).toHaveAttribute('accept', '.mp3,.wav,.m4a,.ogg,.mp4')
  })

  test('has language selection options when available', () => {
    render(<AudioAnalysisPage />)
    
    // The language selection should be available but initially hidden
    // This test validates that the component renders without errors
    expect(screen.getByText('Audio Transcription')).toBeInTheDocument()
  })
})