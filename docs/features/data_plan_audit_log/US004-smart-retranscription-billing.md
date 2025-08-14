# US004: Smart Re-transcription Billing

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

### Business Impact
- **Customer Satisfaction**: Users charged for system failures leads to support complaints
- **Revenue Accuracy**: Missing revenue from legitimate re-transcription requests
- **Support Overhead**: Manual billing adjustments for failure-related charges
- **Platform Trust**: Unclear billing practices reduce user confidence

### Value Delivered
- **Fair Billing**: Free retries for failures, appropriate charges for re-transcription services
- **Revenue Optimization**: Capture legitimate re-transcription revenue without penalizing users
- **User Transparency**: Clear distinction between retry and re-transcription in billing
- **Automated Billing**: No manual intervention needed for billing classification

## 🎯 Acceptance Criteria

### Transcription Type Classification
1. **Failure Retry Logic**
   - [ ] Failed transcriptions can be retried without additional charge
   - [ ] System automatically identifies retry scenarios (session status = FAILED)
   - [ ] Retries preserve original session and don't create new usage logs
   - [ ] Multiple retries of same failed session remain free

2. **Re-transcription Logic**
   - [ ] Successfully completed sessions can be re-transcribed (new transcription)
   - [ ] Re-transcription creates new usage log entry with appropriate billing
   - [ ] Re-transcription preserves original transcription data
   - [ ] Clear user intent confirmation for charged re-transcription

3. **Usage Tracking Integration**
   - [ ] Usage logs include transcription_type field (original, retry_failed, retry_success)
   - [ ] Billing calculations respect transcription type classification
   - [ ] User.usage_minutes only incremented for chargeable transcriptions
   - [ ] Analytics distinguish between different transcription types

### API Enhancements
4. **Enhanced Retry Endpoint**
   - [ ] Existing `/retry-transcription` endpoint remains free for failures
   - [ ] Enhanced logic validates session status before allowing retry
   - [ ] Clear error messages for invalid retry attempts

5. **New Re-transcription Endpoint**
   - [ ] New `/retranscribe` endpoint for intentional re-transcription of successful sessions
   - [ ] User confirmation required with cost estimate
   - [ ] Provider selection support for re-transcription
   - [ ] Progress tracking for re-transcription requests

### User Interface Updates
6. **Clear Action Distinction**
   - [ ] Failed sessions show "Retry" button (free)
   - [ ] Successful sessions show "Re-transcribe" button (charged) 
   - [ ] Cost estimates shown before re-transcription confirmation
   - [ ] Usage history clearly labels transcription types

## 🏗️ Technical Implementation

### Enhanced Usage Log Classification
```python
# packages/core-logic/src/coaching_assistant/models/usage_log.py (Updated from US001)

class TranscriptionType(enum.Enum):
    """Classification of transcription types for billing"""
    ORIGINAL = "original"          # First transcription attempt
    RETRY_FAILED = "retry_failed"  # Retry after failure (free)
    RETRY_SUCCESS = "retry_success" # Re-transcription of successful session (charged)

class UsageLog(BaseModel):
    """Enhanced usage log with transcription type tracking"""
    
    # ... existing fields from US001 ...
    
    transcription_type = Column(Enum(TranscriptionType), nullable=False)
    parent_usage_log_id = Column(UUID(as_uuid=True), ForeignKey("usage_logs.id"), nullable=True)
    
    # Billing metadata
    is_billable = Column(Boolean, nullable=False, default=True)
    billing_reason = Column(String(100), nullable=True)  # "original", "retry_free", "retranscription_requested"
    
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
```

### Smart Billing Service
```python
# packages/core-logic/src/coaching_assistant/services/billing_service.py

class TranscriptionBillingService:
    """Service for intelligent transcription billing decisions"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def classify_transcription_request(self, session_id: UUID, user_id: UUID) -> Dict:
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
            "requires_confirmation": False
        }
        
        if session.status == SessionStatus.FAILED:
            # Failed session - retry should be free
            classification.update({
                "transcription_type": TranscriptionType.RETRY_FAILED,
                "is_billable": False,
                "billing_reason": "retry_after_failure",
                "cost_estimate": 0.0,
                "requires_confirmation": False
            })
            
        elif session.status == SessionStatus.COMPLETED:
            # Successful session - re-transcription is chargeable
            estimated_cost = self._estimate_retranscription_cost(session)
            classification.update({
                "transcription_type": TranscriptionType.RETRY_SUCCESS,
                "is_billable": True,
                "billing_reason": "retranscription_service",
                "cost_estimate": estimated_cost,
                "requires_confirmation": True
            })
            
        else:
            # Session in progress or other state
            raise ValueError(f"Cannot transcribe session with status: {session.status.value}")
        
        return classification
    
    def _estimate_retranscription_cost(self, session: SessionModel) -> float:
        """Estimate cost for re-transcribing a session"""
        
        if not session.duration_seconds:
            # Use existing usage log for estimation
            existing_log = self.db.query(UsageLog).filter(
                UsageLog.session_id == session.id
            ).first()
            
            if existing_log and existing_log.cost_usd:
                return float(existing_log.cost_usd)
            
            # Fallback estimation based on audio length
            duration_minutes = session.duration_seconds / 60 if session.duration_seconds else 5
            return duration_minutes * 0.006  # Google STT v2 pricing
        
        # Estimate based on session duration
        duration_minutes = session.duration_seconds / 60
        
        # Cost varies by provider
        if session.stt_provider == "assemblyai":
            return duration_minutes * 0.00065  # AssemblyAI pricing
        else:
            return duration_minutes * 0.006  # Google STT v2 pricing
    
    def create_usage_log_for_transcription(
        self, 
        session: SessionModel, 
        result: TranscriptionResult,
        transcription_type: TranscriptionType,
        billing_reason: str
    ) -> UsageLog:
        """Create usage log entry with proper billing classification"""
        
        # Find parent usage log if this is a retry/re-transcription
        parent_log = None
        if transcription_type != TranscriptionType.ORIGINAL:
            parent_log = self.db.query(UsageLog).filter(
                UsageLog.session_id == session.id
            ).order_by(UsageLog.created_at.asc()).first()
        
        # Determine if billable
        is_billable = transcription_type != TranscriptionType.RETRY_FAILED
        
        usage_log = UsageLog(
            user_id=session.user_id,
            session_id=session.id,
            client_id=getattr(session, 'client_id', None),
            
            duration_minutes=int(result.total_duration_sec / 60),
            duration_seconds=int(result.total_duration_sec),
            cost_usd=result.cost_usd if is_billable else 0.0,
            stt_provider=session.stt_provider,
            
            transcription_type=transcription_type,
            parent_usage_log_id=parent_log.id if parent_log else None,
            
            is_billable=is_billable,
            billing_reason=billing_reason,
            
            transcription_started_at=session.updated_at,
            transcription_completed_at=datetime.utcnow(),
            
            language=session.language,
            provider_metadata=result.provider_metadata
        )
        
        self.db.add(usage_log)
        self.db.commit()
        
        # Update user usage minutes only for billable transcriptions
        if is_billable:
            user = self.db.query(User).filter(User.id == session.user_id).first()
            user.add_usage(int(result.total_duration_sec / 60))
            self.db.commit()
        
        logger.info(
            f"Created usage log: session={session.id}, type={transcription_type.value}, "
            f"billable={is_billable}, cost=${usage_log.cost_usd}"
        )
        
        return usage_log
```

### Enhanced API Endpoints
```python
# packages/core-logic/src/coaching_assistant/api/sessions.py (Enhanced)

@router.post("/{session_id}/retranscribe")
async def retranscribe_session(
    session_id: UUID,
    request: RetranscriptionRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Re-transcribe a successful session with cost confirmation"""
    
    billing_service = TranscriptionBillingService(db)
    
    # Classify the transcription request
    try:
        classification = billing_service.classify_transcription_request(session_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Must be a successful session for re-transcription
    if classification["transcription_type"] != TranscriptionType.RETRY_SUCCESS:
        raise HTTPException(
            status_code=400,
            detail="Re-transcription is only available for completed sessions. Use /retry-transcription for failed sessions."
        )
    
    # Verify user confirmed the cost
    if not request.confirm_cost:
        return {
            "message": "Cost confirmation required for re-transcription",
            "cost_estimate": classification["cost_estimate"],
            "billing_reason": classification["billing_reason"],
            "requires_confirmation": True
        }
    
    # Check user's usage limits
    estimated_minutes = classification["cost_estimate"] / 0.006 * 60  # Rough estimate
    if not current_user.can_create_session(int(estimated_minutes)):
        raise HTTPException(
            status_code=402,
            detail="Re-transcription would exceed your plan limits"
        )
    
    session = db.query(SessionModel).filter(
        and_(SessionModel.id == session_id, SessionModel.user_id == current_user.id)
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Create new transcription task
    task_result = transcribe_audio.delay(
        session_id=str(session_id),
        gcs_uri=session.gcs_audio_path,
        language=session.language,
        enable_diarization=getattr(request, 'enable_diarization', True),
        transcription_type="retry_success"  # Pass the classification
    )
    
    return {
        "message": "Re-transcription started successfully",
        "task_id": task_result.id,
        "session_id": str(session_id),
        "estimated_cost": classification["cost_estimate"],
        "transcription_type": "re-transcription"
    }

@router.get("/{session_id}/billing-info")
async def get_session_billing_info(
    session_id: UUID,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get billing information for a session"""
    
    session = db.query(SessionModel).filter(
        and_(SessionModel.id == session_id, SessionModel.user_id == current_user.id)
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get all usage logs for this session
    usage_logs = db.query(UsageLog).filter(
        UsageLog.session_id == session_id
    ).order_by(UsageLog.created_at.asc()).all()
    
    # Calculate billing summary
    total_cost = sum(float(log.cost_usd or 0) for log in usage_logs if log.is_billable)
    billable_attempts = len([log for log in usage_logs if log.is_billable])
    free_retries = len([log for log in usage_logs if not log.is_billable])
    
    return {
        "session_id": str(session_id),
        "session_status": session.status.value,
        "billing_summary": {
            "total_cost": total_cost,
            "billable_attempts": billable_attempts,
            "free_retries": free_retries,
            "total_attempts": len(usage_logs)
        },
        "transcription_history": [
            {
                "attempt_number": idx + 1,
                "transcription_type": log.transcription_type.value,
                "cost": float(log.cost_usd or 0),
                "is_billable": log.is_billable,
                "billing_reason": log.billing_reason,
                "created_at": log.created_at.isoformat(),
                "duration_minutes": log.duration_minutes,
                "stt_provider": log.stt_provider
            }
            for idx, log in enumerate(usage_logs)
        ]
    }

# Request models
class RetranscriptionRequest(BaseModel):
    """Request model for re-transcription"""
    confirm_cost: bool = Field(..., description="User must confirm they understand the cost")
    enable_diarization: bool = Field(True, description="Enable speaker diarization")
    stt_provider: Optional[str] = Field(None, description="Specific STT provider to use")
```

### Enhanced Transcription Task Integration
```python
# packages/core-logic/src/coaching_assistant/tasks/transcription_tasks.py (Enhanced)

@celery_app.task(bind=True, base=TranscriptionTask)
def transcribe_audio(
    self,
    session_id: str,
    gcs_uri: str,
    language: str = "zh-TW",
    enable_diarization: bool = True,
    original_filename: str = None,
    transcription_type: str = "original"  # NEW: Pass transcription type
) -> dict:
    """Enhanced transcription task with billing classification"""
    
    session_uuid = UUID(session_id)
    start_time = datetime.utcnow()
    
    # Convert string to enum
    trans_type = TranscriptionType(transcription_type)
    
    with get_db_session() as db:
        session = db.query(SessionModel).filter(
            SessionModel.id == session_uuid
        ).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        billing_service = TranscriptionBillingService(db)
        
        # ... existing transcription logic ...
        
        try:
            # Perform transcription (existing logic)
            result = stt_provider.transcribe(...)
            
            # ... save segments and metadata ...
            
            # NEW: Create usage log with proper billing classification
            billing_reason = _determine_billing_reason(trans_type, session.status)
            
            usage_log = billing_service.create_usage_log_for_transcription(
                session=session,
                result=result,
                transcription_type=trans_type,
                billing_reason=billing_reason
            )
            
            # Mark session as completed
            session.mark_completed(
                duration_seconds=int(result.total_duration_sec),
                cost_usd=str(usage_log.cost_usd)  # Use usage log cost (may be 0 for retries)
            )
            
            logger.info(
                f"Session {session_id} completed: type={trans_type.value}, "
                f"billable={usage_log.is_billable}, cost=${usage_log.cost_usd}"
            )
            
            return {
                "session_id": session_id,
                "status": "completed",
                "transcription_type": trans_type.value,
                "is_billable": usage_log.is_billable,
                "cost_usd": float(usage_log.cost_usd),
                "billing_description": usage_log.billing_description,
                # ... other existing return fields ...
            }
            
        except Exception as exc:
            # Error handling remains the same
            # but no usage log created for failures
            logger.error(f"Transcription failed: {exc}")
            raise

def _determine_billing_reason(transcription_type: TranscriptionType, session_status: SessionStatus) -> str:
    """Determine billing reason based on transcription context"""
    
    if transcription_type == TranscriptionType.ORIGINAL:
        return "original_transcription"
    elif transcription_type == TranscriptionType.RETRY_FAILED:
        return "failure_retry_no_charge"
    elif transcription_type == TranscriptionType.RETRY_SUCCESS:
        return "retranscription_service"
    else:
        return "unknown_transcription_type"
```

## 🎨 Frontend Implementation

### Enhanced Session Actions Component
```tsx
// apps/web/app/dashboard/sessions/SessionActions.tsx

interface SessionActionsProps {
  session: {
    id: string;
    status: 'completed' | 'failed' | 'processing';
    duration_minutes?: number;
    cost_usd?: number;
  };
}

export function SessionActions({ session }: SessionActionsProps) {
  const [showRetranscribeModal, setShowRetranscribeModal] = useState(false);
  const [costEstimate, setCostEstimate] = useState<number | null>(null);
  
  const handleRetryClick = async () => {
    // Free retry for failed sessions
    try {
      await fetch(`/api/v1/sessions/${session.id}/retry-transcription`, {
        method: 'POST'
      });
      
      toast.success('Retry started - no additional charge');
      
    } catch (error) {
      toast.error('Failed to start retry');
    }
  };
  
  const handleRetranscribeClick = async () => {
    // Get cost estimate first
    try {
      const response = await fetch(`/api/v1/sessions/${session.id}/retranscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirm_cost: false })
      });
      
      const data = await response.json();
      setCostEstimate(data.cost_estimate);
      setShowRetranscribeModal(true);
      
    } catch (error) {
      toast.error('Failed to get cost estimate');
    }
  };
  
  const confirmRetranscribe = async () => {
    try {
      await fetch(`/api/v1/sessions/${session.id}/retranscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirm_cost: true })
      });
      
      toast.success('Re-transcription started');
      setShowRetranscribeModal(false);
      
    } catch (error) {
      toast.error('Failed to start re-transcription');
    }
  };
  
  return (
    <div className="flex gap-2">
      {session.status === 'failed' && (
        <button
          onClick={handleRetryClick}
          className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
        >
          🔄 Retry (Free)
        </button>
      )}
      
      {session.status === 'completed' && (
        <button
          onClick={handleRetranscribeClick}
          className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
        >
          🔄 Re-transcribe
        </button>
      )}
      
      {showRetranscribeModal && (
        <RetranscribeConfirmationModal
          costEstimate={costEstimate}
          onConfirm={confirmRetranscribe}
          onCancel={() => setShowRetranscribeModal(false)}
        />
      )}
    </div>
  );
}

function RetranscribeConfirmationModal({ costEstimate, onConfirm, onCancel }: {
  costEstimate: number;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white p-6 rounded-lg max-w-md">
        <h3 className="text-lg font-semibold mb-4">Confirm Re-transcription</h3>
        
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
          <p className="text-sm">
            This will create a new transcription of your audio file. 
            Your original transcription will be preserved.
          </p>
        </div>
        
        <div className="mb-6">
          <div className="flex justify-between items-center">
            <span className="font-medium">Estimated cost:</span>
            <span className="text-lg font-bold">${costEstimate?.toFixed(4)}</span>
          </div>
        </div>
        
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          >
            Confirm & Start
          </button>
        </div>
      </div>
    </div>
  );
}
```

## 🧪 Test Scenarios

### Billing Logic Tests
```python
def test_failed_session_retry_free():
    """Test failed session retry is free"""
    session = create_failed_session(db, user_id)
    
    billing_service = TranscriptionBillingService(db)
    classification = billing_service.classify_transcription_request(session.id, user_id)
    
    assert classification["transcription_type"] == TranscriptionType.RETRY_FAILED
    assert classification["is_billable"] == False
    assert classification["cost_estimate"] == 0.0
    
def test_successful_session_retranscription_charged():
    """Test successful session re-transcription is charged"""
    session = create_completed_session(db, user_id)
    original_usage = create_usage_log(db, session.id, cost_usd=0.05)
    
    billing_service = TranscriptionBillingService(db)
    classification = billing_service.classify_transcription_request(session.id, user_id)
    
    assert classification["transcription_type"] == TranscriptionType.RETRY_SUCCESS
    assert classification["is_billable"] == True
    assert classification["cost_estimate"] > 0
    assert classification["requires_confirmation"] == True

def test_usage_log_billing_classification():
    """Test usage log creation respects billing classification"""
    session = create_completed_session(db, user_id)
    result = create_mock_transcription_result(duration_sec=180, cost_usd=0.05)
    
    billing_service = TranscriptionBillingService(db)
    
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
```

### Integration Tests
```bash
# Test: Failed session retry (free)
curl -X POST /api/v1/sessions/$FAILED_SESSION_ID/retry-transcription \
  -H "Authorization: Bearer $TOKEN"

# Expected: No additional charge, original usage_minutes unchanged

# Test: Successful session re-transcription (charged)  
curl -X POST /api/v1/sessions/$SUCCESS_SESSION_ID/retranscribe \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"confirm_cost": false}'

# Expected: Cost estimate returned, confirmation required

curl -X POST /api/v1/sessions/$SUCCESS_SESSION_ID/retranscribe \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"confirm_cost": true}'

# Expected: Re-transcription started, usage_minutes incremented
```

## 📊 Success Metrics

### Financial Accuracy
- **Billing Classification**: 100% correct classification of retry vs re-transcription
- **Cost Accuracy**: 0% billing errors for failure retries (should always be $0)
- **Revenue Capture**: 100% of legitimate re-transcription requests properly charged

### User Experience  
- **Transparency**: 95% user satisfaction with billing clarity
- **Support Reduction**: 80% reduction in billing-related support tickets
- **User Trust**: Clear cost estimates increase re-transcription usage by 25%

### Technical Performance
- **Classification Speed**: <50ms for billing classification API calls
- **Cost Estimation**: <100ms for re-transcription cost estimates
- **Usage Tracking**: 100% accuracy in usage log creation and classification

## 📋 Definition of Done

- [ ] **Billing Classification**: TranscriptionBillingService correctly classifies all scenarios
- [ ] **Usage Log Enhancement**: UsageLog model includes transcription type and billing fields
- [ ] **API Endpoints**: Enhanced retry and new retranscribe endpoints with cost confirmation
- [ ] **User Interface**: Clear distinction between retry (free) and re-transcribe (charged) actions
- [ ] **Cost Estimation**: Accurate cost estimation for re-transcription requests
- [ ] **Usage Tracking**: Proper integration with usage analytics system (US001)
- [ ] **Unit Tests**: >90% coverage for billing logic and classification
- [ ] **Integration Tests**: End-to-end billing scenarios verified
- [ ] **User Documentation**: Clear explanation of billing policy for retries vs re-transcription
- [ ] **Admin Tools**: Billing analytics distinguish between transcription types

## 🔄 Dependencies & Risks

### Dependencies  
- ✅ US001 (Usage Analytics Foundation) - Required for usage log classification
- ✅ Current transcription system - Base functionality for retry/re-transcription
- ⏳ Cost estimation accuracy for different STT providers
- ⏳ User experience design for cost confirmation flows

### Risks & Mitigations
- **Risk**: Users confused by retry vs re-transcription distinction
  - **Mitigation**: Clear UI labels, help text, confirmation dialogs
- **Risk**: Cost estimation inaccuracy leads to user complaints
  - **Mitigation**: Conservative estimates, clear "estimate" labeling, monitoring
- **Risk**: Billing logic complexity introduces bugs
  - **Mitigation**: Comprehensive test coverage, gradual rollout, monitoring

## 📞 Stakeholders

**Product Owner**: Business/Finance Team  
**Technical Lead**: Backend Engineering, Billing Systems  
**Reviewers**: Finance (Revenue), Legal (Terms of Service), UX (User Experience)  
**QA Focus**: Billing accuracy, User experience, Financial compliance