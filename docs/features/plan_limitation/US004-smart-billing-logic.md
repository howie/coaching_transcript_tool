# US004: Smart Billing Logic

## 📋 User Story

**As a** platform user and business owner  
**I want** intelligent billing for re-transcription requests that distinguishes between failure retries and intentional re-transcription  
**So that** users are not charged for system failures while ensuring accurate billing for legitimate re-transcription services

## 💼 Business Value

### Current Problem
- No distinction between failure retries (should be free) and intentional re-transcription (should be charged)
- Users may be unfairly charged for system failures or provider issues
- Business loses revenue from legitimate re-transcription requests that should be charged
- No clear policy or implementation for retry vs re-transcription billing logic
- Customer support overhead from billing disputes and confusion

### Business Impact
- **Customer Satisfaction**: Users charged for system failures leads to support complaints and churn
- **Revenue Accuracy**: Missing revenue from legitimate re-transcription requests (~$5-10K/month potential)
- **Support Overhead**: Manual billing adjustments for failure-related charges
- **Platform Trust**: Unclear billing practices reduce user confidence and retention
- **Competitive Disadvantage**: Other platforms offer clear retry policies

### Value Delivered
- **Fair Billing**: Free retries for failures, appropriate charges for re-transcription services
- **Revenue Optimization**: Capture legitimate re-transcription revenue without penalizing users
- **User Transparency**: Clear distinction between retry and re-transcription in billing
- **Automated Billing**: No manual intervention needed for billing classification
- **Improved Trust**: Clear, fair billing practices increase user satisfaction and retention

## 🎯 Acceptance Criteria

### Transcription Type Classification
1. **Failure Retry Logic**
   - [ ] Failed transcriptions can be retried without additional charge
   - [ ] System automatically identifies retry scenarios (session status = FAILED)
   - [ ] Retries preserve original session and don't create new usage logs for billing
   - [ ] Multiple retries of same failed session remain free
   - [ ] Clear "Retry" button for failed sessions with "Free" indication

2. **Re-transcription Logic**
   - [ ] Successfully completed sessions can be re-transcribed (new transcription)
   - [ ] Re-transcription creates new billable usage log entry
   - [ ] Re-transcription preserves original transcription data for comparison
   - [ ] Clear user intent confirmation for charged re-transcription with cost estimate
   - [ ] Re-transcription counted against monthly transcription limits

3. **Usage Tracking Integration**
   - [ ] Usage logs include transcription_type field (original, retry_failed, retry_success)
   - [ ] Billing calculations respect transcription type classification
   - [ ] User.usage_minutes only incremented for chargeable transcriptions
   - [ ] Analytics distinguish between different transcription types for reporting

### API Enhancements
4. **Enhanced Retry Endpoint**
   - [ ] Existing `/retry-transcription` endpoint remains free for failures
   - [ ] Enhanced logic validates session status before allowing retry
   - [ ] Clear error messages for invalid retry attempts (e.g., trying to retry successful session)
   - [ ] Retry preserves original transcription metadata and settings

5. **New Re-transcription Endpoint**
   - [ ] New `/retranscribe` endpoint for intentional re-transcription of successful sessions
   - [ ] User confirmation required with detailed cost estimate
   - [ ] Provider selection support for re-transcription (Google STT vs AssemblyAI)
   - [ ] Progress tracking for re-transcription requests with status updates

### User Interface Updates
6. **Clear Action Distinction**
   - [ ] Failed sessions show "Retry (Free)" button with clear messaging
   - [ ] Successful sessions show "Re-transcribe" button with cost indication
   - [ ] Cost estimates shown before re-transcription confirmation with breakdown
   - [ ] Usage history clearly labels transcription types and billing status
   - [ ] Billing history distinguishes between free retries and paid re-transcriptions

### Cost Estimation & Transparency
7. **Accurate Cost Estimation**
   - [ ] Cost estimation based on actual session duration and selected provider
   - [ ] Provider-specific pricing (Google STT vs AssemblyAI different rates)
   - [ ] Real-time cost calculation before user confirmation
   - [ ] Historical cost reference from original transcription

## 🏗️ Technical Implementation

### Enhanced Usage Log Classification
```python
# packages/core-logic/src/coaching_assistant/models/usage_log.py (Updated from US001)

import enum
from sqlalchemy import Column, String, Boolean, UUID, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class TranscriptionType(enum.Enum):
    """Classification of transcription types for billing"""
    ORIGINAL = "original"          # First transcription attempt
    RETRY_FAILED = "retry_failed"  # Retry after failure (free)
    RETRY_SUCCESS = "retry_success" # Re-transcription of successful session (charged)

class UsageLog(BaseModel):
    """Enhanced usage log with transcription type tracking"""
    
    # ... existing fields from US001 ...
    
    # Billing classification
    transcription_type = Column(Enum(TranscriptionType), nullable=False)
    parent_log_id = Column(UUID(as_uuid=True), ForeignKey("usage_logs.id"), nullable=True)
    
    # Billing metadata
    is_billable = Column(Boolean, nullable=False, default=True)
    billing_reason = Column(String(100), nullable=True)  # "original", "retry_free", "retranscription_requested"
    cost_breakdown = Column(JSONB, default=dict)  # Detailed cost breakdown
    
    # Relationships
    parent_usage_log = relationship("UsageLog", remote_side=[id])
    child_usage_logs = relationship("UsageLog", back_populates="parent_usage_log")
    
    @property
    def billing_description(self) -> str:
        """Get human-readable billing description"""
        if self.transcription_type == TranscriptionType.ORIGINAL:
            return "Original transcription"
        elif self.transcription_type == TranscriptionType.RETRY_FAILED:
            return "Failure retry (no charge)"
        elif self.transcription_type == TranscriptionType.RETRY_SUCCESS:
            return "Re-transcription service"
        return "Unknown transcription type"
    
    @property
    def should_charge_user(self) -> bool:
        """Determine if this usage should be charged to user"""
        return self.is_billable and self.transcription_type != TranscriptionType.RETRY_FAILED
    
    @property
    def cost_display(self) -> str:
        """Get formatted cost for display"""
        if not self.should_charge_user:
            return "Free"
        return f"${self.cost_usd:.4f}" if self.cost_usd else "Free"
```

### Smart Billing Service
```python
# packages/core-logic/src/coaching_assistant/services/smart_billing.py

from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models.user import User
from ..models.session import Session as SessionModel, SessionStatus
from ..models.usage_log import UsageLog, TranscriptionType
from ..services.usage_tracking import UsageTrackingService

class SmartBillingService:
    """Service for intelligent transcription billing decisions"""
    
    def __init__(self, db: Session):
        self.db = db
        self.usage_service = UsageTrackingService(db)
    
    def classify_transcription_request(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Classify transcription request and determine billing approach"""
        
        session = self.db.query(SessionModel).filter(
            and_(SessionModel.id == session_id, SessionModel.user_id == user_id)
        ).first()
        
        if not session:
            raise ValueError("Session not found")
        
        # Check existing usage logs for this session
        existing_logs = self.db.query(UsageLog).filter(
            UsageLog.session_id == session_id
        ).order_by(UsageLog.created_at.desc()).all()
        
        classification = {
            "session_id": session_id,
            "session_status": session.status.value,
            "previous_attempts": len(existing_logs),
            "transcription_type": None,
            "is_billable": True,
            "billing_reason": None,
            "cost_estimate": None,
            "requires_confirmation": False,
            "provider_options": self._get_provider_options(),
            "original_transcription": None
        }
        
        # Find original transcription for reference
        original_log = next((log for log in existing_logs if log.transcription_type == TranscriptionType.ORIGINAL), None)
        if original_log:
            classification["original_transcription"] = {
                "duration_minutes": original_log.duration_minutes,
                "cost_usd": float(original_log.cost_usd) if original_log.cost_usd else 0.0,
                "stt_provider": original_log.stt_provider,
                "created_at": original_log.created_at.isoformat()
            }
        
        if session.status == SessionStatus.FAILED:
            # Failed session - retry should be free
            classification.update({
                "transcription_type": TranscriptionType.RETRY_FAILED,
                "is_billable": False,
                "billing_reason": "retry_after_failure",
                "cost_estimate": 0.0,
                "requires_confirmation": False,
                "message": "Free retry available for failed transcription"
            })
            
        elif session.status == SessionStatus.COMPLETED:
            # Successful session - re-transcription is chargeable
            estimated_cost = self._estimate_retranscription_cost(session)
            classification.update({
                "transcription_type": TranscriptionType.RETRY_SUCCESS,
                "is_billable": True,
                "billing_reason": "retranscription_service",
                "cost_estimate": estimated_cost,
                "requires_confirmation": True,
                "message": f"Re-transcription will cost approximately ${estimated_cost:.4f}"
            })
            
        else:
            # Session in progress or other state
            raise ValueError(f"Cannot transcribe session with status: {session.status.value}")
        
        return classification
    
    def _estimate_retranscription_cost(self, session: SessionModel, stt_provider: Optional[str] = None) -> float:
        """Estimate cost for re-transcribing a session with specific provider"""
        
        # Use provided provider or session's current provider
        provider = stt_provider or session.stt_provider
        
        # Get duration from session or existing usage log
        duration_minutes = 0
        if session.duration_seconds:
            duration_minutes = session.duration_seconds / 60
        else:
            # Try to get from existing usage log
            existing_log = self.db.query(UsageLog).filter(
                UsageLog.session_id == session.id
            ).first()
            
            if existing_log:
                duration_minutes = existing_log.duration_minutes
            else:
                # Fallback estimation - assume 5 minutes average
                duration_minutes = 5
        
        # Provider-specific pricing (as of August 2025)
        pricing = {
            "google": 0.006,      # $0.006 per minute
            "assemblyai": 0.00065  # $0.00065 per minute
        }
        
        rate = pricing.get(provider, 0.006)  # Default to Google pricing
        estimated_cost = duration_minutes * rate
        
        # Add 10% buffer for estimation accuracy
        return estimated_cost * 1.1
    
    def _get_provider_options(self) -> List[Dict[str, Any]]:
        """Get available STT provider options with pricing"""
        return [
            {
                "provider": "google",
                "display_name": "Google Speech-to-Text",
                "rate_per_minute": 0.006,
                "features": ["High accuracy", "Diarization support", "Multiple languages"],
                "recommended": True
            },
            {
                "provider": "assemblyai",
                "display_name": "AssemblyAI",
                "rate_per_minute": 0.00065,
                "features": ["AI-powered", "Automatic speaker roles", "Fast processing"],
                "recommended": False
            }
        ]
    
    def create_usage_log_for_transcription(
        self, 
        session: SessionModel, 
        result: 'TranscriptionResult',
        transcription_type: TranscriptionType,
        billing_reason: str
    ) -> UsageLog:
        """Create usage log entry with proper billing classification"""
        
        # Find parent log if this is a retry/re-transcription
        parent_log = None
        if transcription_type != TranscriptionType.ORIGINAL:
            parent_log = self.db.query(UsageLog).filter(
                UsageLog.session_id == session.id
            ).order_by(UsageLog.created_at.asc()).first()
        
        # Determine if billable
        is_billable = transcription_type != TranscriptionType.RETRY_FAILED
        
        # Calculate actual cost
        actual_cost = result.cost_usd if is_billable else 0.0
        
        # Create detailed cost breakdown
        cost_breakdown = {
            "provider": session.stt_provider,
            "duration_seconds": result.total_duration_sec,
            "duration_minutes": result.total_duration_sec / 60,
            "base_rate_per_minute": actual_cost / (result.total_duration_sec / 60) if result.total_duration_sec > 0 else 0,
            "transcription_type": transcription_type.value,
            "is_billable": is_billable,
            "calculation_time": datetime.utcnow().isoformat()
        }
        
        usage_log = UsageLog(
            user_id=session.user_id,
            session_id=session.id,
            client_id=getattr(session, 'client_id', None),
            
            duration_minutes=int(result.total_duration_sec / 60),
            duration_seconds=int(result.total_duration_sec),
            cost_usd=actual_cost,
            stt_provider=session.stt_provider,
            
            transcription_type=transcription_type,
            parent_log_id=parent_log.id if parent_log else None,
            
            is_billable=is_billable,
            billing_reason=billing_reason,
            cost_breakdown=cost_breakdown,
            
            transcription_started_at=session.updated_at,
            transcription_completed_at=datetime.utcnow(),
            
            language=session.language,
            provider_metadata=result.provider_metadata or {}
        )
        
        self.db.add(usage_log)
        self.db.flush()
        
        # Update user usage counters (only for billable transcriptions)
        if is_billable:
            user = self.db.query(User).filter(User.id == session.user_id).first()
            self.usage_service._update_user_usage_counters(user, usage_log)
        
        # Update monthly analytics
        self.usage_service._update_monthly_analytics(session.user_id, usage_log)
        
        self.db.commit()
        
        logger.info(
            f"Created usage log: session={session.id}, type={transcription_type.value}, "
            f"billable={is_billable}, cost=${usage_log.cost_usd}"
        )
        
        return usage_log
    
    def get_session_billing_history(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Get comprehensive billing history for a session"""
        
        session = self.db.query(SessionModel).filter(
            and_(SessionModel.id == session_id, SessionModel.user_id == user_id)
        ).first()
        
        if not session:
            raise ValueError("Session not found")
        
        # Get all usage logs for this session
        usage_logs = self.db.query(UsageLog).filter(
            UsageLog.session_id == session_id
        ).order_by(UsageLog.created_at.asc()).all()
        
        # Calculate billing summary
        total_cost = sum(float(log.cost_usd or 0) for log in usage_logs if log.is_billable)
        billable_attempts = len([log for log in usage_logs if log.is_billable])
        free_retries = len([log for log in usage_logs if not log.is_billable])
        
        return {
            "session_id": session_id,
            "session_status": session.status.value,
            "session_title": session.title,
            "billing_summary": {
                "total_cost_usd": total_cost,
                "billable_attempts": billable_attempts,
                "free_retries": free_retries,
                "total_attempts": len(usage_logs)
            },
            "transcription_history": [
                {
                    "attempt_number": idx + 1,
                    "id": str(log.id),
                    "transcription_type": log.transcription_type.value,
                    "cost_usd": float(log.cost_usd or 0),
                    "is_billable": log.is_billable,
                    "billing_reason": log.billing_reason,
                    "billing_description": log.billing_description,
                    "created_at": log.created_at.isoformat(),
                    "duration_minutes": log.duration_minutes,
                    "stt_provider": log.stt_provider,
                    "cost_breakdown": log.cost_breakdown
                }
                for idx, log in enumerate(usage_logs)
            ],
            "next_action_info": self._get_next_action_info(session, usage_logs)
        }
    
    def _get_next_action_info(self, session: SessionModel, usage_logs: List[UsageLog]) -> Dict[str, Any]:
        """Get information about what actions are available next"""
        
        if session.status == SessionStatus.FAILED:
            return {
                "action": "retry",
                "cost": 0.0,
                "description": "Free retry available for failed transcription",
                "button_text": "Retry (Free)"
            }
        elif session.status == SessionStatus.COMPLETED:
            estimated_cost = self._estimate_retranscription_cost(session)
            return {
                "action": "retranscribe",
                "cost": estimated_cost,
                "description": f"Re-transcribe this session for ${estimated_cost:.4f}",
                "button_text": "Re-transcribe"
            }
        else:
            return {
                "action": "none",
                "description": "No actions available while transcription is in progress"
            }
```

### Enhanced API Endpoints
```python
# packages/core-logic/src/coaching_assistant/api/sessions.py (Enhanced)

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..dependencies import get_db, get_current_user_dependency
from ..models.user import User
from ..services.smart_billing import SmartBillingService
from ..tasks.transcription_tasks import transcribe_audio

@router.post("/{session_id}/retranscribe")
async def retranscribe_session(
    session_id: str,
    request: RetranscriptionRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Re-transcribe a successful session with cost confirmation"""
    
    billing_service = SmartBillingService(db)
    
    # Classify the transcription request
    try:
        classification = billing_service.classify_transcription_request(session_id, str(current_user.id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Must be a successful session for re-transcription
    if classification["transcription_type"] != TranscriptionType.RETRY_SUCCESS:
        raise HTTPException(
            status_code=400,
            detail="Re-transcription is only available for completed sessions. Use /retry-transcription for failed sessions."
        )
    
    # If user hasn't confirmed cost, return estimate
    if not request.confirm_cost:
        return {
            "action": "cost_confirmation_required",
            "message": "Please confirm the cost for re-transcription",
            "cost_estimate": classification["cost_estimate"],
            "billing_reason": classification["billing_reason"],
            "original_transcription": classification["original_transcription"],
            "provider_options": classification["provider_options"],
            "requires_confirmation": True
        }
    
    # Validate user can afford the re-transcription (plan limits)
    from ..services.plan_service import PlanService
    plan_service = PlanService(db)
    validation = plan_service.validate_plan_limits(current_user, "transcribe")
    
    if not validation["allowed"]:
        raise HTTPException(
            status_code=402,
            detail=f"Re-transcription would exceed plan limits: {validation['message']}",
            headers={"X-Suggested-Plan": validation.get("upgrade_suggestion", {}).get("suggested_plan", "")}
        )
    
    session = db.query(SessionModel).filter(
        and_(SessionModel.id == session_id, SessionModel.user_id == current_user.id)
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Create new transcription task with billing classification
    selected_provider = request.stt_provider or session.stt_provider
    task_result = transcribe_audio.delay(
        session_id=session_id,
        gcs_uri=session.gcs_audio_path,
        language=session.language,
        enable_diarization=getattr(request, 'enable_diarization', True),
        stt_provider=selected_provider,
        transcription_type="retry_success"  # Pass the classification
    )
    
    return {
        "message": "Re-transcription started successfully",
        "task_id": task_result.id,
        "session_id": session_id,
        "estimated_cost": classification["cost_estimate"],
        "selected_provider": selected_provider,
        "transcription_type": "re-transcription",
        "is_billable": True,
        "billing_reason": "retranscription_service"
    }

@router.get("/{session_id}/billing")
async def get_session_billing_info(
    session_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get detailed billing information for a session"""
    
    billing_service = SmartBillingService(db)
    
    try:
        billing_info = billing_service.get_session_billing_history(session_id, str(current_user.id))
        return billing_info
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{session_id}/retranscribe/estimate")
async def get_retranscription_estimate(
    session_id: str,
    stt_provider: Optional[str] = Query(None, description="STT provider for estimation"),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get cost estimate for re-transcribing a session with specific provider"""
    
    billing_service = SmartBillingService(db)
    
    try:
        classification = billing_service.classify_transcription_request(session_id, str(current_user.id))
        
        if classification["transcription_type"] != TranscriptionType.RETRY_SUCCESS:
            raise HTTPException(
                status_code=400,
                detail="Cost estimation only available for completed sessions"
            )
        
        # Get estimate for specific provider if requested
        if stt_provider:
            session = db.query(SessionModel).filter(
                and_(SessionModel.id == session_id, SessionModel.user_id == current_user.id)
            ).first()
            
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            provider_estimate = billing_service._estimate_retranscription_cost(session, stt_provider)
            classification["provider_specific_estimate"] = provider_estimate
        
        return {
            "session_id": session_id,
            "cost_estimation": {
                "default_estimate": classification["cost_estimate"],
                "provider_specific": classification.get("provider_specific_estimate"),
                "provider_options": classification["provider_options"]
            },
            "original_transcription": classification["original_transcription"],
            "billing_breakdown": {
                "base_cost": classification["cost_estimate"],
                "taxes": 0.0,  # TODO: Add tax calculation if needed
                "total_cost": classification["cost_estimate"]
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Request models
class RetranscriptionRequest(BaseModel):
    """Request model for re-transcription"""
    confirm_cost: bool = Field(..., description="User must confirm they understand the cost")
    enable_diarization: bool = Field(True, description="Enable speaker diarization")
    stt_provider: Optional[str] = Field(None, description="Specific STT provider to use")
```

## 🧪 Test Scenarios

### Billing Logic Tests
```python
def test_failed_session_retry_free():
    """Test failed session retry is classified as free"""
    user = create_test_user()
    session = create_failed_session(db, user.id)
    
    billing_service = SmartBillingService(db)
    classification = billing_service.classify_transcription_request(str(session.id), str(user.id))
    
    assert classification["transcription_type"] == TranscriptionType.RETRY_FAILED
    assert classification["is_billable"] == False
    assert classification["cost_estimate"] == 0.0
    assert classification["requires_confirmation"] == False

def test_successful_session_retranscription_charged():
    """Test successful session re-transcription is charged"""
    user = create_test_user()
    session = create_completed_session(db, user.id)
    original_usage = create_usage_log(db, session.id, cost_usd=0.05)
    
    billing_service = SmartBillingService(db)
    classification = billing_service.classify_transcription_request(str(session.id), str(user.id))
    
    assert classification["transcription_type"] == TranscriptionType.RETRY_SUCCESS
    assert classification["is_billable"] == True
    assert classification["cost_estimate"] > 0
    assert classification["requires_confirmation"] == True

def test_cost_estimation_accuracy():
    """Test transcription cost estimation accuracy"""
    user = create_test_user()
    session = create_completed_session(db, user.id, duration_seconds=300)  # 5 minutes
    
    billing_service = SmartBillingService(db)
    
    # Test Google STT estimation
    google_cost = billing_service._estimate_retranscription_cost(session, "google")
    expected_google = 5 * 0.006 * 1.1  # 5 min * rate * buffer
    assert abs(google_cost - expected_google) < 0.001
    
    # Test AssemblyAI estimation
    assemblyai_cost = billing_service._estimate_retranscription_cost(session, "assemblyai")
    expected_assemblyai = 5 * 0.00065 * 1.1  # 5 min * rate * buffer
    assert abs(assemblyai_cost - expected_assemblyai) < 0.001

def test_usage_log_billing_classification():
    """Test usage log creation respects billing classification"""
    user = create_test_user()
    session = create_completed_session(db, user.id)
    result = create_mock_transcription_result(duration_sec=180, cost_usd=0.05)
    
    billing_service = SmartBillingService(db)
    
    # Test retry (free)
    retry_log = billing_service.create_usage_log_for_transcription(
        session=session,
        result=result,
        transcription_type=TranscriptionType.RETRY_FAILED,
        billing_reason="failure_retry_no_charge"
    )
    
    assert retry_log.is_billable == False
    assert retry_log.cost_usd == 0
    assert retry_log.billing_reason == "failure_retry_no_charge"
    assert retry_log.cost_breakdown["is_billable"] == False
    
    # Test re-transcription (charged)
    retrans_log = billing_service.create_usage_log_for_transcription(
        session=session,
        result=result,
        transcription_type=TranscriptionType.RETRY_SUCCESS,
        billing_reason="retranscription_service"
    )
    
    assert retrans_log.is_billable == True
    assert retrans_log.cost_usd == 0.05
    assert retrans_log.billing_reason == "retranscription_service"
    assert retrans_log.parent_log_id == retry_log.id  # Links to parent
```

### Integration Tests
```python
def test_retry_vs_retranscribe_api_flow():
    """Test complete retry vs retranscribe API workflow"""
    user = create_test_user()
    
    # Test failed session retry (free)
    failed_session = create_failed_session(db, user.id)
    
    with authenticate_as(user):
        # Should be able to retry for free
        retry_response = client.post(f"/api/sessions/{failed_session.id}/retry-transcription")
        assert retry_response.status_code == 200
        
        retry_data = retry_response.json()
        assert "Free retry" in retry_data["message"]
        assert retry_data.get("cost_estimate", 0) == 0
    
    # Test successful session re-transcription (charged)
    success_session = create_completed_session(db, user.id)
    
    with authenticate_as(user):
        # First call without confirmation should return estimate
        retranscribe_response = client.post(
            f"/api/sessions/{success_session.id}/retranscribe",
            json={"confirm_cost": False}
        )
        assert retranscribe_response.status_code == 200
        
        estimate_data = retranscribe_response.json()
        assert estimate_data["requires_confirmation"] == True
        assert estimate_data["cost_estimate"] > 0
        
        # Second call with confirmation should start transcription
        confirmed_response = client.post(
            f"/api/sessions/{success_session.id}/retranscribe",
            json={"confirm_cost": True}
        )
        assert confirmed_response.status_code == 200
        
        confirmed_data = confirmed_response.json()
        assert "Re-transcription started" in confirmed_data["message"]
        assert confirmed_data["is_billable"] == True

def test_billing_history_endpoint():
    """Test session billing history endpoint"""
    user = create_test_user()
    session = create_completed_session(db, user.id)
    
    # Create multiple usage logs (original + retranscription)
    billing_service = SmartBillingService(db)
    result1 = create_mock_transcription_result(cost_usd=0.05)
    result2 = create_mock_transcription_result(cost_usd=0.06)
    
    # Original transcription
    original_log = billing_service.create_usage_log_for_transcription(
        session=session,
        result=result1,
        transcription_type=TranscriptionType.ORIGINAL,
        billing_reason="original_transcription"
    )
    
    # Re-transcription
    retrans_log = billing_service.create_usage_log_for_transcription(
        session=session,
        result=result2,
        transcription_type=TranscriptionType.RETRY_SUCCESS,
        billing_reason="retranscription_service"
    )
    
    with authenticate_as(user):
        billing_response = client.get(f"/api/sessions/{session.id}/billing")
        assert billing_response.status_code == 200
        
        billing_data = billing_response.json()
        assert billing_data["billing_summary"]["total_cost_usd"] == 0.11  # 0.05 + 0.06
        assert billing_data["billing_summary"]["billable_attempts"] == 2
        assert billing_data["billing_summary"]["free_retries"] == 0
        assert len(billing_data["transcription_history"]) == 2
```

## 📊 Success Metrics

### Financial Accuracy
- **Billing Classification**: 100% correct classification of retry vs re-transcription
- **Cost Accuracy**: 0% billing errors for failure retries (should always be $0)  
- **Revenue Capture**: 100% of legitimate re-transcription requests properly charged
- **Cost Estimation**: Within 5% accuracy of actual transcription costs

### User Experience  
- **Billing Transparency**: 95% user satisfaction with billing clarity
- **Support Reduction**: 80% reduction in billing-related support tickets
- **User Trust**: Clear cost estimates increase re-transcription usage by 25%
- **Confusion Reduction**: 90% reduction in "why was I charged?" inquiries

### Technical Performance
- **Classification Speed**: <50ms for billing classification API calls
- **Cost Estimation**: <100ms for re-transcription cost estimates  
- **Usage Tracking**: 100% accuracy in usage log creation and classification
- **API Response Time**: <200ms for billing history endpoints

## 📋 Definition of Done

- [ ] **Billing Classification**: SmartBillingService correctly classifies all scenarios
- [ ] **Usage Log Enhancement**: UsageLog model includes transcription type and billing fields
- [ ] **API Endpoints**: Enhanced retry and new retranscribe endpoints with cost confirmation
- [ ] **User Interface**: Clear distinction between retry (free) and re-transcribe (charged) actions
- [ ] **Cost Estimation**: Accurate cost estimation for re-transcription requests  
- [ ] **Usage Tracking**: Proper integration with usage analytics system (US001)
- [ ] **Plan Integration**: Re-transcription counts against plan limits (US002)
- [ ] **Provider Support**: Cost estimation works for both Google STT and AssemblyAI
- [ ] **Unit Tests**: >90% coverage for billing logic and classification
- [ ] **Integration Tests**: End-to-end billing scenarios verified
- [ ] **User Documentation**: Clear explanation of billing policy for retries vs re-transcription
- [ ] **Admin Tools**: Billing analytics distinguish between transcription types

## 🔄 Dependencies & Risks

### Dependencies  
- ✅ US001 (Usage Analytics Foundation) - Required for usage log classification
- ✅ US002 (Plan Tiers) - Required for plan limit validation
- ✅ Current transcription system - Base functionality for retry/re-transcription
- ⏳ Payment processing integration - For handling charges
- ⏳ User experience design - For cost confirmation flows

### Risks & Mitigations
- **Risk**: Users confused by retry vs re-transcription distinction
  - **Mitigation**: Clear UI labels, help text, confirmation dialogs, user education
- **Risk**: Cost estimation inaccuracy leads to user complaints  
  - **Mitigation**: Conservative estimates, clear "estimate" labeling, monitoring and adjustment
- **Risk**: Billing logic complexity introduces bugs
  - **Mitigation**: Comprehensive test coverage, gradual rollout, monitoring and alerts

## 📞 Stakeholders

**Product Owner**: Business/Finance Team, Customer Success  
**Technical Lead**: Backend Engineering, Billing Systems Integration  
**Reviewers**: Finance (Revenue), Legal (Terms of Service), UX (User Experience)  
**QA Focus**: Billing accuracy, User experience, Financial compliance, Edge cases