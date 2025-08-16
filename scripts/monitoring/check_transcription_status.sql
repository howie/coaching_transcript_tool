-- 檢查最近的轉檔 session
SELECT 
    id,
    status,
    audio_filename,
    transcription_job_id,
    created_at,
    updated_at
FROM session
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC
LIMIT 5;

-- 檢查處理狀態
SELECT 
    ps.session_id,
    ps.status,
    ps.progress,
    ps.message,
    ps.started_at,
    ps.estimated_completion,
    ps.created_at
FROM processing_status ps
JOIN session s ON ps.session_id = s.id
WHERE ps.created_at > NOW() - INTERVAL '24 hours'
ORDER BY ps.created_at DESC
LIMIT 10;

-- 檢查已完成的轉檔段落
SELECT 
    session_id,
    COUNT(*) as segment_count,
    MIN(start_sec) as first_segment_time,
    MAX(end_sec) as last_segment_time
FROM transcript_segment
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY session_id;
