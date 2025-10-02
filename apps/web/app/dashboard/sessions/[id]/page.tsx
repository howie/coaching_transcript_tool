'use client';

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { PencilIcon, TrashIcon, ArrowLeftIcon, DocumentArrowDownIcon, MicrophoneIcon, DocumentTextIcon, ChartBarIcon, ChatBubbleLeftRightIcon, DocumentMagnifyingGlassIcon, CloudArrowUpIcon, ExclamationTriangleIcon, ArrowUpIcon, UserGroupIcon } from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { useAuth } from '@/contexts/auth-context';
import { useI18n } from '@/contexts/i18n-context';
import { apiClient, TranscriptNotAvailableError } from '@/lib/api';
import { TranscriptionProgress } from '@/components/ui/progress-bar';
import { useTranscriptionStatus, formatTimeRemaining, formatDuration } from '@/hooks/useTranscriptionStatus';
import { AudioUploader } from '@/components/AudioUploader';
import { usePlanLimits } from '@/hooks/usePlanLimits';
import TranscriptSmoothingPanel from '@/components/transcript-smoothing/TranscriptSmoothingPanel';
import TranscriptComparison from '@/components/transcript-smoothing/TranscriptComparison';
import { type SmoothingResponse, type LeMURSmoothingResponse } from '@/lib/api';
import { DeleteTranscriptConfirmDialog } from '@/components/transcript/DeleteTranscriptConfirmDialog';

interface Session {
  id: string;
  session_date: string;
  client_id: string;
  client_name?: string;
  client?: Client;
  duration_min: number;
  fee_currency: string;
  fee_amount: number;
  fee_display: string;
  duration_display: string;
  transcription_session_id?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface TranscriptSegment {
  id: string;
  speaker_id: number;
  start_sec: number;
  end_sec: number;
  content: string;
  confidence?: number;
}

interface TranscriptData {
  session_id: string;
  title: string;
  language: string;
  duration_sec: number;
  segments: TranscriptSegment[];
  created_at: string;
  role_assignments?: { [speakerId: number]: 'coach' | 'client' };
  segment_roles?: { [segmentId: string]: 'coach' | 'client' };
  metadata?: {
    auto_smoothing_applied?: boolean;
    smoothing_stats?: any;
  };
  provider_metadata?: {
    auto_smoothing_applied?: boolean;
    smoothing_stats?: any;
  };
}

interface SpeakingStats {
  coach_speaking_time: number;
  client_speaking_time: number;
  total_speaking_time: number;
  coach_percentage: number;
  client_percentage: number;
  silence_time: number;
}

// Speaker role constants to avoid magic numbers
enum SpeakerRole {
  COACH = 'coach',
  CLIENT = 'client',
  UNKNOWN = 'unknown'
}

// Speaker role constants - using string enums for clarity
const SPEAKER_ROLES = {
  COACH: 'coach' as const,
  CLIENT: 'client' as const
} as const;

// Helper functions for safe role assignment
const getSpeakerRoleFromSegment = (segment: any, roleAssignments?: { [key: number]: 'coach' | 'client' }): SpeakerRole => {
  // First check if segment has direct role field (preferred)
  if (segment.role) {
    // Convert to lowercase for case-insensitive comparison (API returns uppercase)
    const roleStr = String(segment.role).toLowerCase();
    return roleStr === 'coach' ? SpeakerRole.COACH : roleStr === 'client' ? SpeakerRole.CLIENT : SpeakerRole.UNKNOWN;
  }

  // Fallback to role assignments from API
  if (roleAssignments && roleAssignments[segment.speaker_id]) {
    // Convert to lowercase for case-insensitive comparison
    const roleStr = String(roleAssignments[segment.speaker_id]).toLowerCase();
    return roleStr === 'coach' ? SpeakerRole.COACH : roleStr === 'client' ? SpeakerRole.CLIENT : SpeakerRole.UNKNOWN;
  }


  // Last fallback: return UNKNOWN instead of making assumptions
  // This prevents incorrect role assignments when no data is available
  return SpeakerRole.UNKNOWN;
};

const getRoleDisplayName = (role: SpeakerRole, t: any): string => {
  if (role === SpeakerRole.COACH) return t('sessions.coach');
  if (role === SpeakerRole.CLIENT) return t('sessions.client');
  // For UNKNOWN role, show neutral speaker label
  return 'Speaker';
};

const getSpeakerColor = (role: SpeakerRole): string => {
  if (role === SpeakerRole.COACH) return 'text-blue-600';
  if (role === SpeakerRole.CLIENT) return 'text-green-600';
  // For UNKNOWN role, use a neutral color
  return 'text-gray-600';
};

interface Client {
  id: string;
  name: string;
}

const SessionDetailPage = () => {
  const { user, logout } = useAuth();
  const { t } = useI18n();
  const router = useRouter();
  const params = useParams();
  const sessionId = params.id as string;

  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [editMode, setEditMode] = useState(false);
  const [session, setSession] = useState<Session | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
  const [currencies, setCurrencies] = useState<any[]>([]);
  const [formData, setFormData] = useState({
    session_date: '',
    client_id: '',
    duration_min: 60,
    fee_currency: 'TWD',
    fee_amount: 0,
    notes: ''
  });
  const [activeTab, setActiveTab] = useState<'overview' | 'transcript' | 'ai-optimization' | 'analysis'>('overview');
  const [transcript, setTranscript] = useState<TranscriptData | null>(null);
  const [transcriptLoading, setTranscriptLoading] = useState(false);
  const [transcriptDeleted, setTranscriptDeleted] = useState(false);
  const [savedSpeakingStats, setSavedSpeakingStats] = useState<SpeakingStats | null>(null);
  const [exportFormat, setExportFormat] = useState<'txt' | 'xlsx'>('xlsx');
  const [aiAnalysis, setAiAnalysis] = useState<string>('');
  const [chatMessages, setChatMessages] = useState<Array<{role: 'user' | 'assistant', content: string}>>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isGeneratingAnalysis, setIsGeneratingAnalysis] = useState(false);
  const [editingTranscript, setEditingTranscript] = useState(false);
  const [tempRoleAssignments, setTempRoleAssignments] = useState<{ [speakerId: number]: 'coach' | 'client' }>({});
  const [tempSegmentRoles, setTempSegmentRoles] = useState<{ [segmentId: string]: 'coach' | 'client' | 'unknown' }>({});
  const [tempSegmentContent, setTempSegmentContent] = useState<{ [segmentId: string]: string }>({});
  const [uploadMode, setUploadMode] = useState<'audio' | 'transcript'>('audio');
  const [transcriptFile, setTranscriptFile] = useState<File | null>(null);
  const [isUploadingTranscript, setIsUploadingTranscript] = useState(false);
  const [speakerRoleMapping, setSpeakerRoleMapping] = useState<{[speakerId: string]: 'coach' | 'client'}>({});
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeletingTranscript, setIsDeletingTranscript] = useState(false);
  const [previewSegments, setPreviewSegments] = useState<Array<{speaker_id: string, speaker_name: string, content: string, count: number}>>([]);
  const [convertToTraditional, setConvertToTraditional] = useState(false);
  const [canUseAudioAnalysis, setCanUseAudioAnalysis] = useState(true);
  
  // Transcript smoothing states
  const [showSmoothingPanel, setShowSmoothingPanel] = useState(false);
  const [showComparisonModal, setShowComparisonModal] = useState(false);
  const [originalAssemblyAiData, setOriginalAssemblyAiData] = useState<any>(null);
  const [smoothingResult, setSmoothingResult] = useState<SmoothingResponse | null>(null);
  const [smoothingInProgress, setSmoothingInProgress] = useState(false);
  
  // Separate processing states for individual functions
  const [speakerIdentificationInProgress, setSpeakerIdentificationInProgress] = useState(false);
  const [punctuationOptimizationInProgress, setPunctuationOptimizationInProgress] = useState(false);
  
  // Dev-only prompt states
  const [speakerPrompt, setSpeakerPrompt] = useState(getDefaultSpeakerPrompt());
  const [punctuationPrompt, setPunctuationPrompt] = useState(getDefaultPunctuationPrompt());
  const [limitMessage, setLimitMessage] = useState<{
    type: string;
    current: number;
    limit: number;
    message: string;
  } | null>(null);

  // Use plan limits hook
  const { canCreateSession, canTranscribe, validateAction, validateMultiple, lastValidation } = usePlanLimits();

  // Use transcription status hook for progress tracking
  const transcriptionSessionId = session?.transcription_session_id;
  
  // Client information for debugging (removed console.log to prevent infinite loop)
  
  const {
    status: transcriptionStatus,
    session: transcriptionSession,
    loading: statusLoading,
    error: statusError,
    startPolling,
    stopPolling,
    isPolling,
    refetch
  } = useTranscriptionStatus(transcriptionSessionId || null, {
    // Always enable polling if transcriptionSessionId exists, don't restrict by tab to maintain state consistency
    enablePolling: Boolean(transcriptionSessionId)
  });

  // Determine if this session was created from direct transcript upload (not audio)
  const isTranscriptOnly = transcriptionSession?.audio_filename?.endsWith('.manual') || false;

  useEffect(() => {
    if (sessionId) {
      fetchSession();
      fetchClients();
      fetchCurrencies();
      checkUsageLimits();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  // Refresh transcription status when switching back to overview or transcript tabs
  const refetchRef = useRef(refetch);
  refetchRef.current = refetch;

  useEffect(() => {
    if (transcriptionSessionId && (activeTab === 'overview' || activeTab === 'transcript')) {
      refetchRef.current();
    }
  }, [activeTab, transcriptionSessionId]);

  useEffect(() => {
    // Auto-fetch transcript when transcription is completed and we don't have it yet
    if (transcriptionSession?.status === 'completed' && transcriptionSessionId && !transcript) {
      console.log('Transcription completed, fetching transcript...');
      fetchTranscript(transcriptionSessionId);
    }
  }, [transcriptionSession?.status, transcriptionSessionId, transcript]);

  useEffect(() => {
    if (!transcript || !transcript.segments || transcript.segments.length === 0) {
      setTempRoleAssignments({});
      setTempSegmentRoles({});
      return;
    }

    if (transcript.role_assignments) {
      // Convert uppercase roles from API to lowercase for frontend consistency
      const convertedAssignments: { [speakerId: number]: 'coach' | 'client' } = {};
      Object.entries(transcript.role_assignments).forEach(([speakerId, role]) => {
        convertedAssignments[parseInt(speakerId)] = role.toLowerCase() as 'coach' | 'client';
      });
      // Debug: Log role conversion for troubleshooting
      console.log('Role assignments converted:', transcript.role_assignments, '→', convertedAssignments);
      setTempRoleAssignments(convertedAssignments);
    } else {
      const speakerIds = transcript.segments.map(s => s.speaker_id);
      const uniqueSpeakers = Array.from(new Set(speakerIds));
      const defaultAssignments: { [speakerId: number]: 'coach' | 'client' } = {};
      uniqueSpeakers.forEach((speakerId, index) => {
        defaultAssignments[speakerId] = index === 0 ? 'coach' : 'client';
      });
      setTempRoleAssignments(defaultAssignments);
    }

    const segmentRoles: { [segmentId: string]: 'coach' | 'client' | 'unknown' } = {};
    transcript.segments.forEach((segment) => {
      const segmentId = segment.id || `${segment.speaker_id}-${segment.start_sec}`;
      if (transcript.segment_roles && transcript.segment_roles[segmentId]) {
        // Convert uppercase roles from API to lowercase
        segmentRoles[segmentId] = transcript.segment_roles[segmentId].toLowerCase() as 'coach' | 'client';
      } else if (transcript.role_assignments && transcript.role_assignments[segment.speaker_id]) {
        // Convert uppercase roles from API to lowercase
        segmentRoles[segmentId] = transcript.role_assignments[segment.speaker_id].toLowerCase() as 'coach' | 'client';
      } else {
        const role = getSpeakerRoleFromSegment(segment, transcript.role_assignments);
        segmentRoles[segmentId] = role === SpeakerRole.COACH ? 'coach' :
                                   role === SpeakerRole.CLIENT ? 'client' : 'unknown';
      }
    });
    setTempSegmentRoles(segmentRoles);
  }, [transcript]);

  const speakingStats = useMemo<SpeakingStats | null>(() => {
    if (!transcript || !transcript.segments || transcript.segments.length === 0) {
      return null;
    }

    let coachTime = 0;
    let clientTime = 0;

    transcript.segments.forEach(segment => {
      const duration = segment.end_sec - segment.start_sec;
      const segmentId = segment.id || `${segment.speaker_id}-${segment.start_sec}`;

      let roleString: 'coach' | 'client';
      if (tempSegmentRoles[segmentId] && tempSegmentRoles[segmentId] !== 'unknown') {
        roleString = tempSegmentRoles[segmentId] as 'coach' | 'client';
      } else if (tempRoleAssignments[segment.speaker_id]) {
        roleString = tempRoleAssignments[segment.speaker_id];
      } else {
        const defaultRole = getSpeakerRoleFromSegment(segment, transcript.role_assignments);
        roleString = defaultRole === SpeakerRole.COACH ? 'coach' : 'client';
      }

      if (roleString === 'coach') {
        coachTime += duration;
      } else {
        clientTime += duration;
      }
    });

    const totalSpeaking = coachTime + clientTime;

    let totalDuration = 0;
    if (transcript.segments.length > 0) {
      const sortedSegments = transcript.segments.slice().sort((a, b) => a.start_sec - b.start_sec);
      const firstStart = sortedSegments[0].start_sec;
      const lastEnd = Math.max(...transcript.segments.map(s => s.end_sec));
      totalDuration = lastEnd - firstStart;
    }

    const silenceTime = Math.max(0, totalDuration - totalSpeaking);

    return {
      coach_speaking_time: coachTime,
      client_speaking_time: clientTime,
      total_speaking_time: totalSpeaking,
      coach_percentage: totalSpeaking > 0 ? (coachTime / totalSpeaking) * 100 : 0,
      client_percentage: totalSpeaking > 0 ? (clientTime / totalSpeaking) * 100 : 0,
      silence_time: silenceTime
    };
  }, [transcript, tempRoleAssignments, tempSegmentRoles]);

  const checkUsageLimits = useCallback(async () => {
    try {
      // Check if user can create sessions and transcriptions
      const results = await validateMultiple([
        { action: 'create_session', params: {} },
        { action: 'transcribe', params: {} }
      ], { silent: true });

      if (!results) {
        // If any check fails, get detailed info for display
        await validateAction('create_session', {}, { silent: true });
        
        if (!lastValidation?.allowed) {
          setCanUseAudioAnalysis(false);
          setLimitMessage({
            type: 'sessions',
            current: lastValidation?.limit_info?.current || 0,
            limit: lastValidation?.limit_info?.limit || 0,
            message: t('limits.sessionLimitReached')
          });
          return;
        }

        await validateAction('transcribe', {}, { silent: true });
        
        if (!lastValidation?.allowed) {
          setCanUseAudioAnalysis(false);
          setLimitMessage({
            type: 'transcriptions',
            current: lastValidation?.limit_info?.current || 0,
            limit: lastValidation?.limit_info?.limit || 0,
            message: t('limits.transcriptionLimitReached')
          });
          return;
        }
      }

      // All checks passed
      setCanUseAudioAnalysis(true);
      setLimitMessage(null);
      
    } catch (error) {
      console.error('Error checking usage limits:', error);
      // On error, allow usage (fail open)
      setCanUseAudioAnalysis(true);
      setLimitMessage(null);
    }
  }, [validateMultiple, validateAction, lastValidation, t]);

  const fetchSession = async () => {
    try {
      const data = await apiClient.getSession(sessionId);
      console.log('✅ fetchSession - API response:', {
        sessionId: data.id,
        transcription_session_id: data.transcription_session_id,
        client_id: data.client_id,
        hasTranscriptionId: Boolean(data.transcription_session_id)
      });
      
      setSession(data);
      setFormData({
        session_date: data.session_date,
        client_id: data.client_id,
        duration_min: data.duration_min,
        fee_currency: data.fee_currency,
        fee_amount: data.fee_amount,
        notes: data.notes || ''
      });
      
      // Check for transcription session
      if (data.transcription_session_id) {
        console.log('🔍 Found existing transcription session:', data.transcription_session_id);
        
        // Don't automatically fetch transcript here - let the useEffect in line 145 handle it
        // when transcription status shows completed. This avoids unnecessary API calls for
        // sessions that are still processing.
        console.log('ℹ️ Transcription session found, status will be checked via polling');
      } else {
        console.log('❌ No transcription session found - transcription_session_id is null/undefined');
      }
    } catch (error: any) {
      console.error('Failed to fetch session:', error);
      
      // Check if it's a 404 (session not found) or authorization error
      const status = error.status;
      if (status === 404 || status === 401 || status === 403) {
        console.log(`Session error (${status}): ${status === 404 ? 'Session not found' : 'Unauthorized access'}, logging out...`);
        // Force logout and redirect to login
        logout();
        router.push('/login');
        return;
      }
      
      setSession(null);
    } finally {
      setFetching(false);
    }
  };

  const fetchClients = async () => {
    try {
      const response = await apiClient.getClients(1, 100);
      setClients(response.items);
    } catch (error) {
      console.error('Failed to fetch clients:', error);
    }
  };

  const fetchTranscript = async (audioSessionId: string) => {
    try {
      setTranscriptLoading(true);
      const response = await apiClient.exportTranscript(audioSessionId, 'json');
      
      // The export API returns a Blob, we need to convert it to text
      if (response instanceof Blob) {
        const textContent = await response.text();
        try {
          const parsed = JSON.parse(textContent) as TranscriptData;

          // Debug: Log what we received from API
          console.log('=== DEBUG: Transcript Data from API ===');
          console.log('role_assignments:', parsed.role_assignments);
          console.log('segment_roles:', parsed.segment_roles);
          if (parsed.segments && parsed.segments.length > 0) {
            console.log('First 5 segments:');
            parsed.segments.slice(0, 5).forEach((seg: any, idx: number) => {
              console.log(`  Segment ${idx}: speaker_id=${seg.speaker_id}, role="${seg.role}"`);
            });
          }
          console.log('=== END DEBUG ===');

          setTranscript(parsed);
        } catch (e) {
          console.error('Failed to parse transcript JSON:', e);
        }
      } else if (typeof response === 'string') {
        try {
          const parsed = JSON.parse(response) as TranscriptData;
          setTranscript(parsed);
        } catch (e) {
          console.error('Failed to parse transcript JSON:', e);
        }
      } else {
        console.warn('Unexpected response type from exportTranscript:', typeof response);
      }
    } catch (error: any) {
      // Check if this is the expected "transcript not available" error
      if (error.name === 'TranscriptNotAvailableError') {
        // This is normal - transcription hasn't completed yet or no segments exist
        console.log('Transcript not available yet:', error.message);
      } else {
        console.error('Failed to fetch transcript:', error);
      }
    } finally {
      setTranscriptLoading(false);
    }
  };

  const handleExportTranscript = async () => {
    if (!transcriptionSessionId) return;
    
    try {
      const response = await apiClient.exportTranscript(transcriptionSessionId, exportFormat);
      
      let blob: Blob;
      if (response instanceof Blob) {
        blob = response;
      } else {
        // Fallback for string response
        let contentType = 'text/plain';
        if (exportFormat === 'xlsx') {
          contentType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
        }
        blob = new Blob([response], { type: contentType });
      }
      
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `transcript-${session.id}.${exportFormat}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export transcript:', error);
    }
  };

  const formatTime = (seconds: number) => {
    // Handle invalid or undefined values
    if (typeof seconds !== 'number' || isNaN(seconds) || seconds < 0) {
      return '00:00';
    }
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getSpeakerLabel = (speakerId: number) => {
    // Create a fake segment object for compatibility
    const fakeSegment = { speaker_id: speakerId };
    const role = getSpeakerRoleFromSegment(fakeSegment, transcript?.role_assignments);

    if (role === SpeakerRole.UNKNOWN) {
      return `Speaker ${speakerId}`;
    }
    return getRoleDisplayName(role, t);
  };

  const getSegmentSpeakerLabel = (segment: TranscriptSegment) => {
    const segmentId = segment.id || `${segment.speaker_id}-${segment.start_sec}`;

    // Priority: segment-level role > speaker-level role > default convention
    let roleString: string;
    if (tempSegmentRoles[segmentId]) {
      roleString = tempSegmentRoles[segmentId];
    } else if (tempRoleAssignments[segment.speaker_id]) {
      roleString = tempRoleAssignments[segment.speaker_id];
    } else {
      // Use safe fallback
      const defaultRole = getSpeakerRoleFromSegment(segment, transcript?.role_assignments);
      roleString = defaultRole === SpeakerRole.COACH ? 'coach' :
                   defaultRole === SpeakerRole.CLIENT ? 'client' : 'unknown';
    }

    const role = roleString === 'coach' ? SpeakerRole.COACH :
                 roleString === 'client' ? SpeakerRole.CLIENT : SpeakerRole.UNKNOWN;
    return getRoleDisplayName(role, t);
  };

  const getSpeakerColorFromId = (speakerId: number) => {
    const fakeSegment = { speaker_id: speakerId };
    const role = getSpeakerRoleFromSegment(fakeSegment, transcript?.role_assignments);
    return getSpeakerColor(role);
  };


  const generateAISummary = async () => {
    if (!transcript || !transcript.segments.length) return;
    
    setIsGeneratingAnalysis(true);
    try {
      // Mock AI analysis - in real implementation, this would call an AI service
      const duration = speakingStats ? formatDuration(speakingStats.total_speaking_time + speakingStats.silence_time) : formatDuration(transcript.duration_sec);
      const coachPct = speakingStats?.coach_percentage.toFixed(1) || '0';
      const clientPct = speakingStats?.client_percentage.toFixed(1) || '0';
      
      const sessionDurationText = t('sessions.aiAnalysisSessionDuration')
        .replace('{duration}', duration)
        .replace('{coachPct}', coachPct)
        .replace('{clientPct}', clientPct);
      
      const mockSummary = `## ${t('sessions.aiAnalysisSummaryTitle')}

${sessionDurationText}

### ${t('sessions.aiAnalysisMainTopicsTitle')}
- ${t('sessions.aiAnalysisMainTopic1')}
- ${t('sessions.aiAnalysisMainTopic2')}
- ${t('sessions.aiAnalysisMainTopic3')}

### ${t('sessions.aiAnalysisCoachObservationTitle')}
- ${t('sessions.aiAnalysisObservation1')}
- ${t('sessions.aiAnalysisObservation2')}
- ${t('sessions.aiAnalysisObservation3')}

### ${t('sessions.aiAnalysisFollowUpTitle')}
1. ${t('sessions.aiAnalysisFollowUp1')}
2. ${t('sessions.aiAnalysisFollowUp2')}
3. ${t('sessions.aiAnalysisFollowUp3')}`;
      
      setAiAnalysis(mockSummary);
      
      // Also add to chat history
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: mockSummary
      }]);
      
    } catch (error) {
      console.error('Failed to generate AI summary:', error);
    } finally {
      setIsGeneratingAnalysis(false);
    }
  };

  const sendChatMessage = async () => {
    if (!currentMessage.trim()) return;
    
    const userMessage = currentMessage;
    setCurrentMessage('');
    setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    
    // Mock AI response - in real implementation, this would call an AI service
    setTimeout(() => {
      const mockResponse = `${t('sessions.aiChatResponseIntro')}

1. ${t('sessions.aiChatResponse1')}
2. ${t('sessions.aiChatResponse2')}
3. ${t('sessions.aiChatResponse3')}

${t('sessions.aiChatFollowUp')}`;
      setChatMessages(prev => [...prev, { role: 'assistant', content: mockResponse }]);
    }, 1000);
  };

  const saveTranscriptChanges = async () => {
    if (!transcriptionSessionId) return;
    
    try {
      // Save segment-level role assignments via API (filter out 'unknown' values)
      const filteredSegmentRoles = Object.fromEntries(
        Object.entries(tempSegmentRoles).filter(([_, role]) => role !== 'unknown')
      ) as { [segmentId: string]: 'coach' | 'client' };
      await apiClient.updateSegmentRoles(transcriptionSessionId, filteredSegmentRoles);
      
      // Save segment content changes via API (only if there are actual changes)
      if (Object.keys(tempSegmentContent).length > 0) {
        try {
          const contentResult = await apiClient.updateSegmentContent(transcriptionSessionId, tempSegmentContent);
          if (!contentResult.success) {
            console.warn('Content update not available:', contentResult.message);
          }
        } catch (error: any) {
          console.error('Failed to update segment content:', error);

          // Provide more specific error messages to users
          let errorMessage = t('sessions.saveTranscriptError') || 'Failed to save transcript changes';

          if (error.message.includes('No segment content provided')) {
            errorMessage = t('sessions.noContentToSave') || 'No content changes to save';
          } else if (error.message.includes('permission') || error.message.includes('Access denied')) {
            errorMessage = t('sessions.accessDeniedError') || 'You do not have permission to edit this transcript';
          } else if (error.message.includes('Session') && error.message.includes('not found')) {
            errorMessage = t('sessions.sessionNotFoundError') || 'Session not found or no longer available';
          } else if (error.message.includes('completed sessions')) {
            errorMessage = t('sessions.sessionNotEditableError') || 'Only completed sessions can be edited';
          }

          alert(errorMessage);
          throw error; // Re-throw to prevent saving role changes if content update failed
        }
      }
      
      // Update local transcript data to include both roles and content changes
      setTranscript(prev => prev ? {
        ...prev,
        role_assignments: tempRoleAssignments,  // Keep speaker-level for compatibility
        segment_roles: filteredSegmentRoles,  // Add segment-level roles (filtered)
        segments: prev.segments.map(segment => {
          const segmentId = segment.id || `${segment.speaker_id}-${segment.start_sec}`;
          return {
            ...segment,
            content: tempSegmentContent[segmentId] || segment.content
          };
        })
      } : null);
      
      setEditingTranscript(false);
    } catch (error) {
      console.error('Failed to save transcript changes:', error);
      alert(t('sessions.saveTranscriptError') || 'Failed to save transcript changes');
    }
  };

  const cancelTranscriptEditing = () => {
    // Reset to original assignments (convert uppercase API values to lowercase)
    if (transcript?.role_assignments) {
      const convertedAssignments: { [speakerId: number]: 'coach' | 'client' } = {};
      Object.entries(transcript.role_assignments).forEach(([speakerId, role]) => {
        convertedAssignments[parseInt(speakerId)] = role.toLowerCase() as 'coach' | 'client';
      });
      console.log('DEBUG cancelTranscriptEditing: Converting role_assignments:', transcript.role_assignments, '→', convertedAssignments);
      setTempRoleAssignments(convertedAssignments);
    }

    // Reset segment roles to original state
    if (transcript && transcript.segments) {
      const originalSegmentRoles: { [segmentId: string]: 'coach' | 'client' | 'unknown' } = {};
      transcript.segments.forEach((segment) => {
        const segmentId = segment.id || `${segment.speaker_id}-${segment.start_sec}`;
        // Use saved segment roles if available, otherwise use speaker roles or default
        if (transcript.segment_roles && transcript.segment_roles[segmentId]) {
          originalSegmentRoles[segmentId] = transcript.segment_roles[segmentId].toLowerCase() as 'coach' | 'client';
        } else if (transcript.role_assignments && transcript.role_assignments[segment.speaker_id]) {
          originalSegmentRoles[segmentId] = transcript.role_assignments[segment.speaker_id].toLowerCase() as 'coach' | 'client';
        } else {
          const defaultRole = getSpeakerRoleFromSegment(segment, transcript?.role_assignments);
          originalSegmentRoles[segmentId] = defaultRole === SpeakerRole.COACH ? 'coach' :
                                            defaultRole === SpeakerRole.CLIENT ? 'client' : 'unknown';
        }
      });
      console.log('DEBUG cancelTranscriptEditing: Setting originalSegmentRoles:', originalSegmentRoles);
      setTempSegmentRoles(originalSegmentRoles);
    }
    
    // Reset content changes
    setTempSegmentContent({});
    
    setEditingTranscript(false);
  };

  const handleDeleteTranscript = async () => {
    if (!sessionId || !user) return;

    setIsDeletingTranscript(true);
    try {
      // Save speaking stats before deletion
      if (speakingStats) {
        setSavedSpeakingStats(speakingStats);
      }

      await apiClient.deleteSessionTranscript(sessionId);

      // Refresh session data
      await fetchSession();
      setTranscript(null);
      setTranscriptDeleted(true);  // Mark that transcript was deleted
      setShowDeleteConfirm(false);

      // Show success message
      alert('逐字稿已刪除，教練 session 和統計資料已保留');
    } catch (error) {
      console.error('Delete transcript error:', error);
      alert(error instanceof Error ? error.message : '刪除逐字稿失敗');
    } finally {
      setIsDeletingTranscript(false);
    }
  };

  const handleTranscriptFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const fileExtension = file.name.split('.').pop()?.toLowerCase();
      if (fileExtension === 'vtt' || fileExtension === 'srt') {
        setTranscriptFile(file);
        // Parse and preview the file to identify speakers
        await parseFilePreview(file);
      } else {
        alert(t('sessions.selectVttSrtFile'));
      }
    }
  };

  const parseFilePreview = async (file: File) => {
    try {
      const content = await file.text();
      const fileExtension = file.name.split('.').pop()?.toLowerCase();
      
      let speakers: {[speakerKey: string]: {speaker_name: string, content: string[], count: number}} = {};
      
      if (fileExtension === 'vtt') {
        // Parse VTT content
        const lines = content.split('\n');
        for (let i = 0; i < lines.length; i++) {
          const line = lines[i].trim();
          if (line.includes('-->')) {
            i++;
            if (i < lines.length) {
              const contentLine = lines[i].trim();
              let speakerName = 'Unknown Speaker';
              let speakerKey = 'speaker_1';
              let actualContent = contentLine;
              
              // Extract speaker from VTT format like <v jolly shih>content</v> or <v Speaker>content</v>
              const speakerMatch = contentLine.match(/<v\s+([^>]+)>\s*(.*?)(?:<\/v>)?$/);
              if (speakerMatch) {
                speakerName = speakerMatch[1].trim();
                actualContent = speakerMatch[2];
                // Use speaker name as key, normalize for consistency
                speakerKey = `speaker_${speakerName.toLowerCase().replace(/\s+/g, '_').replace(/[^\w_]/g, '')}`;
              } else {
                // Handle case without explicit speaker tag (e.g., "教練: content" or "Coach: content")
                const fallbackMatch = contentLine.match(/^([^:：]+)[：:]\s*(.*)$/);
                if (fallbackMatch) {
                  speakerName = fallbackMatch[1].trim();
                  actualContent = fallbackMatch[2];
                  speakerKey = `speaker_${speakerName.toLowerCase().replace(/\s+/g, '_').replace(/[^\w_]/g, '')}`;
                }
              }
              
              if (!speakers[speakerKey]) {
                speakers[speakerKey] = { speaker_name: speakerName, content: [], count: 0 };
              }
              speakers[speakerKey].content.push(actualContent);
              speakers[speakerKey].count++;
            }
          }
        }
      } else if (fileExtension === 'srt') {
        // Parse SRT content
        const blocks = content.split(/\n\s*\n/);
        for (const block of blocks) {
          const lines = block.trim().split('\n');
          if (lines.length >= 3) {
            const contentLines = lines.slice(2);
            const contentText = contentLines.join(' ');
            
            let speakerName = 'Unknown Speaker';
            let speakerKey = 'speaker_1';
            let actualContent = contentText;
            
            // Extract speaker from SRT format like "jolly shih: content" or "教練: content"
            const speakerMatch = contentText.match(/^([^:：]+)[：:]\s*(.*)$/);
            if (speakerMatch) {
              speakerName = speakerMatch[1].trim();
              actualContent = speakerMatch[2];
              speakerKey = `speaker_${speakerName.toLowerCase().replace(/\s+/g, '_').replace(/[^\w_]/g, '')}`;
            }
            
            if (!speakers[speakerKey]) {
              speakers[speakerKey] = { speaker_name: speakerName, content: [], count: 0 };
            }
            speakers[speakerKey].content.push(actualContent);
            speakers[speakerKey].count++;
          }
        }
      }
      
      // Create preview segments
      const segments = Object.entries(speakers).map(([speakerKey, data]) => ({
        speaker_id: speakerKey,
        speaker_name: data.speaker_name,
        content: data.content.slice(0, 3).join(' ').substring(0, 100) + (data.content.length > 3 || data.content.join(' ').length > 100 ? '...' : ''),
        count: data.count
      }));
      
      setPreviewSegments(segments);
      
      // Initialize default role mapping - simple and predictable
      const defaultMapping: {[speakerId: string]: 'coach' | 'client'} = {};
      
      segments.forEach((segment, index) => {
        // Simple rule: first speaker defaults to coach, others default to client
        // User can easily change this in the UI
        if (index === 0) {
          defaultMapping[segment.speaker_id] = 'coach';
        } else {
          defaultMapping[segment.speaker_id] = 'client';
        }
      });
      
      setSpeakerRoleMapping(defaultMapping);
      console.log('Initialized speaker role mapping:', defaultMapping);
      
    } catch (error) {
      console.error('Error parsing file preview:', error);
      alert(t('sessions.parseFileError'));
    }
  };

  const handleTranscriptUpload = async () => {
    if (!transcriptFile || !session) return;
    
    console.log('Starting transcript upload with speaker role mapping:', speakerRoleMapping);
    
    setIsUploadingTranscript(true);
    try {
      // Create a new API call for direct transcript upload to session
      const response = await apiClient.uploadSessionTranscript(
        session.id, 
        transcriptFile, 
        speakerRoleMapping,
        convertToTraditional
      );
      
      console.log('Upload response:', response);
      
      // Update the session with transcription session ID immediately
      if (response.transcription_session_id) {
        setSession(prev => prev ? {
          ...prev,
          transcription_session_id: response.transcription_session_id
        } : null);
      }
      
      // Refresh session and transcript data
      await fetchSession();
      
      // If we have a transcription session ID, fetch the transcript
      const newTranscriptionSessionId = response.transcription_session_id || session.transcription_session_id;
      if (newTranscriptionSessionId) {
        // Force refetch transcription status and transcript
        if (refetch) {
          await refetch();
        }
        await fetchTranscript(newTranscriptionSessionId);
      }
      
      // Reset upload state
      setTranscriptFile(null);
      setPreviewSegments([]);
      setSpeakerRoleMapping({});
      
      // Show success feedback
      alert(t('sessions.uploadSuccess').replace('{count}', response.segments_count));
      
      // Switch to transcript tab to show the uploaded content
      setActiveTab('transcript');
      
      // Set upload mode back to audio for future uploads
      setUploadMode('audio');
      
    } catch (error) {
      console.error('Failed to upload transcript:', error);
      let errorMessage = t('sessions.uploadFailed');
      if (error instanceof Error) {
        errorMessage = error.message;
      }
      alert(errorMessage);
    } finally {
      setIsUploadingTranscript(false);
    }
  };

  const fetchCurrencies = async () => {
    try {
      const data = await apiClient.getCurrencies();
      // Validate that data is an array with the expected structure
      if (Array.isArray(data) && data.length > 0 && 
          data.every(item => item && typeof item === 'object' && 'value' in item && 'label' in item)) {
        setCurrencies(data);
      } else {
        console.warn('Invalid currency data format, using defaults');
        setCurrencies([
          { value: 'TWD', label: t('sessions.currencyTWD') },
          { value: 'USD', label: t('sessions.currencyUSD') },
          { value: 'CNY', label: t('sessions.currencyCNY') }
        ]);
      }
    } catch (error) {
      console.error('Failed to fetch currencies:', error);
      setCurrencies([
        { value: 'TWD', label: `TWD - ${t('sessions.twdCurrency')}` },
        { value: 'USD', label: `USD - ${t('sessions.usdCurrency')}` },
        { value: 'CNY', label: `CNY - ${t('sessions.cnyCurrency')}` }
      ]);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await apiClient.updateSession(sessionId, {
        ...formData,
        fee_amount: Number(formData.fee_amount),
        duration_min: Number(formData.duration_min)
      });
      setEditMode(false);
      fetchSession();
    } catch (error) {
      console.error('Failed to update session:', error);
      alert(t('sessions.updateError') || 'Failed to update session');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm(t('sessions.confirmDelete'))) return;

    try {
      await apiClient.deleteSession(sessionId);
      router.push('/dashboard/sessions');
    } catch (error) {
      console.error('Failed to delete session:', error);
      alert(t('sessions.deleteError') || 'Failed to delete session');
    }
  };

  if (fetching) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">{t('sessions.loading')}</div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Session not found</div>
      </div>
    );
  }

  // Default prompt getters for dev mode
  function getDefaultSpeakerPrompt(): string {
    return `你是一個專業的教練對話分析師。請分析以下教練對話逐字稿，並識別說話者身份。

這是一段教練(Coach)與客戶(Client)的對話。請判斷每個說話者是「教練」還是「客戶」。

教練的特徵：
- 會問開放性問題（如「你可以多說一點嗎？」「你覺得呢？」）
- 會引導對話方向和深入探索
- 會提供反饋、觀察和建議
- 語調通常比較引導性和支持性
- 會使用教練技巧如重述、澄清、挑戰

客戶的特徵：
- 主要分享自己的情況、感受和經歷
- 回答教練的問題和探索
- 尋求幫助、建議或解決方案
- 語調比較敘述性和個人化
- 會表達困惑、糾結或需要支持的狀況

請回覆一個JSON格式的說話者對應表，將原始說話者標籤對應到正確的角色（使用繁體中文）：
例如：{"A": "教練", "B": "客戶"} 或 {"Speaker A": "教練", "Speaker B": "客戶"}

只回覆JSON，不要其他說明，請確保使用繁體中文。`;
  }

  function getDefaultPunctuationPrompt(): string {
    return `你是一個專業的繁體中文文本編輯師。請改善以下教練對話逐字稿的標點符號和斷句。

重要格式要求：
1. 必須使用繁體中文字（Traditional Chinese）輸出
2. 中文字之間不要加空格，保持中文連續書寫習慣
3. 只在標點符號後面可以有空格（如果需要的話）
4. 保持說話者標籤和對話結構不變
5. 使用繁體中文全形標點符號（，。？！）

標點符號改善任務：
1. 在長段落內部添加適當的逗號、句號、問號、驚嘆號
2. 每個完整的思想或意思單元要用逗號分隔
3. 每個完整的句子要用句號結尾
4. 疑問句要用問號結尾
5. 感嘆或強調要用驚嘆號
6. 轉折詞（但是、然後、所以、因為）前後要加逗號
7. 列舉項目之間要用逗號分隔
8. 將所有簡體中文轉換為繁體中文

範例格式：
教練: 好，Lisha你好，我是你今天的教練，那我待會錄音，並且會做一些筆記，你OK嗎？

回覆改善後的逐字稿，嚴格保持相同格式（說話者: 內容），只改善標點符號，不要在中文字之間加空格，並確保使用繁體中文。`;
  }

  // AI Optimization handlers using LeMUR
  const handleSmoothTranscript = async () => {
    if (!transcript || !sessionId || smoothingInProgress) return;
    
    setSmoothingInProgress(true);
    
    try {
      let assemblyAiData: any = null;
      
      // Try to get the raw AssemblyAI data first
      try {
        const rawDataResponse = await apiClient.getRawAssemblyAiData(sessionId);
        if (rawDataResponse.success && rawDataResponse.raw_data) {
          assemblyAiData = rawDataResponse.raw_data;
        }
      } catch (error) {
        console.warn('Could not get raw AssemblyAI data, creating from current transcript:', error);
      }
      
      // If no raw data, create from current transcript segments
      if (!assemblyAiData) {
        assemblyAiData = {
          utterances: transcript.segments.map(segment => ({
            speaker: String.fromCharCode(65 + segment.speaker_id - 1), // Convert 1,2 -> A,B
            start: Math.round(segment.start_sec * 1000), // Convert to milliseconds
            end: Math.round(segment.end_sec * 1000),
            text: segment.content,
            confidence: segment.confidence || 0.9
          })),
          language_code: transcript.language || 'zh'
        };
      }
      
      // Determine language for LeMUR processing
      const language = transcript.language?.startsWith('zh') ? 'chinese' : 
                     transcript.language?.startsWith('en') ? 'english' : 'auto';
      
      console.log('🧠 Sending transcript to LeMUR for AI optimization...');
      console.log('Data to send:', { utterances: assemblyAiData.utterances?.length, language });
      
      // Prepare custom prompts for dev mode
      const customPrompts = process.env.NODE_ENV === 'development' ? {
        speakerPrompt: speakerPrompt.trim(),
        punctuationPrompt: punctuationPrompt.trim()
      } : undefined;
      
      console.log('Using custom prompts:', customPrompts ? 'Yes' : 'No');
      
      // Send to LeMUR for AI-powered optimization
      const lemurResult = await apiClient.lemurSmoothTranscript(assemblyAiData, language, customPrompts);
      
      if (lemurResult.success && lemurResult.segments?.length > 0) {
        // Apply the LeMUR optimized transcript directly
        await applyLeMUROptimization(lemurResult);
        
        // Show success message
        alert(`✅ AI 優化完成！\n\n改善項目：\n${lemurResult.improvements_made.join('\n')}\n\n說話者對應：${JSON.stringify(lemurResult.speaker_mapping, null, 2)}`);
      } else {
        throw new Error('LeMUR optimization returned no results');
      }
      
    } catch (error) {
      console.error('AI optimization failed:', error);
      alert(`❌ AI 優化失敗：${error instanceof Error ? error.message : '未知錯誤'}`);
    } finally {
      setSmoothingInProgress(false);
    }
  };

  // Apply LeMUR optimization results to current transcript
  const applyLeMUROptimization = async (lemurResult: LeMURSmoothingResponse) => {
    if (!transcript) return;
    
    // Convert LeMUR segments to our transcript format
    const optimizedSegments = lemurResult.segments.map((segment, index: number) => ({
      id: `lemur-${index}`,
      speaker_id: segment.speaker === '教練' || segment.speaker === 'Coach' ? 1 : 2,
      start_sec: segment.start_ms / 1000,
      end_sec: segment.end_ms / 1000,
      content: segment.text,
      confidence: 0.98 // High confidence for AI-optimized content
    }));
    
    // Create updated transcript
    // Calculate correct duration for optimized transcript
    let optimizedDuration = 0;
    if (optimizedSegments.length > 0) {
      const sortedSegments = optimizedSegments.slice().sort((a, b) => a.start_sec - b.start_sec);
      const firstStart = sortedSegments[0].start_sec;
      const lastEnd = Math.max(...optimizedSegments.map(s => s.end_sec));
      optimizedDuration = lastEnd - firstStart;
    }
    
    const optimizedTranscript: TranscriptData = {
      ...transcript,
      segments: optimizedSegments,
      duration_sec: optimizedDuration
    };
    
    // Update the state to show optimized transcript
    setTranscript(optimizedTranscript);
    
    console.log('✅ Applied LeMUR optimization:', {
      originalSegments: transcript.segments.length,
      optimizedSegments: optimizedSegments.length,
      speakerMapping: lemurResult.speaker_mapping,
      improvements: lemurResult.improvements_made
    });
  };

  // Handle speaker identification only
  const handleSpeakerIdentification = async () => {
    if (!transcript || !sessionId || speakerIdentificationInProgress) return;
    
    setSpeakerIdentificationInProgress(true);
    
    try {
      // IMPORTANT: sessionId here could be either:
      // 1. Coaching Session ID (from URL like /dashboard/sessions/{id})
      // 2. Transcript Session ID (direct transcript processing)
      // Backend API will automatically resolve the correct transcript session ID
      const lemurResult = await apiClient.lemurSpeakerIdentificationFromDB(
        sessionId, // Backend will resolve: coaching_session -> transcription_session_id
        { speakerPrompt }
      );

      // Database has been updated - reload transcript from server
      // Use transcript session ID for export API (fetchTranscript expects transcript session ID)
      const transcriptSessionId = session?.transcription_session_id || sessionId;
      await fetchTranscript(transcriptSessionId);
      
      console.log('✅ Applied speaker identification (DB updated):', {
        speakerMapping: lemurResult.speaker_mapping,
        improvementsMade: lemurResult.improvements_made,
      });

      alert('✅ 說話者識別已完成並應用！資料庫已更新。');
    } catch (error) {
      console.error('Speaker identification failed:', error);
      alert(`❌ 說話者識別失敗：${error instanceof Error ? error.message : '未知錯誤'}`);
    } finally {
      setSpeakerIdentificationInProgress(false);
    }
  };

  // Handle punctuation optimization only
  const handlePunctuationOptimization = async () => {
    if (!transcript || !sessionId || punctuationOptimizationInProgress) return;
    
    setPunctuationOptimizationInProgress(true);
    
    try {
      // IMPORTANT: sessionId resolution handled by backend
      // See docs/claude/session-id-mapping.md for details
      const lemurResult = await apiClient.lemurPunctuationOptimizationFromDB(
        sessionId, // Backend will resolve: coaching_session -> transcription_session_id
        { punctuationPrompt }
      );

      // Database has been updated - reload transcript from server
      // Use transcript session ID for export API (fetchTranscript expects transcript session ID)
      const transcriptSessionId = session?.transcription_session_id || sessionId;
      await fetchTranscript(transcriptSessionId);
      
      console.log('✅ Applied punctuation optimization (DB updated):', {
        improvementsMade: lemurResult.improvements_made,
      });

      alert('✅ 標點符號優化已完成並應用！資料庫已更新。');
    } catch (error) {
      console.error('Punctuation optimization failed:', error);
      alert(`❌ 標點符號優化失敗：${error instanceof Error ? error.message : '未知錯誤'}`);
    } finally {
      setPunctuationOptimizationInProgress(false);
    }
  };

  const handleSmoothingComplete = (result: SmoothingResponse) => {
    setSmoothingResult(result);
    setShowSmoothingPanel(false);
    
    // For development, auto-accept the smoothing result
    if (process.env.NODE_ENV === 'development') {
      // Auto-accept for faster testing
      handleAcceptSmoothedVersionInternal(result);
      
      // Show brief success message
      alert('✅ 逐字稿已自動優化並應用！已加入適當的標點符號。');
    } else {
      setShowComparisonModal(true);
    }
  };

  const handleAcceptSmoothedVersionInternal = (result: SmoothingResponse) => {
    // Convert smoothed segments back to transcript format
    const smoothedTranscript: TranscriptData = {
      session_id: transcript?.session_id || '',
      title: transcript?.title || 'Smoothed Transcript',
      language: result.stats.language_detected,
      duration_sec: (() => {
        if (result.segments.length === 0) return 0;
        const segments = result.segments.map(s => ({ start_sec: s.start_ms / 1000, end_sec: s.end_ms / 1000 }));
        const sortedSegments = segments.slice().sort((a, b) => a.start_sec - b.start_sec);
        const firstStart = sortedSegments[0].start_sec;
        const lastEnd = Math.max(...segments.map(s => s.end_sec));
        return lastEnd - firstStart;
      })(),
      segments: result.segments.map((segment, index) => ({
        id: `smoothed-${index}`,
        speaker_id: segment.speaker === 'A' ? 1 : 2, // Map speaker letters to numbers
        start_sec: segment.start_ms / 1000,
        end_sec: segment.end_ms / 1000,
        content: segment.text,
        confidence: 0.9 // Default confidence for smoothed content
      })),
      created_at: new Date().toISOString(),
      role_assignments: transcript?.role_assignments
    };
    
    setTranscript(smoothedTranscript);
    setShowComparisonModal(false);
    setSmoothingResult(null);
  };

  const handleAcceptSmoothedVersion = () => {
    if (!smoothingResult) return;
    handleAcceptSmoothedVersionInternal(smoothingResult);
  };

  const currentClient = clients.find(c => c.id === session.client_id);
  const isTranscribing = transcriptionSession?.status === 'processing' || transcriptionSession?.status === 'pending';
  const hasTranscript = transcript && transcript.segments && transcript.segments.length > 0;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-content-primary">
            {t('sessions.sessionDetail')}
          </h1>
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => router.push('/dashboard/sessions')}
              className="flex items-center gap-2"
            >
              <ArrowLeftIcon className="h-4 w-4" />
              {t('common.back')}
            </Button>
            {!editMode ? (
              <Button
                onClick={() => setEditMode(true)}
                className="flex items-center gap-2"
              >
                <PencilIcon className="h-4 w-4" />
                {t('common.edit')}
              </Button>
            ) : null}
            <Button
              variant="outline"
              onClick={handleDelete}
              className="flex items-center gap-2 text-red-600 hover:text-red-700"
            >
              <TrashIcon className="h-4 w-4" />
              {t('common.delete')}
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 mb-6 border-b border-border">
          <button
            onClick={() => setActiveTab('overview')}
            className={`pb-2 px-4 transition-colors flex items-center gap-2 ${
              activeTab === 'overview' 
                ? 'text-blue-500 border-b-2 border-blue-500' 
                : 'text-content-secondary hover:text-content-primary'
            }`}
          >
            <ChartBarIcon className="h-4 w-4" />
            {t('sessions.overview')}
          </button>
          <button
            onClick={() => setActiveTab('transcript')}
            className={`pb-2 px-4 transition-colors flex items-center gap-2 ${
              activeTab === 'transcript' 
                ? 'text-blue-500 border-b-2 border-blue-500' 
                : 'text-content-secondary hover:text-content-primary'
            }`}
          >
            <DocumentTextIcon className="h-4 w-4" />
            {t('sessions.transcript')}
            {isTranscribing && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                {t('sessions.processing')}
              </span>
            )}
            {hasTranscript && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                {t('sessions.processingCompleted')}
              </span>
            )}
          </button>
          {hasTranscript && (
            <button
              onClick={() => setActiveTab('ai-optimization')}
              className={`pb-2 px-4 transition-colors flex items-center gap-2 ${
                activeTab === 'ai-optimization' 
                  ? 'text-blue-500 border-b-2 border-blue-500' 
                  : 'text-content-secondary hover:text-content-primary'
              }`}
            >
              <DocumentMagnifyingGlassIcon className="h-4 w-4" />
              🧠 AI 優化
            </button>
          )}
          <button
            onClick={() => setActiveTab('analysis')}
            className={`pb-2 px-4 transition-colors flex items-center gap-2 ${
              activeTab === 'analysis' 
                ? 'text-blue-500 border-b-2 border-blue-500' 
                : 'text-content-secondary hover:text-content-primary'
            }`}
          >
            <ChatBubbleLeftRightIcon className="h-4 w-4" />
            {t('sessions.aiAnalysis')}
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
              {t('sessions.comingSoon')}
            </span>
          </button>
        </div>

        {/* Content */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Basic Information Card */}
            <div className="bg-surface border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4 text-content-primary flex items-center gap-2">
                <DocumentMagnifyingGlassIcon className="h-5 w-5" />
                {t('sessions.basicInfo')}
              </h3>
              
              {editMode ? (
                <form onSubmit={handleUpdate} className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-content-primary mb-2">
                      {t('sessions.sessionDate')} *
                    </label>
                    <Input
                      type="date"
                      required
                      value={formData.session_date}
                      onChange={(e) => setFormData({ ...formData, session_date: e.target.value })}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-content-primary mb-2">
                      {t('sessions.client')} *
                    </label>
                    <Select
                      required
                      value={formData.client_id}
                      onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}
                    >
                      <option value="" disabled>{t('sessions.selectClient')}</option>
                      {clients.map((client) => (
                        <option key={client.id} value={client.id}>
                          {client.name}
                        </option>
                      ))}
                    </Select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-content-primary mb-2">
                      {t('sessions.durationMinutes')}
                    </label>
                    <Input
                      type="number"
                      min="1"
                      required
                      value={formData.duration_min}
                      onChange={(e) => setFormData({ ...formData, duration_min: parseInt(e.target.value) || 0 })}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-content-primary mb-2">
                        {t('sessions.currency')}
                      </label>
                      <Select
                        value={formData.fee_currency}
                        onChange={(e) => setFormData({ ...formData, fee_currency: e.target.value })}
                      >
                        {currencies.map((currency) => (
                          <option key={currency.value} value={currency.value}>
                            {String(currency.label || currency.value)}
                          </option>
                        ))}
                      </Select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-content-primary mb-2">
                        {t('sessions.amount')} *
                      </label>
                      <Input
                        type="number"
                        min="0"
                        required
                        value={formData.fee_amount}
                        onChange={(e) => setFormData({ ...formData, fee_amount: parseInt(e.target.value) || 0 })}
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-content-primary mb-2">
                      {t('sessions.notes')}
                    </label>
                    <textarea
                      className="w-full px-3 py-2 border border-border rounded-md bg-surface text-content-primary focus:outline-none focus:ring-2 focus:ring-accent"
                      rows={4}
                      value={formData.notes}
                      onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    />
                  </div>

                  <div className="flex justify-end gap-4 pt-6 border-t border-border">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        setEditMode(false);
                        // Reset form data
                        setFormData({
                          session_date: session.session_date,
                          client_id: session.client_id,
                          duration_min: session.duration_min,
                          fee_currency: session.fee_currency,
                          fee_amount: session.fee_amount,
                          notes: session.notes || ''
                        });
                      }}
                      disabled={loading}
                    >
                      {t('common.cancel')}
                    </Button>
                    <Button type="submit" disabled={loading}>
                      {loading ? t('common.updating') : t('common.save')}
                    </Button>
                  </div>
                </form>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-content-secondary mb-1">
                      {t('sessions.sessionDate')}
                    </label>
                    <p className="text-content-primary text-lg">{session.session_date}</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-content-secondary mb-1">
                      {t('sessions.client')}
                    </label>
                    <p className="text-content-primary text-lg">
                      {session.client?.name || currentClient?.name || session.client_name || '-'}
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-content-secondary mb-1">
                      {t('sessions.duration')}
                    </label>
                    <p className="text-content-primary">{session.duration_display}</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-content-secondary mb-1">
                      {t('sessions.fee')}
                    </label>
                    <p className="text-content-primary text-lg font-medium">{session.fee_display}</p>
                  </div>

                  {session.notes && (
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-content-secondary mb-1">
                        {t('sessions.notes')}
                      </label>
                      <p className="text-content-primary whitespace-pre-wrap">{session.notes}</p>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Audio Analysis Card */}
            <div className="bg-surface border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4 text-content-primary flex items-center gap-2">
                {isTranscriptOnly ? (
                  <>
                    <DocumentTextIcon className="h-5 w-5" />
                    {t('sessions.transcriptContent')}
                  </>
                ) : (
                  <>
                    <MicrophoneIcon className="h-5 w-5" />
                    {t('sessions.audioAnalysis')}
                  </>
                )}
              </h3>
              
              {/* Upload Mode Selection */}
              {!session?.transcription_session_id && !hasTranscript && (transcriptionSession?.status !== 'completed' && transcriptionSession?.status !== 'processing' && transcriptionSession?.status !== 'pending') && (
                <div className="mb-6">
                  <p className="text-sm text-content-secondary mb-3">{t('sessions.selectUploadMethod')}</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <button
                      onClick={() => setUploadMode('audio')}
                      className={`p-4 border-2 rounded-lg transition-all ${
                        uploadMode === 'audio'
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                          : 'border-border hover:border-gray-400'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <MicrophoneIcon className="h-6 w-6 text-blue-600" />
                        <div className="text-left">
                          <div className="font-medium text-content-primary">{t('sessions.audioAnalysisTitle')}</div>
                          <div className="text-sm text-content-secondary">{t('sessions.audioAnalysisDesc')}</div>
                        </div>
                      </div>
                    </button>
                    
                    <button
                      onClick={() => setUploadMode('transcript')}
                      className={`p-4 border-2 rounded-lg transition-all ${
                        uploadMode === 'transcript'
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                          : 'border-border hover:border-gray-400'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <DocumentTextIcon className="h-6 w-6 text-green-600" />
                        <div className="text-left">
                          <div className="font-medium text-content-primary">{t('sessions.directUploadTitle')}</div>
                          <div className="text-sm text-content-secondary">{t('sessions.directUploadDesc')}</div>
                        </div>
                      </div>
                    </button>
                  </div>
                </div>
              )}

              {/* Audio Upload Mode */}
              {uploadMode === 'audio' && !canUseAudioAnalysis ? (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
                  <div className="flex items-start gap-4">
                    <ExclamationTriangleIcon className="h-6 w-6 text-red-600 dark:text-red-400 flex-shrink-0 mt-1" />
                    <div className="flex-1">
                      <h4 className="text-lg font-semibold text-red-900 dark:text-red-100 mb-2">
                        {t('limits.usageLimitReached')}
                      </h4>
                      <p className="text-red-700 dark:text-red-300 mb-3">
                        {limitMessage?.message}
                      </p>
                      {limitMessage && (
                        <div className="bg-white dark:bg-gray-800 rounded-md p-3 mb-4">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600 dark:text-gray-400">
                              {t(`limits.${limitMessage.type}`)}
                            </span>
                            <span className="text-sm font-medium text-red-600 dark:text-red-400">
                              {limitMessage.current} / {limitMessage.limit}
                            </span>
                          </div>
                          <div className="mt-2 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div 
                              className="bg-red-600 h-2 rounded-full"
                              style={{ width: '100%' }}
                            />
                          </div>
                        </div>
                      )}
                      <div className="flex gap-3">
                        <button
                          onClick={() => router.push('/dashboard/billing?tab=plans')}
                          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                          <ArrowUpIcon className="h-4 w-4 inline mr-2" />
                          {t('limits.upgradeNow')}
                        </button>
                        <button
                          onClick={() => router.push('/dashboard/billing?tab=overview')}
                          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                        >
                          {t('limits.viewUsage')}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ) : uploadMode === 'audio' && !session?.transcription_session_id && !hasTranscript && (transcriptionSession?.status !== 'completed' && transcriptionSession?.status !== 'processing' && transcriptionSession?.status !== 'pending') && (
                <AudioUploader
                  sessionId={sessionId}
                  existingAudioSessionId={transcriptionSessionId || undefined}
                  isSessionLoading={fetching}
                  transcriptionStatus={transcriptionStatus}
                  transcriptionSession={transcriptionSession}
                  onUploadComplete={(newTranscriptionSessionId) => {
                    // Update session with new transcription session ID
                    setSession(prev => prev ? {
                      ...prev,
                      transcription_session_id: newTranscriptionSessionId
                    } : null);
                    // Trigger transcript fetch if needed
                    fetchSession();
                  }}
                />
              )}

              {/* Transcript Upload Mode */}
              {uploadMode === 'transcript' && !session?.transcription_session_id && !hasTranscript && (transcriptionSession?.status !== 'completed' && transcriptionSession?.status !== 'processing' && transcriptionSession?.status !== 'pending') && (
                <div className="space-y-4">
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-400 p-4">
                    <div className="flex">
                      <div className="ml-3">
                        <p className="text-sm text-yellow-700 dark:text-yellow-200">
                          <strong>{t('common.note')}</strong> {t('sessions.directUploadWarning')}
                        </p>
                      </div>
                    </div>
                  </div>

                  {!transcriptFile ? (
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-gray-400 transition-colors">
                      <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
                      <div className="mt-4">
                        <label htmlFor="transcript-upload" className="cursor-pointer">
                          <span className="text-lg font-medium text-content-primary">{t('sessions.clickToUpload')}</span>
                          <p className="text-sm text-content-secondary mt-1">{t('sessions.supportedFormatsVttSrt')}</p>
                        </label>
                        <input
                          id="transcript-upload"
                          type="file"
                          accept=".vtt,.srt"
                          onChange={handleTranscriptFileChange}
                          className="hidden"
                        />
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <DocumentTextIcon className="h-8 w-8 text-green-600" />
                            <div>
                              <p className="font-medium text-content-primary">{transcriptFile.name}</p>
                              <p className="text-sm text-content-secondary">
                                {(transcriptFile.size / 1024).toFixed(1)} KB
                              </p>
                            </div>
                          </div>
                          <button
                            onClick={() => {
                              setTranscriptFile(null);
                              setPreviewSegments([]);
                              setSpeakerRoleMapping({});
                            }}
                            className="text-red-600 hover:text-red-800 text-sm font-medium"
                            disabled={isUploadingTranscript}
                          >
                            {t('sessions.remove')}
                          </button>
                        </div>
                      </div>

                      {/* Convert to Traditional Chinese Option */}
                      <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
                        <label className="flex items-center gap-3 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={convertToTraditional}
                            onChange={(e) => setConvertToTraditional(e.target.checked)}
                            className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                            disabled={isUploadingTranscript}
                          />
                          <div className="flex-1">
                            <span className="font-medium text-content-primary">{t('sessions.convertToTraditionalChinese')}</span>
                            <p className="text-sm text-content-secondary">
                              {t('sessions.convertToTraditionalChineseDesc')}
                            </p>
                          </div>
                        </label>
                      </div>

                      {/* Speaker Role Assignment */}
                      {previewSegments.length > 0 && (
                        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                          <h4 className="font-medium text-content-primary mb-3">{t('sessions.speakerRoleAssignment')}</h4>
                          <p className="text-sm text-content-secondary mb-4">
                            {t('sessions.detectSpeakersMessage').replace('{count}', previewSegments.length.toString())}
                          </p>
                          
                          <div className="space-y-3">
                            {previewSegments.map((segment) => (
                              <div key={segment.speaker_id} className="bg-white dark:bg-gray-800 rounded-lg p-3">
                                <div className="flex items-start gap-3">
                                  <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-2">
                                      <span className="font-medium text-sm">
                                        {segment.speaker_name}
                                      </span>
                                      <span className="text-xs text-content-secondary">
                                        {t('sessions.segmentsCount').replace('{count}', segment.count.toString())}
                                      </span>
                                    </div>
                                    <p className="text-sm text-content-secondary italic">
                                      &ldquo;{segment.content}&rdquo;
                                    </p>
                                  </div>
                                  <div className="flex-shrink-0">
                                    <select
                                      value={speakerRoleMapping[segment.speaker_id] || 'client'}
                                      onChange={(e) => setSpeakerRoleMapping(prev => ({
                                        ...prev,
                                        [segment.speaker_id]: e.target.value as 'coach' | 'client'
                                      }))}
                                      className="text-sm px-3 py-1 border border-border rounded-md bg-surface focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    >
                                      <option value="coach">{t('sessions.coachRole')}</option>
                                      <option value="client">{t('sessions.clientRole')}</option>
                                    </select>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <Button
                        onClick={handleTranscriptUpload}
                        disabled={isUploadingTranscript || previewSegments.length === 0}
                        className="w-full"
                      >
                        {isUploadingTranscript ? (
                          <div className="flex items-center gap-2">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                            {t('sessions.uploading')}
                          </div>
                        ) : (
                          t('sessions.uploadTranscript')
                        )}
                      </Button>
                    </div>
                  )}
                </div>
              )}
              
              {/* Transcription Status Display */}
              {transcriptionSessionId && (
                <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                  <div className="flex items-center gap-3">
                    <DocumentTextIcon className="h-5 w-5 text-blue-600" />
                    <div>
                      <h4 className="font-medium text-blue-800 dark:text-blue-200">{t('sessions.conversionHistory')}</h4>
                      <p className="text-sm text-blue-600 dark:text-blue-300">
                        {hasTranscript ? 
                          t('sessions.transcriptCompleted') : 
                          transcriptionSession?.status === 'completed' ? 
                            t('sessions.conversionCompleted') :
                            t('sessions.conversionStatus').replace('{status}', transcriptionSession?.status || t('sessions.checking'))
                        }
                      </p>
                      {transcriptionSession?.id && (
                        <p className="text-xs text-blue-500 dark:text-blue-400 mt-1">
                          {t('sessions.conversionId').replace('{id}', transcriptionSession.id)}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}
              
              {/* Auto-optimization Notice */}
              {hasTranscript && transcript && (
                (() => {
                  // Check if auto-smoothing was applied
                  const isAutoOptimized = transcript?.metadata?.auto_smoothing_applied || 
                                         transcript?.provider_metadata?.auto_smoothing_applied;
                  const smoothingStats = transcript?.metadata?.smoothing_stats || 
                                       transcript?.provider_metadata?.smoothing_stats;
                  
                  if (isAutoOptimized) {
                    return (
                      <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 mb-4">
                        <div className="flex items-start gap-3">
                          <div className="flex-shrink-0">
                            <svg className="w-5 h-5 text-green-600 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                          </div>
                          <div>
                            <h4 className="text-sm font-medium text-green-800 dark:text-green-200">
                              🎯 逐字稿已自動優化
                            </h4>
                            <p className="text-sm text-green-700 dark:text-green-300 mt-1">
                              系統已自動修正講者邊界錯誤並改善中文標點符號（如問號、感嘆號、句號），為您提供更準確的逐字稿。
                            </p>
                            {smoothingStats && (
                              <div className="text-xs text-green-600 dark:text-green-400 mt-2 flex gap-4">
                                {smoothingStats.moved_word_count > 0 && (
                                  <span>移動了 {smoothingStats.moved_word_count} 個詞</span>
                                )}
                                {smoothingStats.merged_segments > 0 && (
                                  <span>合併了 {smoothingStats.merged_segments} 個片段</span>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  }
                  return null;
                })()
              )}

            </div>
          </div>
        )}

        {activeTab === 'transcript' && (
          <div className="space-y-4">
            {/* Speaking Statistics - moved from overview tab */}
            {(speakingStats || (transcriptDeleted && savedSpeakingStats)) && (
              <div className="bg-surface border border-border rounded-lg p-6">
                <div className="border-b border-border pb-4 mb-6">
                  <h3 className="text-lg font-semibold text-content-primary flex items-center gap-2">
                    <DocumentMagnifyingGlassIcon className="h-5 w-5" />
                    {t('sessions.talkAnalysisResults')}
                    {transcriptDeleted && savedSpeakingStats && (
                      <span className="text-sm text-yellow-600 font-normal">
                        (逐字稿已刪除，顯示刪除前的統計資料)
                      </span>
                    )}
                  </h3>
                </div>
                
                {(() => {
                  const stats = speakingStats || savedSpeakingStats!;
                  return (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Speaking Time Distribution */}
                      <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
                        <h4 className="font-medium text-content-primary mb-3">{t('sessions.talkTimeDistribution')}</h4>
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <span className="text-blue-600 font-medium">{t('sessions.coach')}</span>
                            <span className="text-sm">{formatDuration(stats.coach_speaking_time)} ({stats.coach_percentage.toFixed(1)}%)</span>
                          </div>
                          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div
                              className="bg-blue-500 h-2 rounded-full"
                              style={{width: `${stats.coach_percentage}%`}}
                            ></div>
                          </div>

                          <div className="flex items-center justify-between">
                            <span className="text-green-600 font-medium">{t('sessions.client')}</span>
                            <span className="text-sm">{formatDuration(stats.client_speaking_time)} ({stats.client_percentage.toFixed(1)}%)</span>
                          </div>
                          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div
                              className="bg-green-500 h-2 rounded-full"
                              style={{width: `${stats.client_percentage}%`}}
                            ></div>
                          </div>
                        </div>
                      </div>

                      {/* Overall Stats */}
                      <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
                        <h4 className="font-medium text-content-primary mb-3">{t('sessions.overallStats')}</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-content-secondary">{t('sessions.totalDuration')}</span>
                            <span className="text-content-primary font-medium">
                              {formatDuration(stats.total_speaking_time + stats.silence_time)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-content-secondary">{t('sessions.talkTime')}</span>
                            <span className="text-content-primary font-medium">{formatDuration(stats.total_speaking_time)}</span>
                          </div>
                          {/* Silence time calculation is not accurate from STT, showing warning */}
                          <div className="flex justify-between">
                            <span className="text-content-secondary">
                              {t('sessions.silenceTime')}
                              <span className="text-xs text-yellow-600 ml-1" title={t('sessions.silenceTimeNote')}>
                                ({t('sessions.silenceTimeNote')})
                              </span>
                            </span>
                            <span className="text-content-primary font-medium">
                              {stats.silence_time > 0 ? formatDuration(stats.silence_time) : t('sessions.silenceTimeCalculationError')}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-content-secondary">{t('sessions.conversationSegments')}</span>
                            <span className="text-content-primary font-medium">{transcript?.segments.length || (transcriptDeleted ? '(已刪除)' : '0')}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })()}
              </div>
            )}
            {/* Transcription Status */}
            {(isTranscribing || transcriptionSession?.status === 'pending') && transcriptionStatus && (
              <div className="bg-surface border border-border rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4 text-content-primary">
                  {t('sessions.transcriptionProcessing')}
                </h3>
                <TranscriptionProgress
                  progress={Number(transcriptionStatus.progress) || 0}
                  status={transcriptionSession?.status === 'processing' ? 'processing' : 'pending'}
                  message={transcriptionStatus.message || (transcriptionSession?.status === 'pending' ? t('sessions.waitingToStart') : t('sessions.processing'))}
                  estimatedTime={transcriptionStatus.estimated_completion ? 
                    formatTimeRemaining(transcriptionStatus.estimated_completion) : undefined}
                />
                {transcriptionStatus.duration_processed != null && 
                 transcriptionStatus.duration_total != null && 
                 transcriptionStatus.duration_total > 0 && (
                  <div className="mt-2 text-sm text-content-secondary">
                    {t('sessions.processed').replace('{processed}', formatDuration(transcriptionStatus.duration_processed)).replace('{total}', formatDuration(transcriptionStatus.duration_total))}
                  </div>
                )}
              </div>
            )}


            {/* Export Controls - hide when transcript is deleted */}
            {hasTranscript && !transcriptDeleted && (
              <div className="bg-surface border border-border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <label className="text-sm font-medium text-content-primary">
                      {t('sessions.exportFormat')}
                    </label>
                    <select
                      value={exportFormat}
                      onChange={(e) => setExportFormat(e.target.value as any)}
                      className="px-3 py-1 border border-border rounded-md bg-surface text-content-primary"
                    >
                      <option value="xlsx">Excel (.xlsx)</option>
                      <option value="txt">{t('sessions.exportTxt')}</option>
                    </select>
                  </div>
                  <Button
                    onClick={handleExportTranscript}
                    className="flex items-center gap-2"
                  >
                    <DocumentArrowDownIcon className="h-4 w-4" />
                    {t('sessions.exportTranscript')}
                  </Button>
                </div>
              </div>
            )}

            {/* Transcript Table - only show when has transcript and not deleted */}
            {hasTranscript && !transcriptDeleted && (
              <div className="bg-surface border border-border rounded-lg overflow-hidden">
                <div className="px-6 py-4 border-b border-border">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-content-primary">
                      {t('sessions.conversationRecord')}
                    </h3>
                    <div className="flex items-center gap-4">
                      <div className="text-sm text-content-secondary">
                        {t('sessions.conversationSummary').replace('{duration}', 
                          speakingStats ? formatDuration(speakingStats.total_speaking_time + speakingStats.silence_time) : formatDuration(transcript.duration_sec)
                        ).replace('{count}', transcript.segments.length.toString())}
                      </div>
                      {!editingTranscript ? (
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            onClick={() => setEditingTranscript(true)}
                            className="flex items-center gap-2 text-sm px-3 py-1"
                          >
                            <PencilIcon className="h-3 w-3" />
                            編輯逐字稿
                          </Button>
                          <Button
                            variant="outline"
                            onClick={() => setShowDeleteConfirm(true)}
                            className="flex items-center gap-2 text-sm px-3 py-1 text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
                          >
                            <TrashIcon className="h-3 w-3" />
                            刪除逐字稿
                          </Button>
                        </div>
                      ) : (
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            onClick={cancelTranscriptEditing}
                            className="text-sm px-3 py-1"
                          >
                            {t('sessions.cancel')}
                          </Button>
                          <Button
                            onClick={saveTranscriptChanges}
                            className="flex items-center gap-2 text-sm px-3 py-1"
                          >
                            {t('sessions.save')}
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-border">
                    <thead className="bg-gray-50 dark:bg-gray-800">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-content-secondary uppercase tracking-wider w-20">
                          {t('sessions.time')}
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-content-secondary uppercase tracking-wider w-24">
                          {t('sessions.speaker')}
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-content-secondary uppercase tracking-wider">
                          {t('sessions.content')}
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-surface divide-y divide-border">
                      {transcript.segments.map((segment, index) => (
                        <tr key={segment.id || index} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                          <td className="px-4 py-3 whitespace-nowrap text-xs text-content-secondary">
                            {formatTime(segment.start_sec)}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            {editingTranscript ? (
                              <select
                                value={(() => {
                                  const segmentId = segment.id || `${segment.speaker_id}-${segment.start_sec}`;
                                  const tempSegmentRole = tempSegmentRoles[segmentId];
                                  const tempSpeakerRole = tempRoleAssignments[segment.speaker_id];

                                  if (tempSegmentRole) return tempSegmentRole;
                                  if (tempSpeakerRole) return tempSpeakerRole;

                                  const roleFromSegment = getSpeakerRoleFromSegment(segment, transcript?.role_assignments);
                                  if (roleFromSegment === SpeakerRole.COACH) return 'coach';
                                  if (roleFromSegment === SpeakerRole.CLIENT) return 'client';
                                  // For UNKNOWN role, default to 'client' for dropdown
                                  return 'client';
                                })()}
                                onChange={(e) => {
                                  const segmentId = segment.id || `${segment.speaker_id}-${segment.start_sec}`;
                                  setTempSegmentRoles(prev => ({
                                    ...prev,
                                    [segmentId]: e.target.value as 'coach' | 'client'
                                  }));
                                }}
                                className="text-xs px-2 py-1 border border-border rounded bg-surface"
                              >
                                <option value="coach">{t('sessions.coach')}</option>
                                <option value="client">{t('sessions.client')}</option>
                              </select>
                            ) : (
                              <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                                (() => {
                                  const segmentId = segment.id || `${segment.speaker_id}-${segment.start_sec}`;
                                  let roleString: string;
                                  if (tempSegmentRoles[segmentId]) {
                                    roleString = tempSegmentRoles[segmentId];
                                  } else if (tempRoleAssignments[segment.speaker_id]) {
                                    roleString = tempRoleAssignments[segment.speaker_id];
                                  } else {
                                    const defaultRole = getSpeakerRoleFromSegment(segment, transcript?.role_assignments);
                                    roleString = defaultRole === SpeakerRole.COACH ? 'coach' :
                                                 defaultRole === SpeakerRole.CLIENT ? 'client' : 'unknown';
                                  }
                                  return (roleString === 'coach' || roleString === SpeakerRole.COACH)
                                    ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' 
                                    : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
                                })()
                              }`}>
                                {getSegmentSpeakerLabel(segment)}
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-content-primary text-sm">
                            {editingTranscript ? (
                              <textarea
                                value={tempSegmentContent[segment.id || `${segment.speaker_id}-${segment.start_sec}`] || segment.content}
                                onChange={(e) => {
                                  const segmentId = segment.id || `${segment.speaker_id}-${segment.start_sec}`;
                                  setTempSegmentContent(prev => ({
                                    ...prev,
                                    [segmentId]: e.target.value
                                  }));
                                }}
                                className="w-full p-2 border border-border rounded bg-surface text-sm resize-none"
                                rows={Math.max(1, Math.ceil(segment.content.length / 80))}
                              />
                            ) : (
                              segment.content
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* No Transcript */}
            {!hasTranscript && !isTranscribing && (
              <div className="bg-surface border border-border rounded-lg p-12 text-center">
                <div className="space-y-4">
                  {transcriptDeleted ? (
                    <>
                      <TrashIcon className="h-12 w-12 text-content-secondary mx-auto" />
                      <div>
                        <p className="text-content-primary font-medium mb-2">
                          逐字稿已刪除
                        </p>
                        <p className="text-content-secondary text-sm">
                          教練 session 記錄和統計資料已保留於上方
                        </p>
                      </div>
                    </>
                  ) : (
                    <>
                      <MicrophoneIcon className="h-16 w-16 text-content-secondary mx-auto" />
                      <p className="text-content-secondary mb-4">
                        {t('sessions.noTranscriptUploaded')}
                      </p>
                      <Button
                        onClick={() => setActiveTab('overview')}
                        className="mx-auto flex items-center gap-2"
                      >
                        <DocumentTextIcon className="h-4 w-4" />
                        {t('sessions.goToOverviewToUpload').replace('{type}', isTranscriptOnly ? t('sessions.transcriptFile') : t('sessions.audioFile'))}
                      </Button>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'ai-optimization' && (
          <div className="space-y-6">
            {!hasTranscript ? (
              <div className="bg-surface border border-border rounded-lg p-12 text-center">
                <DocumentMagnifyingGlassIcon className="h-16 w-16 text-content-secondary mx-auto mb-4" />
                <p className="text-content-secondary mb-4">
                  需要先上傳音檔並完成轉錄才能使用 AI 優化功能
                </p>
                <Button
                  onClick={() => setActiveTab('overview')}
                  className="flex items-center gap-2 mx-auto"
                >
                  <DocumentTextIcon className="h-4 w-4" />
                  前往上傳音檔
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {/* AI Transcript Optimization - Dev Only with Editable Prompts */}
                <div className="bg-surface border border-border rounded-lg p-6">
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold mb-2 text-content-primary flex items-center gap-2">
                      🧠 AI 逐字稿優化
                    </h3>
                    <p className="text-sm text-content-secondary">
                      使用 AI 技術優化逐字稿品質，包括說話者識別和標點符號改善
                    </p>
                  </div>
                  
                  {/* Optimization buttons */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    {/* Speaker Identification Button */}
                    <Button
                      onClick={handleSpeakerIdentification}
                      className="bg-blue-600 text-white hover:bg-blue-700 h-auto py-4"
                      disabled={speakerIdentificationInProgress || !transcript}
                    >
                      <div className="flex flex-col items-center gap-2">
                        {speakerIdentificationInProgress ? (
                          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                        ) : (
                          <UserGroupIcon className="h-6 w-6" />
                        )}
                        <span className="font-medium">說話者識別</span>
                        <span className="text-xs opacity-90">識別教練與客戶對話</span>
                      </div>
                    </Button>

                    {/* Punctuation Optimization Button */}
                    <Button
                      onClick={handlePunctuationOptimization}
                      className="bg-green-600 text-white hover:bg-green-700 h-auto py-4"
                      disabled={punctuationOptimizationInProgress || !transcript}
                    >
                      <div className="flex flex-col items-center gap-2">
                        {punctuationOptimizationInProgress ? (
                          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                        ) : (
                          <PencilIcon className="h-6 w-6" />
                        )}
                        <span className="font-medium">標點符號優化</span>
                        <span className="text-xs opacity-90">改善中文標點符號</span>
                      </div>
                    </Button>

                    {/* Combined Full Optimization Button */}
                    <Button
                      onClick={handleSmoothTranscript}
                      className="bg-dashboard-accent text-dashboard-bg hover:bg-dashboard-accent-hover h-auto py-4"
                      disabled={smoothingInProgress || !transcript}
                    >
                      <div className="flex flex-col items-center gap-2">
                        {smoothingInProgress ? (
                          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                        ) : (
                          <DocumentMagnifyingGlassIcon className="h-6 w-6" />
                        )}
                        <span className="font-medium">完整優化</span>
                        <span className="text-xs opacity-90">說話者 + 標點符號</span>
                      </div>
                    </Button>
                  </div>
                  
                  {/* System Prompt Editor */}
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-content-primary mb-2">
                        說話者識別 System Prompt:
                      </label>
                      <textarea
                        value={speakerPrompt}
                        onChange={(e) => setSpeakerPrompt(e.target.value)}
                        className="w-full h-32 px-3 py-2 border border-border rounded-md bg-surface text-content-primary text-sm font-mono"
                        placeholder="輸入說話者識別的 system prompt..."
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-content-primary mb-2">
                        標點符號優化 System Prompt:
                      </label>
                      <textarea
                        value={punctuationPrompt}
                        onChange={(e) => setPunctuationPrompt(e.target.value)}
                        className="w-full h-32 px-3 py-2 border border-border rounded-md bg-surface text-content-primary text-sm font-mono"
                        placeholder="輸入標點符號優化的 system prompt..."
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'analysis' && (
          <div className="space-y-6">
            {!hasTranscript ? (
              <div className="bg-surface border border-border rounded-lg p-12 text-center">
                {transcriptDeleted ? (
                  <>
                    <TrashIcon className="h-16 w-16 text-content-secondary mx-auto mb-4" />
                    <p className="text-content-primary font-medium mb-2">
                      音檔和逐字稿已刪除
                    </p>
                    <p className="text-content-secondary text-sm">
                      無法進行 AI 分析
                    </p>
                  </>
                ) : (
                  <>
                    <ChatBubbleLeftRightIcon className="h-16 w-16 text-content-secondary mx-auto mb-4" />
                    <p className="text-content-secondary mb-4">
                      {t('sessions.needUploadForAI').replace('{type}', isTranscriptOnly ? t('sessions.transcriptFile') : t('sessions.needUploadAndTranscription').replace('{type}', t('sessions.audioFile')))}
                    </p>
                    <Button
                      onClick={() => setActiveTab('overview')}
                      className="flex items-center gap-2 mx-auto"
                    >
                      {isTranscriptOnly ? (
                        <DocumentTextIcon className="h-4 w-4" />
                      ) : (
                        <MicrophoneIcon className="h-4 w-4" />
                      )}
                      {t('sessions.goToOverviewToUpload').replace('{type}', isTranscriptOnly ? t('sessions.transcriptFile') : t('sessions.audioFile'))}
                    </Button>
                  </>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* AI Summary */}
                <div className="bg-surface border border-border rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-content-primary flex items-center gap-2">
                      <DocumentMagnifyingGlassIcon className="h-5 w-5" />
                      {t('sessions.sessionSummary')}
                    </h3>
                    <Button
                      onClick={generateAISummary}
                      disabled={isGeneratingAnalysis}
                      className="flex items-center gap-2 text-sm"
                    >
                      {isGeneratingAnalysis ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      ) : (
                        <ChatBubbleLeftRightIcon className="h-4 w-4" />
                      )}
                      {isGeneratingAnalysis ? t('sessions.generating') : t('sessions.generateSummary')}
                    </Button>
                  </div>
                  
                  <div className="prose prose-sm max-w-none text-content-primary">
                    {aiAnalysis ? (
                      <div className="whitespace-pre-wrap">{aiAnalysis}</div>
                    ) : (
                      <p className="text-content-secondary italic">
                        {t('sessions.generateSummaryDesc')}
                      </p>
                    )}
                  </div>
                </div>

                {/* AI Chat */}
                <div className="bg-surface border border-border rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-content-primary flex items-center gap-2 mb-4">
                    <ChatBubbleLeftRightIcon className="h-5 w-5" />
                    {t('sessions.aiChat')}
                  </h3>
                  
                  {/* Chat Messages */}
                  <div className="space-y-4 max-h-96 overflow-y-auto mb-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    {chatMessages.length === 0 ? (
                      <p className="text-content-secondary text-sm italic text-center py-4">
                        {t('sessions.aiChatDesc')}
                      </p>
                    ) : (
                      chatMessages.map((message, index) => (
                        <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                          <div className={`max-w-[80%] px-3 py-2 rounded-lg ${
                            message.role === 'user' 
                              ? 'bg-blue-500 text-white' 
                              : 'bg-white dark:bg-gray-700 text-content-primary border border-border'
                          }`}>
                            <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                  
                  {/* Chat Input */}
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={currentMessage}
                      onChange={(e) => setCurrentMessage(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && sendChatMessage()}
                      placeholder={t('sessions.enterQuestion')}
                      className="flex-1 px-3 py-2 border border-border rounded-md bg-surface text-content-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <Button
                      onClick={sendChatMessage}
                      disabled={!currentMessage.trim()}
                      className="flex items-center gap-2"
                    >
                      <ChatBubbleLeftRightIcon className="h-4 w-4" />
                      {t('sessions.send')}
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Transcript Smoothing Modals */}
      <TranscriptSmoothingPanel
        assemblyAiTranscript={originalAssemblyAiData}
        onSmoothingComplete={handleSmoothingComplete}
        isVisible={showSmoothingPanel}
        onClose={() => setShowSmoothingPanel(false)}
      />

      <TranscriptComparison
        originalTranscript={originalAssemblyAiData}
        smoothedSegments={smoothingResult?.segments || []}
        processingStats={smoothingResult?.stats || {} as any}
        isVisible={showComparisonModal}
        onClose={() => setShowComparisonModal(false)}
        onAccept={handleAcceptSmoothedVersion}
      />

      {/* Delete Transcript Confirmation Dialog */}
      <DeleteTranscriptConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={handleDeleteTranscript}
        isDeleting={isDeletingTranscript}
      />
    </div>
  );
};

export default SessionDetailPage;
