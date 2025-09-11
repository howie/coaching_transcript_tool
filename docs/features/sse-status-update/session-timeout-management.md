# Session Timeout Management & Emergency Recovery

## 🚨 Critical Production Issue

**Date**: 2025-09-11  
**Priority**: P0 - Critical  
**Impact**: 5 sessions stuck in processing state for 5-7 days  

## Problem Analysis

### Current Stuck Sessions (Production)
```
Session ae51bf07...: 9,856 minutes (6.8 days) in processing
Session 271930c1...: 9,656 minutes (6.7 days) in processing  
Session d5eae700...: 9,375 minutes (6.5 days) in processing
Session 926e58fa...: 8,186 minutes (5.7 days) in processing
Session 04585e32...: 1,178 minutes (19.6 hours) in processing
```

### Root Causes
1. **No timeout mechanism** for stuck sessions
2. **No monitoring alerts** for long-running sessions
3. **No automatic recovery** from processing failures
4. **Poor user experience** with indefinite "processing" status

## Emergency Action Plan

### Phase 1: Immediate Reset (Today) ⚡

#### 1.1 Manual Session Reset Script
```python
# scripts/emergency_session_reset.py
#!/usr/bin/env python3
"""Emergency script to reset stuck transcription sessions"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from src.coaching_assistant.core.database import get_db
from src.coaching_assistant.models.transcription_session import TranscriptionSession
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_stuck_sessions(timeout_minutes=30, dry_run=True):
    """Reset sessions stuck in processing state"""
    db = next(get_db())
    
    cutoff_time = datetime.now() - timedelta(minutes=timeout_minutes)
    
    # Find stuck sessions
    stuck_sessions = db.query(TranscriptionSession).filter(
        TranscriptionSession.status == 'processing',
        TranscriptionSession.created_at < cutoff_time
    ).all()
    
    logger.info(f"Found {len(stuck_sessions)} stuck sessions")
    
    for session in stuck_sessions:
        processing_time = datetime.now() - session.created_at
        logger.info(f"Session {session.id}: stuck for {processing_time}")
        
        if not dry_run:
            session.status = 'failed'
            session.error_message = f'Session timeout after {processing_time} - automatically reset'
            session.updated_at = datetime.now()
            logger.info(f"Reset session {session.id} to failed status")
    
    if not dry_run:
        db.commit()
        logger.info(f"Successfully reset {len(stuck_sessions)} sessions")
    else:
        logger.info("DRY RUN - No changes made. Use --execute to apply changes")
    
    db.close()
    return len(stuck_sessions)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Reset stuck transcription sessions')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout in minutes')
    parser.add_argument('--execute', action='store_true', help='Actually execute changes')
    
    args = parser.parse_args()
    
    dry_run = not args.execute
    count = reset_stuck_sessions(args.timeout, dry_run)
    
    if dry_run:
        print(f"Would reset {count} sessions. Use --execute to apply changes.")
    else:
        print(f"Successfully reset {count} sessions.")
```

#### 1.2 Database Direct Reset (Backup Option)
```sql
-- Emergency SQL to reset stuck sessions
-- Run this if the Python script fails

BEGIN;

-- Show stuck sessions first
SELECT 
    id,
    status,
    created_at,
    EXTRACT(EPOCH FROM (NOW() - created_at))/60 as minutes_stuck
FROM transcription_sessions 
WHERE status = 'processing' 
  AND created_at < NOW() - INTERVAL '30 minutes'
ORDER BY created_at;

-- Reset stuck sessions
UPDATE transcription_sessions 
SET 
    status = 'failed',
    error_message = 'Session timeout - manually reset via emergency procedure',
    updated_at = NOW()
WHERE status = 'processing' 
  AND created_at < NOW() - INTERVAL '30 minutes';

-- Verify changes
SELECT COUNT(*) as reset_count FROM transcription_sessions 
WHERE status = 'failed' 
  AND error_message LIKE 'Session timeout - manually reset%';

COMMIT;
```

#### 1.3 Execution Steps
```bash
# 1. Test the reset script (dry run)
cd /Users/howie/Workspace/github/coaching_transcript_tool
python scripts/emergency_session_reset.py --timeout 30

# 2. Execute the reset
python scripts/emergency_session_reset.py --timeout 30 --execute

# 3. Verify results
python -c "
from src.coaching_assistant.core.database import get_db
from src.coaching_assistant.models.transcription_session import TranscriptionSession
db = next(get_db())
processing_count = db.query(TranscriptionSession).filter(TranscriptionSession.status == 'processing').count()
print(f'Remaining processing sessions: {processing_count}')
db.close()
"
```

### Phase 2: Monitoring & Alerts (This Week) 📊

#### 2.1 Session Health Monitor Service
```python
# src/coaching_assistant/services/session_health_monitor.py
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.transcription_session import TranscriptionSession
from .notification_service import NotificationService

logger = logging.getLogger(__name__)

class SessionHealthMonitor:
    """Monitor session health and automatically timeout stuck sessions"""
    
    def __init__(self, timeout_minutes: int = 30, check_interval: int = 300):
        self.timeout_minutes = timeout_minutes
        self.check_interval = check_interval  # 5 minutes
        self.notification_service = NotificationService()
        self.running = False
    
    async def start_monitoring(self):
        """Start the monitoring loop"""
        self.running = True
        logger.info(f"Starting session health monitor (timeout: {self.timeout_minutes}min, interval: {self.check_interval}s)")
        
        while self.running:
            try:
                await self.check_session_health()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in session health monitor: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.running = False
        logger.info("Stopping session health monitor")
    
    async def check_session_health(self):
        """Check for stuck sessions and timeout them"""
        db: Session = next(get_db())
        
        try:
            cutoff_time = datetime.now() - timedelta(minutes=self.timeout_minutes)
            
            # Find stuck sessions
            stuck_sessions = db.query(TranscriptionSession).filter(
                TranscriptionSession.status == 'processing',
                TranscriptionSession.created_at < cutoff_time
            ).all()
            
            if stuck_sessions:
                logger.warning(f"Found {len(stuck_sessions)} stuck sessions")
                
                for session in stuck_sessions:
                    await self.timeout_session(db, session)
                
                # Send alert
                await self.notification_service.send_session_timeout_alert(len(stuck_sessions))
            
            # Also check for general health metrics
            await self.check_processing_health(db)
            
        finally:
            db.close()
    
    async def timeout_session(self, db: Session, session: TranscriptionSession):
        """Timeout a specific session"""
        processing_time = datetime.now() - session.created_at
        
        session.status = 'failed'
        session.error_message = f'Processing timeout after {processing_time} - automatically failed by health monitor'
        session.updated_at = datetime.now()
        
        db.commit()
        
        logger.info(f"Timed out session {session.id} (processing for {processing_time})")
        
        # TODO: Send SSE notification to user
        # await self.send_sse_notification(session.user_id, {
        #     'type': 'session_timeout',
        #     'session_id': str(session.id),
        #     'message': 'Session processing timed out'
        # })
    
    async def check_processing_health(self, db: Session):
        """Check overall processing health"""
        # Count sessions by status
        processing_count = db.query(TranscriptionSession).filter(
            TranscriptionSession.status == 'processing'
        ).count()
        
        # Count long-running sessions (>15 minutes)
        warning_cutoff = datetime.now() - timedelta(minutes=15)
        long_running_count = db.query(TranscriptionSession).filter(
            TranscriptionSession.status == 'processing',
            TranscriptionSession.created_at < warning_cutoff
        ).count()
        
        # Alert if too many long-running sessions
        if long_running_count > 3:
            await self.notification_service.send_health_degradation_alert({
                'processing_sessions': processing_count,
                'long_running_sessions': long_running_count,
                'threshold': 3
            })
            
        logger.info(f"Health check: {processing_count} processing, {long_running_count} long-running")

# Background task to start the monitor
monitor = SessionHealthMonitor()

async def start_session_health_monitor():
    """Start the session health monitor as a background task"""
    await monitor.start_monitoring()
```

#### 2.2 Health Check API Endpoint
```python
# src/coaching_assistant/api/v1/health.py
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.transcription_session import TranscriptionSession

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/sessions")
async def get_session_health(db: Session = Depends(get_db)):
    """Get session processing health metrics"""
    current_time = datetime.now()
    
    # Count sessions by status
    total_sessions = db.query(TranscriptionSession).count()
    processing_sessions = db.query(TranscriptionSession).filter(
        TranscriptionSession.status == 'processing'
    ).count()
    
    # Count long-running sessions
    warning_cutoff = current_time - timedelta(minutes=15)
    timeout_cutoff = current_time - timedelta(minutes=30)
    
    long_running = db.query(TranscriptionSession).filter(
        TranscriptionSession.status == 'processing',
        TranscriptionSession.created_at < warning_cutoff
    ).count()
    
    stuck_sessions = db.query(TranscriptionSession).filter(
        TranscriptionSession.status == 'processing',
        TranscriptionSession.created_at < timeout_cutoff
    ).count()
    
    # Determine overall health status
    if stuck_sessions > 0:
        status = "critical"
    elif long_running > 3:
        status = "warning"
    else:
        status = "healthy"
    
    return {
        "status": status,
        "timestamp": current_time.isoformat(),
        "metrics": {
            "total_sessions": total_sessions,
            "processing_sessions": processing_sessions,
            "long_running_sessions": long_running,
            "stuck_sessions": stuck_sessions
        },
        "thresholds": {
            "warning_minutes": 15,
            "timeout_minutes": 30,
            "max_long_running": 3
        }
    }

@router.get("/sessions/stuck")
async def get_stuck_sessions(db: Session = Depends(get_db)):
    """Get details of stuck sessions for debugging"""
    timeout_cutoff = datetime.now() - timedelta(minutes=30)
    
    stuck_sessions = db.query(TranscriptionSession).filter(
        TranscriptionSession.status == 'processing',
        TranscriptionSession.created_at < timeout_cutoff
    ).all()
    
    session_details = []
    for session in stuck_sessions:
        processing_time = datetime.now() - session.created_at
        session_details.append({
            "id": str(session.id),
            "user_id": str(session.user_id),
            "created_at": session.created_at.isoformat(),
            "processing_minutes": int(processing_time.total_seconds() / 60),
            "file_name": getattr(session, 'audio_file_name', 'unknown')
        })
    
    return {
        "stuck_sessions": session_details,
        "count": len(session_details)
    }
```

#### 2.3 Notification Service
```python
# src/coaching_assistant/services/notification_service.py
import asyncio
import logging
from typing import Dict, Any
import aiohttp

logger = logging.getLogger(__name__)

class NotificationService:
    """Send alerts and notifications for system events"""
    
    def __init__(self):
        self.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        self.alert_email = os.getenv('ALERT_EMAIL', 'admin@coachly.ai')
    
    async def send_session_timeout_alert(self, session_count: int):
        """Send alert when sessions are timing out"""
        message = f"⚠️ Session Timeout Alert: {session_count} sessions have been automatically reset to failed status due to processing timeout"
        
        await self.send_slack_alert(message)
        logger.warning(f"Session timeout alert sent: {session_count} sessions timed out")
    
    async def send_health_degradation_alert(self, metrics: Dict[str, Any]):
        """Send alert when system health degrades"""
        message = f"🚨 System Health Alert: {metrics['long_running_sessions']} long-running sessions detected (threshold: {metrics['threshold']})"
        
        await self.send_slack_alert(message)
        logger.error(f"Health degradation alert sent: {metrics}")
    
    async def send_slack_alert(self, message: str):
        """Send alert to Slack webhook"""
        if not self.slack_webhook_url:
            logger.warning("Slack webhook URL not configured, skipping Slack alert")
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"text": message}
                async with session.post(self.slack_webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info("Slack alert sent successfully")
                    else:
                        logger.error(f"Failed to send Slack alert: {response.status}")
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
```

### Phase 3: Integration with SSE (Next Week) 🔄

#### 3.1 SSE Session Status Updates
```python
# Integrate with existing SSE implementation
# When session times out, send real-time notification to user

async def notify_session_timeout_via_sse(user_id: str, session_id: str):
    """Send session timeout notification via SSE"""
    message = {
        "type": "session_timeout",
        "session_id": session_id,
        "status": "failed",
        "message": "Session processing timed out",
        "timestamp": datetime.now().isoformat()
    }
    
    # Add to SSE message queue for this user
    await add_sse_message(user_id, message)
```

## Deployment Plan

### Immediate (Today) ⚡
1. ✅ Create and test emergency reset script
2. ✅ Execute session reset in production
3. ✅ Verify all stuck sessions are resolved

### Short-term (This Week) 📊
1. 🔄 Deploy session health monitor service
2. 🔄 Add health check API endpoints
3. 🔄 Set up Slack alerting
4. 🔄 Configure monitoring dashboard

### Medium-term (Next Week) 🔄
1. 📋 Integrate timeout notifications with SSE
2. 📋 Add user-facing timeout messages
3. 📋 Implement progressive timeout warnings
4. 📋 Add session recovery mechanisms

## Configuration

### Environment Variables
```env
# Session timeout settings
SESSION_TIMEOUT_MINUTES=30
SESSION_HEALTH_CHECK_INTERVAL=300
SESSION_WARNING_THRESHOLD=15
MAX_LONG_RUNNING_SESSIONS=3

# Alert settings
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
ALERT_EMAIL=admin@coachly.ai

# Health monitoring
HEALTH_CHECK_ENABLED=true
AUTO_TIMEOUT_ENABLED=true
```

### Systemd Service (Optional)
```ini
# /etc/systemd/system/session-health-monitor.service
[Unit]
Description=Session Health Monitor
After=network.target

[Service]
Type=simple
User=app
WorkingDirectory=/app
ExecStart=/app/venv/bin/python -m src.coaching_assistant.services.session_health_monitor
Restart=always
RestartSec=10
Environment=DATABASE_URL=postgresql://...

[Install]
WantedBy=multi-user.target
```

## Testing Plan

### Unit Tests
```python
# tests/test_session_health_monitor.py
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.coaching_assistant.services.session_health_monitor import SessionHealthMonitor

@pytest.fixture
def mock_db():
    return Mock()

@pytest.fixture
def health_monitor():
    return SessionHealthMonitor(timeout_minutes=30, check_interval=5)

async def test_timeout_stuck_session(health_monitor, mock_db):
    """Test that stuck sessions are properly timed out"""
    # Create mock stuck session
    stuck_session = Mock()
    stuck_session.id = "test-session-id"
    stuck_session.status = "processing"
    stuck_session.created_at = datetime.now() - timedelta(hours=2)
    
    mock_db.query.return_value.filter.return_value.all.return_value = [stuck_session]
    
    await health_monitor.timeout_session(mock_db, stuck_session)
    
    assert stuck_session.status == "failed"
    assert "timeout" in stuck_session.error_message.lower()
    mock_db.commit.assert_called_once()

async def test_health_check_alert_threshold(health_monitor, mock_db):
    """Test that alerts are sent when threshold is exceeded"""
    mock_db.query.return_value.filter.return_value.count.return_value = 5  # > threshold
    
    with patch.object(health_monitor.notification_service, 'send_health_degradation_alert') as mock_alert:
        await health_monitor.check_processing_health(mock_db)
        mock_alert.assert_called_once()
```

### Integration Tests
```python
# tests/integration/test_emergency_reset.py
def test_emergency_session_reset():
    """Test emergency session reset script end-to-end"""
    # Create test stuck sessions
    # Run reset script
    # Verify sessions are reset
    pass
```

## Success Metrics

### Immediate Success (Phase 1)
- ✅ Zero sessions stuck > 30 minutes
- ✅ All 5 current stuck sessions resolved
- ✅ Emergency procedures documented and tested

### Short-term Success (Phase 2)
- 📊 Automatic timeout detection within 5 minutes
- 📊 Alert response time < 30 seconds
- 📊 Zero manual intervention required for timeouts

### Long-term Success (Phase 3)
- 🔄 Real-time user notifications for timeouts
- 🔄 < 1% session timeout rate during normal operation
- 🔄 Improved user satisfaction with session reliability

## Risk Mitigation

### False Positives
- **Risk**: Timing out legitimately slow sessions
- **Mitigation**: Progressive timeouts based on file size, configurable thresholds

### Service Dependencies
- **Risk**: Health monitor service fails
- **Mitigation**: Multiple monitoring methods, external health checks

### Data Loss
- **Risk**: Timing out sessions with valuable data
- **Mitigation**: Preserve session data, allow manual recovery

---

**Owner**: Platform Engineering Team  
**Priority**: P0 - Critical  
**Status**: Emergency response required  
**Next Review**: Daily until Phase 1 complete