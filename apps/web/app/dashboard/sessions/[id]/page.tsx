'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { PencilIcon, TrashIcon, ArrowLeftIcon, DocumentArrowDownIcon, MicrophoneIcon, DocumentTextIcon, ChartBarIcon, ChatBubbleLeftRightIcon, DocumentMagnifyingGlassIcon, CloudArrowUpIcon } from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { useAuth } from '@/contexts/auth-context';
import { useI18n } from '@/contexts/i18n-context';
import { apiClient, TranscriptNotAvailableError } from '@/lib/api';
import { TranscriptionProgress } from '@/components/ui/progress-bar';
import { useTranscriptionStatus, formatTimeRemaining, formatDuration } from '@/hooks/useTranscriptionStatus';
import { AudioUploader } from '@/components/AudioUploader';

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
  CLIENT = 'client'
}

// Speaker ID constants - these should match the backend convention
const SPEAKER_IDS = {
  COACH: 0,  // Speaker 0 is typically assigned as coach by AssemblyAI
  CLIENT: 1  // Speaker 1 is typically assigned as client by AssemblyAI
} as const;

// Helper functions for safe role assignment
const getSpeakerRoleFromId = (speakerId: number, roleAssignments?: { [key: number]: 'coach' | 'client' }): SpeakerRole => {
  // First check explicit role assignments from API
  if (roleAssignments && roleAssignments[speakerId]) {
    return roleAssignments[speakerId] === 'coach' ? SpeakerRole.COACH : SpeakerRole.CLIENT;
  }
  
  // Fallback to our convention: Speaker 0 = coach, others = client
  return speakerId === SPEAKER_IDS.COACH ? SpeakerRole.COACH : SpeakerRole.CLIENT;
};

const getRoleDisplayName = (role: SpeakerRole): string => {
  return role === SpeakerRole.COACH ? '教練' : '客戶';
};

const getSpeakerColor = (role: SpeakerRole): string => {
  return role === SpeakerRole.COACH ? 'text-blue-600' : 'text-green-600';
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
  const [activeTab, setActiveTab] = useState<'overview' | 'transcript' | 'analysis'>('overview');
  const [transcript, setTranscript] = useState<TranscriptData | null>(null);
  const [transcriptLoading, setTranscriptLoading] = useState(false);
  const [exportFormat, setExportFormat] = useState<'vtt' | 'srt' | 'txt' | 'json' | 'xlsx'>('vtt');
  const [speakingStats, setSpeakingStats] = useState<SpeakingStats | null>(null);
  const [aiAnalysis, setAiAnalysis] = useState<string>('');
  const [chatMessages, setChatMessages] = useState<Array<{role: 'user' | 'assistant', content: string}>>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isGeneratingAnalysis, setIsGeneratingAnalysis] = useState(false);
  const [editingRoles, setEditingRoles] = useState(false);
  const [tempRoleAssignments, setTempRoleAssignments] = useState<{ [speakerId: number]: 'coach' | 'client' }>({});
  const [tempSegmentRoles, setTempSegmentRoles] = useState<{ [segmentId: string]: 'coach' | 'client' }>({});
  const [uploadMode, setUploadMode] = useState<'audio' | 'transcript'>('audio');
  const [transcriptFile, setTranscriptFile] = useState<File | null>(null);
  const [isUploadingTranscript, setIsUploadingTranscript] = useState(false);
  const [speakerRoleMapping, setSpeakerRoleMapping] = useState<{[speakerId: string]: 'coach' | 'client'}>({});
  const [previewSegments, setPreviewSegments] = useState<Array<{speaker_id: string, speaker_name: string, content: string, count: number}>>([]);
  const [convertToTraditional, setConvertToTraditional] = useState(false);

  // Use transcription status hook for progress tracking
  const transcriptionSessionId = session?.transcription_session_id;
  
  // Debug client information
  console.log('Client debug info:', {
    sessionClient: session?.client,
    sessionClientId: session?.client_id,
    clientsArray: clients,
    currentClient: clients.find(c => c.id === session?.client_id),
    fullSession: session
  });
  
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
    // Always enable polling if transcriptionSessionId exists, restrict polling by active tab only
    enablePolling: Boolean(transcriptionSessionId && (activeTab === 'overview' || activeTab === 'transcript'))
  });

  // Determine if this session was created from direct transcript upload (not audio)
  const isTranscriptOnly = transcriptionSession?.audio_filename?.endsWith('.manual') || false;

  useEffect(() => {
    if (sessionId) {
      fetchSession();
      fetchClients();
      fetchCurrencies();
    }
  }, [sessionId]);

  useEffect(() => {
    // Auto-fetch transcript when transcription is completed and we don't have it yet
    if (transcriptionSession?.status === 'completed' && transcriptionSessionId && !transcript) {
      console.log('Transcription completed, fetching transcript...');
      fetchTranscript(transcriptionSessionId);
    }
  }, [transcriptionSession?.status, transcriptionSessionId, transcript]);

  useEffect(() => {
    // Calculate speaking stats when transcript is available
    if (transcript && transcript.segments && transcript.segments.length > 0) {
      const stats = calculateSpeakingStats(transcript.segments);
      setSpeakingStats(stats);
      
      // Initialize role assignments from transcript data (keep for compatibility)
      if (transcript.role_assignments) {
        setTempRoleAssignments(transcript.role_assignments);
      } else {
        // Default assignments if none exist
        const speakerIds = transcript.segments.map(s => s.speaker_id);
        const uniqueSpeakers = Array.from(new Set(speakerIds));
        const defaultAssignments: { [speakerId: number]: 'coach' | 'client' } = {};
        uniqueSpeakers.forEach((speakerId, index) => {
          defaultAssignments[speakerId] = index === 0 ? 'coach' : 'client';
        });
        setTempRoleAssignments(defaultAssignments);
      }
      
      // Initialize segment-level role assignments
      const segmentRoles: { [segmentId: string]: 'coach' | 'client' } = {};
      transcript.segments.forEach((segment) => {
        const segmentId = segment.id || `${segment.speaker_id}-${segment.start_sec}`;
        // Use existing segment roles if available, otherwise use speaker role assignments, or default
        if (transcript.segment_roles && transcript.segment_roles[segmentId]) {
          segmentRoles[segmentId] = transcript.segment_roles[segmentId];
        } else if (transcript.role_assignments && transcript.role_assignments[segment.speaker_id]) {
          segmentRoles[segmentId] = transcript.role_assignments[segment.speaker_id];
        } else {
          // Use safe fallback with proper convention
          segmentRoles[segmentId] = getSpeakerRoleFromId(segment.speaker_id, transcript.role_assignments);
        }
      });
      setTempSegmentRoles(segmentRoles);
    }
  }, [transcript]);

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
        if (exportFormat === 'json') {
          contentType = 'application/json';
        } else if (exportFormat === 'xlsx') {
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
    const role = getSpeakerRoleFromId(speakerId, transcript?.role_assignments);
    return getRoleDisplayName(role);
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
      const defaultRole = getSpeakerRoleFromId(segment.speaker_id, transcript?.role_assignments);
      roleString = defaultRole;
    }
    
    const role = roleString === 'coach' ? SpeakerRole.COACH : SpeakerRole.CLIENT;
    return getRoleDisplayName(role);
  };

  const getSpeakerColorFromId = (speakerId: number) => {
    const role = getSpeakerRoleFromId(speakerId, transcript?.role_assignments);
    return getSpeakerColor(role);
  };

  const calculateSpeakingStats = (segments: TranscriptSegment[]): SpeakingStats => {
    let coachTime = 0;
    let clientTime = 0;
    
    segments.forEach(segment => {
      const duration = segment.end_sec - segment.start_sec;
      const segmentId = segment.id || `${segment.speaker_id}-${segment.start_sec}`;
      
      // Determine role using safe priority logic
      let roleString: string;
      if (tempSegmentRoles[segmentId]) {
        roleString = tempSegmentRoles[segmentId];
      } else if (tempRoleAssignments[segment.speaker_id]) {
        roleString = tempRoleAssignments[segment.speaker_id];
      } else {
        // Use safe fallback
        const defaultRole = getSpeakerRoleFromId(segment.speaker_id, transcript?.role_assignments);
        roleString = defaultRole;
      }
      
      if (roleString === 'coach' || roleString === SpeakerRole.COACH) {
        coachTime += duration;
      } else {
        clientTime += duration;
      }
    });
    
    const totalSpeaking = coachTime + clientTime;
    const totalDuration = transcript?.duration_sec || 0;
    
    // Important note: STT total duration is usually the maximum timestamp from segments,
    // not the actual audio file duration. So silence time calculation may be inaccurate.
    // Only calculate silence time if total duration is significantly larger than speaking time
    let silenceTime = 0;
    if (totalDuration > totalSpeaking && (totalDuration - totalSpeaking) > 10) {
      // Only show silence time if there's at least 10 seconds difference
      silenceTime = totalDuration - totalSpeaking;
    }
    
    return {
      coach_speaking_time: coachTime,
      client_speaking_time: clientTime,
      total_speaking_time: totalSpeaking,
      coach_percentage: totalSpeaking > 0 ? (coachTime / totalSpeaking) * 100 : 0,
      client_percentage: totalSpeaking > 0 ? (clientTime / totalSpeaking) * 100 : 0,
      silence_time: silenceTime
    };
  };

  const generateAISummary = async () => {
    if (!transcript || !transcript.segments.length) return;
    
    setIsGeneratingAnalysis(true);
    try {
      // Mock AI analysis - in real implementation, this would call an AI service
      const mockSummary = `## 會談摘要

本次諮詢會談時長約 ${formatDuration(transcript.duration_sec)}，教練與客戶的對話比例為 ${speakingStats?.coach_percentage.toFixed(1)}% : ${speakingStats?.client_percentage.toFixed(1)}%。

### 主要討論議題
- 客戶分享了近期工作上的挑戰
- 探討了職涯發展的方向
- 討論了工作與生活平衡的策略

### 教練觀察
- 客戶在表達時較為謹慎，可能需要更多鼓勵
- 對於目標設定有清晰的想法
- 展現出積極的學習態度

### 後續建議
1. 客戶可嘗試設定SMART目標
2. 建議進行時間管理技巧的練習
3. 下次會談可深入討論具體行動計畫`;
      
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
      const mockResponse = `這是一個很好的問題。根據會談內容，我建議您可以從以下角度來思考：

1. 客戶在這方面表現出的模式
2. 可能的改善策略
3. 下次會談的重點方向

您還有其他想了解的嗎？`;
      setChatMessages(prev => [...prev, { role: 'assistant', content: mockResponse }]);
    }, 1000);
  };

  const saveRoleAssignments = async () => {
    if (!transcriptionSessionId) return;
    
    try {
      // Save segment-level role assignments via API
      await apiClient.updateSegmentRoles(transcriptionSessionId, tempSegmentRoles);
      
      // Update local transcript data to include segment roles
      setTranscript(prev => prev ? {
        ...prev,
        role_assignments: tempRoleAssignments,  // Keep speaker-level for compatibility
        segment_roles: tempSegmentRoles  // Add segment-level roles
      } : null);
      
      setEditingRoles(false);
      
      // Recalculate stats with new role assignments
      if (transcript) {
        const stats = calculateSpeakingStats(transcript.segments);
        setSpeakingStats(stats);
      }
    } catch (error) {
      console.error('Failed to save role assignments:', error);
      alert('儲存角色分配失敗，請稍後再試');
    }
  };

  const cancelRoleEditing = () => {
    // Reset to original assignments
    if (transcript?.role_assignments) {
      setTempRoleAssignments(transcript.role_assignments);
    }
    
    // Reset segment roles to original state
    if (transcript && transcript.segments) {
      const originalSegmentRoles: { [segmentId: string]: 'coach' | 'client' } = {};
      transcript.segments.forEach((segment) => {
        const segmentId = segment.id || `${segment.speaker_id}-${segment.start_sec}`;
        // Use saved segment roles if available, otherwise use speaker roles or default
        if (transcript.segment_roles && transcript.segment_roles[segmentId]) {
          originalSegmentRoles[segmentId] = transcript.segment_roles[segmentId];
        } else if (transcript.role_assignments && transcript.role_assignments[segment.speaker_id]) {
          originalSegmentRoles[segmentId] = transcript.role_assignments[segment.speaker_id];
        } else {
          originalSegmentRoles[segmentId] = getSpeakerRoleFromId(segment.speaker_id, transcript?.role_assignments);
        }
      });
      setTempSegmentRoles(originalSegmentRoles);
    }
    
    setEditingRoles(false);
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
        alert('請選擇 VTT 或 SRT 格式的檔案');
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
                speakerKey = `speaker_${speakerName.toLowerCase().replace(/\s+/g, '_')}`;
              } else {
                // Handle case without explicit speaker tag
                const fallbackMatch = contentLine.match(/^([^:：]+)[：:]\s*(.*)$/);
                if (fallbackMatch) {
                  speakerName = fallbackMatch[1].trim();
                  actualContent = fallbackMatch[2];
                  speakerKey = `speaker_${speakerName.toLowerCase().replace(/\s+/g, '_')}`;
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
              speakerKey = `speaker_${speakerName.toLowerCase().replace(/\s+/g, '_')}`;
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
      
      // Initialize default role mapping using consistent logic
      const defaultMapping: {[speakerId: string]: 'coach' | 'client'} = {};
      segments.forEach((segment, index) => {
        // Try to guess based on name first
        const name = segment.speaker_name.toLowerCase();
        if (name.includes('coach') || name.includes('教練') || name.includes('老師')) {
          defaultMapping[segment.speaker_id] = 'coach';
        } else if (name.includes('client') || name.includes('客戶') || name.includes('學員')) {
          defaultMapping[segment.speaker_id] = 'client';
        } else {
          // Use consistent convention: numeric speaker_id 0 = coach, others = client
          // Note: This assumes speaker_id is a number; if it's a string, parse it
          const speakerIdNum = typeof segment.speaker_id === 'number' ? segment.speaker_id : parseInt(segment.speaker_id);
          defaultMapping[segment.speaker_id] = speakerIdNum === SPEAKER_IDS.COACH ? 'coach' : 'client';
        }
      });
      setSpeakerRoleMapping(defaultMapping);
      
    } catch (error) {
      console.error('Error parsing file preview:', error);
      alert('無法解析檔案內容，請檢查檔案格式');
    }
  };

  const handleTranscriptUpload = async () => {
    if (!transcriptFile || !session) return;
    
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
      alert('逐字稿上傳成功！已建立 ' + response.segments_count + ' 個對話片段');
      
      // Switch to transcript tab to show the uploaded content
      setActiveTab('transcript');
      
      // Set upload mode back to audio for future uploads
      setUploadMode('audio');
      
    } catch (error) {
      console.error('Failed to upload transcript:', error);
      let errorMessage = '逐字稿上傳失敗，請重試';
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
          { value: 'TWD', label: 'TWD - 新台幣' },
          { value: 'USD', label: 'USD - 美元' },
          { value: 'CNY', label: 'CNY - 人民幣' }
        ]);
      }
    } catch (error) {
      console.error('Failed to fetch currencies:', error);
      setCurrencies([
        { value: 'TWD', label: 'TWD - 新台幣' },
        { value: 'USD', label: 'USD - 美元' },
        { value: 'CNY', label: 'CNY - 人民幣' }
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
            會談概覽
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
            逐字稿
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-800">
              Beta
            </span>
            {isTranscribing && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                處理中
              </span>
            )}
            {hasTranscript && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                已完成
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('analysis')}
            className={`pb-2 px-4 transition-colors flex items-center gap-2 ${
              activeTab === 'analysis' 
                ? 'text-blue-500 border-b-2 border-blue-500' 
                : 'text-content-secondary hover:text-content-primary'
            }`}
          >
            <ChatBubbleLeftRightIcon className="h-4 w-4" />
            AI 分析
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
              即將推出
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
                基本資料
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
                      <option value="" disabled>請選擇客戶</option>
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
                    逐字稿內容
                  </>
                ) : (
                  <>
                    <MicrophoneIcon className="h-5 w-5" />
                    音檔分析
                  </>
                )}
              </h3>
              
              {/* Upload Mode Selection */}
              {!transcriptionSessionId && !hasTranscript && !transcriptionSession && (
                <div className="mb-6">
                  <p className="text-sm text-content-secondary mb-3">請選擇上傳方式：</p>
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
                          <div className="font-medium text-content-primary">音檔分析</div>
                          <div className="text-sm text-content-secondary">上傳音檔進行 AI 轉錄</div>
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
                          <div className="font-medium text-content-primary">直接上傳逐字稿</div>
                          <div className="text-sm text-content-secondary">上傳 VTT/SRT 檔案</div>
                        </div>
                      </div>
                    </button>
                  </div>
                </div>
              )}

              {/* Audio Upload Mode */}
              {uploadMode === 'audio' && !transcriptionSessionId && !hasTranscript && (
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
              {uploadMode === 'transcript' && !transcriptionSessionId && !hasTranscript && (
                <div className="space-y-4">
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-400 p-4">
                    <div className="flex">
                      <div className="ml-3">
                        <p className="text-sm text-yellow-700 dark:text-yellow-200">
                          <strong>注意：</strong> 直接上傳的逐字稿將無法享有自動說話者辨識功能，需要手動編輯角色分配。
                        </p>
                      </div>
                    </div>
                  </div>

                  {!transcriptFile ? (
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-gray-400 transition-colors">
                      <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
                      <div className="mt-4">
                        <label htmlFor="transcript-upload" className="cursor-pointer">
                          <span className="text-lg font-medium text-content-primary">點擊上傳逐字稿</span>
                          <p className="text-sm text-content-secondary mt-1">支援 VTT、SRT 格式</p>
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
                            移除
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
                            <span className="font-medium text-content-primary">轉換為繁體中文</span>
                            <p className="text-sm text-content-secondary">
                              自動將簡體中文內容轉換為繁體中文
                            </p>
                          </div>
                        </label>
                      </div>

                      {/* Speaker Role Assignment */}
                      {previewSegments.length > 0 && (
                        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                          <h4 className="font-medium text-content-primary mb-3">說話者角色分配</h4>
                          <p className="text-sm text-content-secondary mb-4">
                            檔案中偵測到 {previewSegments.length} 位說話者，請為每位說話者指定角色：
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
                                        ({segment.count} 個片段)
                                      </span>
                                    </div>
                                    <p className="text-sm text-content-secondary italic">
                                      "{segment.content}"
                                    </p>
                                  </div>
                                  <div className="flex-shrink-0">
                                    <select
                                      value={speakerRoleMapping[segment.speaker_id] || 'coach'}
                                      onChange={(e) => setSpeakerRoleMapping(prev => ({
                                        ...prev,
                                        [segment.speaker_id]: e.target.value as 'coach' | 'client'
                                      }))}
                                      className="text-sm px-3 py-1 border border-border rounded-md bg-surface focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    >
                                      <option value="coach">教練</option>
                                      <option value="client">客戶</option>
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
                            上傳中...
                          </div>
                        ) : (
                          '上傳逐字稿'
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
                      <h4 className="font-medium text-blue-800 dark:text-blue-200">轉檔記錄</h4>
                      <p className="text-sm text-blue-600 dark:text-blue-300">
                        {hasTranscript ? 
                          '逐字稿已完成，可於逐字稿分頁查看內容' : 
                          transcriptionSession?.status === 'completed' ? 
                            '轉檔已完成，正在載入逐字稿...' :
                            `轉檔狀態：${transcriptionSession?.status || '檢查中...'}`
                        }
                      </p>
                      {transcriptionSession?.id && (
                        <p className="text-xs text-blue-500 dark:text-blue-400 mt-1">
                          轉檔 ID: {transcriptionSession.id}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}
              
              {/* Speaking Statistics - shown when transcript is available */}
              {speakingStats && hasTranscript && (
                <div className="mt-6 space-y-4">
                  <div className="border-t border-border pt-4">
                    <h4 className="font-medium text-content-primary mb-3">談話分析結果</h4>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Speaking Time Distribution */}
                    <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
                      <h4 className="font-medium text-content-primary mb-3">談話時間分配</h4>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-blue-600 font-medium">教練</span>
                          <span className="text-sm">{formatDuration(speakingStats.coach_speaking_time)} ({speakingStats.coach_percentage.toFixed(1)}%)</span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div 
                            className="bg-blue-500 h-2 rounded-full" 
                            style={{width: `${speakingStats.coach_percentage}%`}}
                          ></div>
                        </div>
                        
                        <div className="flex items-center justify-between">
                          <span className="text-green-600 font-medium">客戶</span>
                          <span className="text-sm">{formatDuration(speakingStats.client_speaking_time)} ({speakingStats.client_percentage.toFixed(1)}%)</span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div 
                            className="bg-green-500 h-2 rounded-full" 
                            style={{width: `${speakingStats.client_percentage}%`}}
                          ></div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Overall Stats */}
                    <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
                      <h4 className="font-medium text-content-primary mb-3">整體統計</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-content-secondary">總時長</span>
                          <span className="text-content-primary font-medium">{formatDuration(transcript?.duration_sec || 0)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-content-secondary">談話時間</span>
                          <span className="text-content-primary font-medium">{formatDuration(speakingStats.total_speaking_time)}</span>
                        </div>
                        {/* Silence time calculation is not accurate from STT, showing warning */}
                        <div className="flex justify-between">
                          <span className="text-content-secondary">
                            靜默時間
                            <span className="text-xs text-yellow-600 ml-1" title="此數據為推算值，可能不夠準確">
                              (推算)
                            </span>
                          </span>
                          <span className="text-content-primary font-medium">
                            {speakingStats.silence_time > 0 ? formatDuration(speakingStats.silence_time) : '無法計算'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-content-secondary">對話段數</span>
                          <span className="text-content-primary font-medium">{transcript?.segments.length || 0}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'transcript' && (
          <div className="space-y-4">
            {/* Transcription Status */}
            {(isTranscribing || transcriptionSession?.status === 'pending') && transcriptionStatus && (
              <div className="bg-surface border border-border rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4 text-content-primary">
                  轉檔處理中
                </h3>
                <TranscriptionProgress
                  progress={Number(transcriptionStatus.progress) || 0}
                  status={transcriptionSession?.status === 'processing' ? 'processing' : 'pending'}
                  message={transcriptionStatus.message || (transcriptionSession?.status === 'pending' ? '等待開始處理...' : '處理中...')}
                  estimatedTime={transcriptionStatus.estimated_completion ? 
                    formatTimeRemaining(transcriptionStatus.estimated_completion) : undefined}
                />
                {transcriptionStatus.duration_processed != null && 
                 transcriptionStatus.duration_total != null && 
                 transcriptionStatus.duration_total > 0 && (
                  <div className="mt-2 text-sm text-content-secondary">
                    已處理: {formatDuration(transcriptionStatus.duration_processed)} / {formatDuration(transcriptionStatus.duration_total)}
                  </div>
                )}
              </div>
            )}

            {/* Export Controls */}
            {hasTranscript && (
              <div className="bg-surface border border-border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <label className="text-sm font-medium text-content-primary">
                      匯出格式:
                    </label>
                    <select
                      value={exportFormat}
                      onChange={(e) => setExportFormat(e.target.value as any)}
                      className="px-3 py-1 border border-border rounded-md bg-surface text-content-primary"
                    >
                      <option value="vtt">WebVTT (.vtt)</option>
                      <option value="srt">SubRip (.srt)</option>
                      <option value="txt">純文字 (.txt)</option>
                      <option value="json">JSON (.json)</option>
                      <option value="xlsx">Excel (.xlsx)</option>
                    </select>
                  </div>
                  <Button
                    onClick={handleExportTranscript}
                    className="flex items-center gap-2"
                  >
                    <DocumentArrowDownIcon className="h-4 w-4" />
                    匯出逐字稿
                  </Button>
                </div>
              </div>
            )}

            {/* Transcript Table */}
            {hasTranscript && (
              <div className="bg-surface border border-border rounded-lg overflow-hidden">
                <div className="px-6 py-4 border-b border-border">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-content-primary">
                      對話紀錄
                    </h3>
                    <div className="flex items-center gap-4">
                      <div className="text-sm text-content-secondary">
                        總時長: {formatDuration(transcript.duration_sec)} | {transcript.segments.length} 段對話
                      </div>
                      {!editingRoles ? (
                        <Button
                          variant="outline"
                          onClick={() => setEditingRoles(true)}
                          className="flex items-center gap-2 text-sm px-3 py-1"
                        >
                          <PencilIcon className="h-3 w-3" />
                          編輯角色
                        </Button>
                      ) : (
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            onClick={cancelRoleEditing}
                            className="text-sm px-3 py-1"
                          >
                            取消
                          </Button>
                          <Button
                            onClick={saveRoleAssignments}
                            className="flex items-center gap-2 text-sm px-3 py-1"
                          >
                            儲存
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
                          時間
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-content-secondary uppercase tracking-wider w-24">
                          說話者
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-content-secondary uppercase tracking-wider">
                          內容
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-content-secondary uppercase tracking-wider w-16">
                          信心度
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
                            {editingRoles ? (
                              <select
                                value={tempSegmentRoles[segment.id || `${segment.speaker_id}-${segment.start_sec}`] || tempRoleAssignments[segment.speaker_id] || getSpeakerRoleFromId(segment.speaker_id, transcript?.role_assignments)}
                                onChange={(e) => {
                                  const segmentId = segment.id || `${segment.speaker_id}-${segment.start_sec}`;
                                  setTempSegmentRoles(prev => ({
                                    ...prev,
                                    [segmentId]: e.target.value as 'coach' | 'client'
                                  }));
                                }}
                                className="text-xs px-2 py-1 border border-border rounded bg-surface"
                              >
                                <option value="coach">教練</option>
                                <option value="client">客戶</option>
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
                                    roleString = getSpeakerRoleFromId(segment.speaker_id, transcript?.role_assignments);
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
                            {segment.content}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-xs text-content-secondary">
                            {segment.confidence ? `${Math.round(segment.confidence * 100)}%` : '-'}
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
                  <MicrophoneIcon className="h-16 w-16 text-content-secondary mx-auto" />
                  <p className="text-content-secondary mb-4">
                    此諮詢記錄尚未上傳音檔或逐字稿
                  </p>
                  <Button
                    onClick={() => setActiveTab('overview')}
                    className="mx-auto flex items-center gap-2"
                  >
                    <DocumentTextIcon className="h-4 w-4" />
                    前往概覽頁面上傳{isTranscriptOnly ? '逐字稿' : '音檔'}
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'analysis' && (
          <div className="space-y-6">
            {!hasTranscript ? (
              <div className="bg-surface border border-border rounded-lg p-12 text-center">
                <ChatBubbleLeftRightIcon className="h-16 w-16 text-content-secondary mx-auto mb-4" />
                <p className="text-content-secondary mb-4">
                  需要先上傳{isTranscriptOnly ? '逐字稿' : '音檔並完成轉檔'}才能使用 AI 分析功能
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
                  前往概覽頁面上傳{isTranscriptOnly ? '逐字稿' : '音檔'}
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* AI Summary */}
                <div className="bg-surface border border-border rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-content-primary flex items-center gap-2">
                      <DocumentMagnifyingGlassIcon className="h-5 w-5" />
                      會談摘要
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
                      {isGeneratingAnalysis ? '產生中...' : '產生摘要'}
                    </Button>
                  </div>
                  
                  <div className="prose prose-sm max-w-none text-content-primary">
                    {aiAnalysis ? (
                      <div className="whitespace-pre-wrap">{aiAnalysis}</div>
                    ) : (
                      <p className="text-content-secondary italic">
                        點擊「產生摘要」按鈕，讓 AI 幫您分析這次會談的重點和洞察
                      </p>
                    )}
                  </div>
                </div>

                {/* AI Chat */}
                <div className="bg-surface border border-border rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-content-primary flex items-center gap-2 mb-4">
                    <ChatBubbleLeftRightIcon className="h-5 w-5" />
                    AI 對話
                  </h3>
                  
                  {/* Chat Messages */}
                  <div className="space-y-4 max-h-96 overflow-y-auto mb-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    {chatMessages.length === 0 ? (
                      <p className="text-content-secondary text-sm italic text-center py-4">
                        您可以在這裡對會談內容提問，或請 AI 提供更深入的分析
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
                      placeholder="輸入您的問題..."
                      className="flex-1 px-3 py-2 border border-border rounded-md bg-surface text-content-primary focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <Button
                      onClick={sendChatMessage}
                      disabled={!currentMessage.trim()}
                      className="flex items-center gap-2"
                    >
                      <ChatBubbleLeftRightIcon className="h-4 w-4" />
                      發送
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default SessionDetailPage;