# WP6: Bug Fix - Session Upload ID Mismatch

## Problem Statement

When uploading audio files through the AudioUploader component, the system fails with a "Session not found" error. The root cause is a mismatch between coaching session IDs and transcription session IDs.

## Error Analysis

### Symptoms
1. User navigates to `/dashboard/sessions/{coaching-session-id}`
2. Attempts to upload audio file
3. System returns 404 error: "Session not found"
4. Upload fails despite successful transcription session creation

### Root Cause

The AudioUploader component has a critical bug in its error handling flow:

```javascript
// Current problematic flow:
1. Create transcription session (POST /api/v1/sessions)
2. If creation fails silently or returns unexpected format
3. Code continues with undefined/invalid session.id
4. getUploadUrl called with wrong ID (falls back to coaching session ID)
5. Backend rejects because coaching session ID != transcription session ID
```

### Log Evidence

```
POST /api/v1/sessions HTTP/1.1" 200 OK  // Success!
POST /api/v1/sessions/1deb074d-2ab7-46ae-bd66-ff430f09baec/upload-url 404  // Wrong ID!
❌ Upload URL request failed - Session 1deb074d-2ab7-46ae-bd66-ff430f09baec not found
```

The `1deb074d-2ab7-46ae-bd66-ff430f09baec` is the coaching session ID, not the newly created transcription session ID.

## Technical Details

### Current Code Flow (Buggy)

```typescript
// AudioUploader.tsx - handleUpload function
const session = await apiClient.createTranscriptionSession({
  title: sessionTitle.trim(),
  language: language
})
// BUG: No validation that session.id exists
// BUG: If session creation fails, session might be undefined
const uploadData = await apiClient.getUploadUrl(
  session.id,  // Could be undefined!
  selectedFile.name,
  fileSizeMB
)
```

### API Endpoint Expectations

The `/api/v1/sessions/{session_id}/upload-url` endpoint expects:
- A valid **transcription session ID** from the `session` table
- NOT a coaching session ID from the `coaching_sessions` table

## Solution

### Fix 1: Add Proper Validation After Session Creation

```typescript
// Step 1: Create transcription session with proper error handling
let session;
try {
  session = await apiClient.createTranscriptionSession({
    title: sessionTitle.trim(),
    language: language
  });

  // CRITICAL: Validate session response
  if (!session || !session.id) {
    throw new Error('Failed to create transcription session: Invalid response');
  }

  console.log('✅ Transcription session created:', session.id);
} catch (error) {
  console.error('❌ Failed to create transcription session:', error);
  setUploadState(prev => ({
    ...prev,
    status: 'failed',
    progress: 0,
    error: t('audio.sessionCreationFailed')
  }));
  return; // STOP execution here
}

// Step 2: Only proceed if we have a valid session ID
const uploadData = await apiClient.getUploadUrl(
  session.id,  // Now guaranteed to exist
  selectedFile.name,
  fileSizeMB
);
```

### Fix 2: Improve Error Messages

```typescript
catch (error: any) {
  console.error('Upload error at step:', uploadState.currentPhase, error);

  // Provide specific error messages based on phase
  let errorMessage = t('audio.uploadFailed');
  if (uploadState.currentPhase === 'creating_session') {
    errorMessage = t('audio.sessionCreationFailed');
  } else if (uploadState.currentPhase === 'uploading_file') {
    errorMessage = t('audio.fileUploadFailed');
  }

  setUploadState(prev => ({
    ...prev,
    status: 'failed',
    progress: 0,
    error: error.message || errorMessage
  }));
}
```

### Fix 3: Add Debug Logging

```typescript
// Add comprehensive logging for debugging
console.log('📋 Upload flow started', {
  coachingSessionId: sessionId,
  fileName: selectedFile.name,
  fileSize: fileSizeMB
});

const session = await apiClient.createTranscriptionSession({
  title: sessionTitle.trim(),
  language: language
});

console.log('📋 Transcription session response:', {
  success: !!session,
  hasId: !!(session?.id),
  sessionId: session?.id,
  fullResponse: session
});
```

## Implementation Plan

1. **Update AudioUploader.tsx**
   - Add session validation after creation
   - Implement early return on error
   - Add comprehensive logging
   - Improve error messages

2. **Update API Client (optional)**
   - Add response validation in `createTranscriptionSession`
   - Ensure consistent error handling

3. **Testing**
   - Test with valid audio file
   - Test with network errors
   - Test with API failures
   - Verify proper session ID usage

## Files to Modify

1. `/apps/web/components/AudioUploader.tsx` - Main fix location
2. `/apps/web/lib/i18n/translations/audio.ts` - Add new error messages

## Success Criteria

- [ ] Audio upload succeeds without 404 errors
- [ ] Proper transcription session ID is used for upload URL
- [ ] Clear error messages when session creation fails
- [ ] No confusion between coaching and transcription session IDs
- [ ] Debug logs show correct session ID flow

## Implementation Status

### ✅ Completed Fixes

1. **Session Validation Added** (AudioUploader.tsx:293-296)
   ```typescript
   if (!session || !session.id) {
     console.error('❌ Failed to create transcription session: Invalid response', { session });
     throw new Error('Failed to create transcription session: Invalid response from server');
   }
   ```

2. **Debug Logging Enhanced** (AudioUploader.tsx:274-290)
   ```typescript
   console.log('📋 Upload flow started', {
     coachingSessionId: sessionId,
     fileName: selectedFile.name,
     fileSize: (selectedFile.size / (1024 * 1024)).toFixed(2) + ' MB'
   });

   console.log('📋 Transcription session response:', {
     success: !!session,
     hasId: !!(session?.id),
     sessionId: session?.id,
     fullResponse: session
   });
   ```

3. **Error Handling Improved** (AudioUploader.tsx:431-447)
   ```typescript
   // Provide specific error messages based on phase
   let errorMessage = t('audio.uploadFailed');
   if (uploadState.currentPhase === 'creating_session') {
     errorMessage = error.message || t('audio.sessionCreationFailed');
     console.error('❌ Session creation failed:', {
       coachingSessionId: sessionId,
       error: error.message,
       stack: error.stack
     });
   }
   ```

4. **Translation Updates** (audio.ts:79-81, 169-171)
   - Added `audio.sessionCreationFailed`
   - Added `audio.fileUploadFailed`
   - Added `audio.confirmationFailed`

### 🔍 Current Issues Still Being Investigated

Despite the fixes, you may still see errors if:

1. **Session Creation API Fails**
   - The `POST /api/v1/sessions` might be returning an unexpected response format
   - Check browser console for the new debug logs to see actual response

2. **Authentication Issues**
   - If user authentication fails, session creation will fail
   - Look for 401 errors in network tab

3. **Database/Backend Issues**
   - Backend might have database connection issues
   - Check backend logs for SQL errors

### 🛠️ Debugging Next Steps

To identify remaining issues, check:

1. **Browser Console** - Look for new debug messages:
   ```
   📋 Upload flow started
   📋 Transcription session response
   ❌ Session creation failed (if error occurs)
   ```

2. **Network Tab** - Check these API calls:
   ```
   POST /api/v1/sessions (should return 200 with session object)
   POST /api/v1/sessions/{id}/upload-url (should use transcription session ID)
   ```

3. **Backend Logs** - Look for session creation errors

### 💡 What to Report

Please provide:
- Browser console logs (specifically the new 📋 debug messages)
- Network tab showing failed requests
- Exact error message you're seeing
- Which step fails (session creation, upload URL, file upload, etc.)

## Migration Notes

This fix is backward compatible and requires no database changes. The issue was in frontend error handling logic and has been addressed with better validation and debugging.