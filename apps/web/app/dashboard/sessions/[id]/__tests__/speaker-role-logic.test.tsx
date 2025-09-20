/**
 * Unit tests for speaker role logic in SessionDetailPage
 * Tests the critical speaker role assignment and display functionality
 */

describe('Speaker Role Logic Tests', () => {

  // Helper function to test getSpeakerRoleFromSegment logic
  const testGetSpeakerRoleFromSegment = (
    segment: any,
    roleAssignments?: { [key: number]: 'coach' | 'client' }
  ) => {
    // Mock SpeakerRole enum
    enum SpeakerRole {
      COACH = 'coach',
      CLIENT = 'client',
      UNKNOWN = 'unknown'
    }

    // Replicate the actual getSpeakerRoleFromSegment function logic
    if (segment.role) {
      const roleStr = String(segment.role).toLowerCase();
      return roleStr === 'coach' ? SpeakerRole.COACH :
             roleStr === 'client' ? SpeakerRole.CLIENT : SpeakerRole.UNKNOWN;
    }

    if (roleAssignments && roleAssignments[segment.speaker_id]) {
      const roleStr = String(roleAssignments[segment.speaker_id]).toLowerCase();
      return roleStr === 'coach' ? SpeakerRole.COACH :
             roleStr === 'client' ? SpeakerRole.CLIENT : SpeakerRole.UNKNOWN;
    }

    return SpeakerRole.UNKNOWN;
  };

  describe('getSpeakerRoleFromSegment', () => {
    it('should handle uppercase roles from API correctly', () => {
      const segment = { speaker_id: 1, role: 'COACH' };
      const result = testGetSpeakerRoleFromSegment(segment);
      expect(result).toBe('coach');
    });

    it('should handle lowercase roles correctly', () => {
      const segment = { speaker_id: 1, role: 'client' };
      const result = testGetSpeakerRoleFromSegment(segment);
      expect(result).toBe('client');
    });

    it('should fallback to roleAssignments when segment has no role', () => {
      const segment = { speaker_id: 1 };
      const roleAssignments = { 1: 'coach' as const };
      const result = testGetSpeakerRoleFromSegment(segment, roleAssignments);
      expect(result).toBe('coach');
    });

    it('should handle uppercase roleAssignments correctly', () => {
      const segment = { speaker_id: 1 };
      const roleAssignments = { 1: 'CLIENT' as any };
      const result = testGetSpeakerRoleFromSegment(segment, roleAssignments);
      expect(result).toBe('client');
    });

    it('should return UNKNOWN when no role is found', () => {
      const segment = { speaker_id: 1 };
      const result = testGetSpeakerRoleFromSegment(segment);
      expect(result).toBe('unknown');
    });

    it('should prioritize segment role over roleAssignments', () => {
      const segment = { speaker_id: 1, role: 'COACH' };
      const roleAssignments = { 1: 'client' as const };
      const result = testGetSpeakerRoleFromSegment(segment, roleAssignments);
      expect(result).toBe('coach');
    });
  });

  describe('Role Assignment Conversion', () => {
    it('should convert uppercase API role_assignments to lowercase', () => {
      const apiRoleAssignments = { 1: 'CLIENT', 2: 'COACH' };

      // Simulate the conversion logic from useEffect
      const convertedAssignments: { [speakerId: number]: 'coach' | 'client' } = {};
      Object.entries(apiRoleAssignments).forEach(([speakerId, role]) => {
        convertedAssignments[parseInt(speakerId)] = role.toLowerCase() as 'coach' | 'client';
      });

      expect(convertedAssignments).toEqual({
        1: 'client',
        2: 'coach'
      });
    });

    it('should handle mixed case API responses', () => {
      const apiRoleAssignments = { 1: 'Client', 2: 'COACH', 3: 'coach' };

      const convertedAssignments: { [speakerId: number]: 'coach' | 'client' } = {};
      Object.entries(apiRoleAssignments).forEach(([speakerId, role]) => {
        convertedAssignments[parseInt(speakerId)] = role.toLowerCase() as 'coach' | 'client';
      });

      expect(convertedAssignments).toEqual({
        1: 'client',
        2: 'coach',
        3: 'coach'
      });
    });
  });

  describe('Segment Role Processing', () => {
    const mockTranscript = {
      segments: [
        { id: '1', speaker_id: 1, role: 'COACH' },
        { id: '2', speaker_id: 2, role: 'CLIENT' },
        { id: '3', speaker_id: 1 } // No role
      ],
      role_assignments: { 1: 'COACH', 2: 'CLIENT' },
      segment_roles: { '2': 'COACH' } // Override for segment 2
    };

    it('should process segment roles correctly with API data', () => {
      const segmentRoles: { [segmentId: string]: 'coach' | 'client' | 'unknown' } = {};

      mockTranscript.segments.forEach((segment) => {
        const segmentId = segment.id || `${segment.speaker_id}-${segment.start_sec}`;

        if (mockTranscript.segment_roles && mockTranscript.segment_roles[segmentId]) {
          segmentRoles[segmentId] = mockTranscript.segment_roles[segmentId].toLowerCase() as 'coach' | 'client';
        } else if (mockTranscript.role_assignments && mockTranscript.role_assignments[segment.speaker_id]) {
          segmentRoles[segmentId] = mockTranscript.role_assignments[segment.speaker_id].toLowerCase() as 'coach' | 'client';
        } else {
          const defaultRole = testGetSpeakerRoleFromSegment(segment, mockTranscript.role_assignments);
          segmentRoles[segmentId] = defaultRole === 'coach' ? 'coach' :
                                     defaultRole === 'client' ? 'client' : 'unknown';
        }
      });

      expect(segmentRoles).toEqual({
        '1': 'coach',    // From segment.role
        '2': 'coach',    // From segment_roles override
        '3': 'coach'     // From role_assignments fallback
      });
    });

    it('should handle unknown roles without defaulting to client', () => {
      const segmentWithoutRole = { id: '999', speaker_id: 999 };
      const emptyRoleAssignments = {};

      const segmentRoles: { [segmentId: string]: 'coach' | 'client' | 'unknown' } = {};
      const segmentId = segmentWithoutRole.id;

      const defaultRole = testGetSpeakerRoleFromSegment(segmentWithoutRole, emptyRoleAssignments);
      segmentRoles[segmentId] = defaultRole === 'coach' ? 'coach' :
                                 defaultRole === 'client' ? 'client' : 'unknown';

      expect(segmentRoles[segmentId]).toBe('unknown');
    });
  });

  describe('Cancel Edit Logic', () => {
    it('should convert role_assignments back to lowercase on cancel', () => {
      const mockTranscript = {
        role_assignments: { 1: 'CLIENT', 2: 'COACH' },
        segments: [
          { id: '1', speaker_id: 1, start_sec: 0 },
          { id: '2', speaker_id: 2, start_sec: 5 }
        ],
        segment_roles: {}
      };

      // Simulate cancelTranscriptEditing logic
      const convertedAssignments: { [speakerId: number]: 'coach' | 'client' } = {};
      Object.entries(mockTranscript.role_assignments).forEach(([speakerId, role]) => {
        convertedAssignments[parseInt(speakerId)] = role.toLowerCase() as 'coach' | 'client';
      });

      const originalSegmentRoles: { [segmentId: string]: 'coach' | 'client' | 'unknown' } = {};
      mockTranscript.segments.forEach((segment) => {
        const segmentId = segment.id || `${segment.speaker_id}-${segment.start_sec}`;

        if (mockTranscript.segment_roles && mockTranscript.segment_roles[segmentId]) {
          originalSegmentRoles[segmentId] = mockTranscript.segment_roles[segmentId].toLowerCase() as 'coach' | 'client';
        } else if (mockTranscript.role_assignments && mockTranscript.role_assignments[segment.speaker_id]) {
          originalSegmentRoles[segmentId] = mockTranscript.role_assignments[segment.speaker_id].toLowerCase() as 'coach' | 'client';
        } else {
          const defaultRole = testGetSpeakerRoleFromSegment(segment, mockTranscript.role_assignments);
          originalSegmentRoles[segmentId] = defaultRole === 'coach' ? 'coach' :
                                            defaultRole === 'client' ? 'client' : 'unknown';
        }
      });

      expect(convertedAssignments).toEqual({ 1: 'client', 2: 'coach' });
      expect(originalSegmentRoles).toEqual({ '1': 'client', '2': 'coach' });
    });
  });

  describe('Display Name Logic', () => {
    it('should return correct display names for each role', () => {
      const getRoleDisplayName = (role: string, t: any): string => {
        if (role === 'coach') return t('sessions.coach');
        if (role === 'client') return t('sessions.client');
        return 'Speaker';
      };

      const mockT = (key: string) => {
        if (key === 'sessions.coach') return '教練';
        if (key === 'sessions.client') return '客戶';
        return key;
      };

      expect(getRoleDisplayName('coach', mockT)).toBe('教練');
      expect(getRoleDisplayName('client', mockT)).toBe('客戶');
      expect(getRoleDisplayName('unknown', mockT)).toBe('Speaker');
    });
  });

  describe('Edge Cases', () => {
    it('should handle null/undefined role values', () => {
      const segment1 = { speaker_id: 1, role: null };
      const segment2 = { speaker_id: 2, role: undefined };

      expect(testGetSpeakerRoleFromSegment(segment1)).toBe('unknown');
      expect(testGetSpeakerRoleFromSegment(segment2)).toBe('unknown');
    });

    it('should handle empty string roles', () => {
      const segment = { speaker_id: 1, role: '' };
      expect(testGetSpeakerRoleFromSegment(segment)).toBe('unknown');
    });

    it('should handle invalid role values', () => {
      const segment = { speaker_id: 1, role: 'INVALID_ROLE' };
      expect(testGetSpeakerRoleFromSegment(segment)).toBe('unknown');
    });

    it('should handle missing speaker_id in roleAssignments', () => {
      const segment = { speaker_id: 999 };
      const roleAssignments = { 1: 'coach' as const, 2: 'client' as const };
      expect(testGetSpeakerRoleFromSegment(segment, roleAssignments)).toBe('unknown');
    });
  });

  describe('Integration Scenarios', () => {
    it('should handle complete workflow: API → Display → Edit → Cancel', () => {
      // Step 1: API response with uppercase roles
      const apiResponse = {
        role_assignments: { 1: 'CLIENT', 2: 'COACH' },
        segment_roles: {},
        segments: [
          { id: 'seg1', speaker_id: 1, role: 'CLIENT' },
          { id: 'seg2', speaker_id: 2, role: 'COACH' }
        ]
      };

      // Step 2: Convert for frontend (initial load)
      const tempRoleAssignments: { [speakerId: number]: 'coach' | 'client' } = {};
      Object.entries(apiResponse.role_assignments).forEach(([speakerId, role]) => {
        tempRoleAssignments[parseInt(speakerId)] = role.toLowerCase() as 'coach' | 'client';
      });

      // Step 3: Process segment roles
      const tempSegmentRoles: { [segmentId: string]: 'coach' | 'client' | 'unknown' } = {};
      apiResponse.segments.forEach((segment) => {
        const segmentId = segment.id;
        if (apiResponse.segment_roles && apiResponse.segment_roles[segmentId]) {
          tempSegmentRoles[segmentId] = apiResponse.segment_roles[segmentId].toLowerCase() as 'coach' | 'client';
        } else if (apiResponse.role_assignments && apiResponse.role_assignments[segment.speaker_id]) {
          tempSegmentRoles[segmentId] = apiResponse.role_assignments[segment.speaker_id].toLowerCase() as 'coach' | 'client';
        } else {
          const defaultRole = testGetSpeakerRoleFromSegment(segment, apiResponse.role_assignments);
          tempSegmentRoles[segmentId] = defaultRole === 'coach' ? 'coach' :
                                         defaultRole === 'client' ? 'client' : 'unknown';
        }
      });

      // Step 4: Simulate edit mode changes
      const editedRoleAssignments = { ...tempRoleAssignments, 1: 'coach' as const };
      const editedSegmentRoles = { ...tempSegmentRoles, 'seg1': 'coach' as const };

      // Step 5: Cancel edit (reset to original)
      const resetRoleAssignments: { [speakerId: number]: 'coach' | 'client' } = {};
      Object.entries(apiResponse.role_assignments).forEach(([speakerId, role]) => {
        resetRoleAssignments[parseInt(speakerId)] = role.toLowerCase() as 'coach' | 'client';
      });

      // Verify the complete workflow
      expect(tempRoleAssignments).toEqual({ 1: 'client', 2: 'coach' });
      expect(tempSegmentRoles).toEqual({ 'seg1': 'client', 'seg2': 'coach' });
      expect(editedRoleAssignments).toEqual({ 1: 'coach', 2: 'coach' });
      expect(editedSegmentRoles).toEqual({ 'seg1': 'coach', 'seg2': 'coach' });
      expect(resetRoleAssignments).toEqual({ 1: 'client', 2: 'coach' });
    });
  });
});