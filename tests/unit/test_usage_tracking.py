"""Unit tests for usage tracking functionality."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from freezegun import freeze_time
from sqlalchemy.orm import Session
from uuid import uuid4

from coaching_assistant.models.user import User, UserPlan
from coaching_assistant.models.session import Session as SessionModel, SessionStatus
from coaching_assistant.models.usage_log import UsageLog, TranscriptionType
from coaching_assistant.models.usage_analytics import UsageAnalytics
from coaching_assistant.models.client import Client
from coaching_assistant.services.usage_tracking import UsageTrackingService, PlanLimits


class TestPlanLimits:
    """Test plan limit configuration."""
    
    def test_get_free_plan_limits(self):
        """Test FREE plan limits."""
        limits = PlanLimits.get_limits(UserPlan.FREE)
        assert limits["minutes_per_month"] == 60
        assert limits["sessions_per_month"] == 5
        assert limits["max_file_size_mb"] == 50
        assert "basic_transcription" in limits["features"]
    
    def test_get_pro_plan_limits(self):
        """Test PRO plan limits."""
        limits = PlanLimits.get_limits(UserPlan.PRO)
        assert limits["minutes_per_month"] == 600
        assert limits["sessions_per_month"] == 50
        assert limits["max_file_size_mb"] == 200
        assert "speaker_diarization" in limits["features"]
    
    def test_get_enterprise_plan_limits(self):
        """Test ENTERPRISE plan limits."""
        limits = PlanLimits.get_limits(UserPlan.ENTERPRISE)
        assert limits["minutes_per_month"] == float("inf")
        assert limits["sessions_per_month"] == float("inf")
        assert limits["max_file_size_mb"] == 500
        assert "api_access" in limits["features"]


class TestUsageTrackingService:
    """Test usage tracking service functionality."""
    
    @pytest.fixture
    def test_user(self, db_session: Session) -> User:
        """Create a test user."""
        user = User(
            id=uuid4(),
            email="test@example.com",
            name="Test User",
            plan=UserPlan.FREE,
            usage_minutes=0,
            session_count=0,
            transcription_count=0,
            total_sessions_created=0,
            total_transcriptions_generated=0,
            total_minutes_processed=Decimal("0"),
            total_cost_usd=Decimal("0")
        )
        db_session.add(user)
        db_session.commit()
        return user
    
    @pytest.fixture
    def test_client(self, db_session: Session, test_user: User) -> Client:
        """Create a test client."""
        client = Client(
            id=uuid4(),
            user_id=test_user.id,
            name="Test Client",
            email="client@example.com"
        )
        db_session.add(client)
        db_session.commit()
        return client
    
    @pytest.fixture
    def test_session(self, db_session: Session, test_user: User, test_client: Client) -> SessionModel:
        """Create a test session."""
        session = SessionModel(
            id=uuid4(),
            title="Test Session",
            user_id=test_user.id,
            status=SessionStatus.COMPLETED,
            duration_seconds=300,  # 5 minutes
            language="en-US",
            stt_provider="google",
            audio_filename="test.mp3"
        )
        db_session.add(session)
        db_session.commit()
        return session
    
    @pytest.fixture
    def tracking_service(self, db_session: Session) -> UsageTrackingService:
        """Create usage tracking service instance."""
        return UsageTrackingService(db_session)
    
    def test_create_usage_log_original(
        self,
        db_session: Session,
        tracking_service: UsageTrackingService,
        test_session: SessionModel,
        test_user: User
    ):
        """Test creating usage log for original transcription."""
        usage_log = tracking_service.create_usage_log(
            session=test_session,
            transcription_type=TranscriptionType.ORIGINAL,
            cost_usd=0.08,
            is_billable=True,
            billing_reason="transcription_completed"
        )
        
        assert usage_log.user_id == test_user.id
        assert usage_log.session_id == test_session.id
        assert usage_log.duration_minutes == 5
        assert usage_log.duration_seconds == 300
        assert float(usage_log.cost_usd) == 0.08
        assert usage_log.stt_provider == "google"
        assert usage_log.transcription_type == TranscriptionType.ORIGINAL
        assert usage_log.is_billable is True
        assert usage_log.user_plan == "free"
        assert usage_log.parent_log_id is None
    
    def test_create_usage_log_retry(
        self,
        db_session: Session,
        tracking_service: UsageTrackingService,
        test_session: SessionModel,
        test_user: User
    ):
        """Test creating usage log for retry transcription."""
        # Create original log first
        original_log = tracking_service.create_usage_log(
            session=test_session,
            transcription_type=TranscriptionType.ORIGINAL,
            cost_usd=0.08
        )
        
        # Create retry log
        retry_log = tracking_service.create_usage_log(
            session=test_session,
            transcription_type=TranscriptionType.RETRY_FAILED,
            cost_usd=0.0,
            is_billable=False,
            billing_reason="free_retry_after_failure"
        )
        
        assert retry_log.parent_log_id == original_log.id
        assert retry_log.is_billable is False
        assert float(retry_log.cost_usd) == 0.0
        assert retry_log.transcription_type == TranscriptionType.RETRY_FAILED
    
    def test_user_counters_updated(
        self,
        db_session: Session,
        tracking_service: UsageTrackingService,
        test_session: SessionModel,
        test_user: User
    ):
        """Test that user counters are updated after usage log creation."""
        initial_usage = test_user.usage_minutes
        initial_transcriptions = test_user.transcription_count
        
        tracking_service.create_usage_log(
            session=test_session,
            cost_usd=0.08
        )
        
        db_session.refresh(test_user)
        
        assert test_user.usage_minutes == initial_usage + 5
        assert test_user.transcription_count == initial_transcriptions + 1
        assert test_user.total_transcriptions_generated == 1
        assert float(test_user.total_minutes_processed) == 5.0
        assert float(test_user.total_cost_usd) == 0.08
    
    @freeze_time("2025-08-15 10:00:00")
    def test_monthly_usage_reset(
        self,
        db_session: Session,
        tracking_service: UsageTrackingService,
        test_session: SessionModel,
        test_user: User
    ):
        """Test monthly usage counter reset."""
        # Set user's counters to previous month
        test_user.usage_minutes = 50
        test_user.session_count = 5
        test_user.transcription_count = 10
        test_user.current_month_start = datetime(2025, 7, 1)
        db_session.commit()
        
        # Create usage log in new month
        tracking_service.create_usage_log(
            session=test_session,
            cost_usd=0.08
        )
        
        db_session.refresh(test_user)
        
        # Monthly counters should be reset
        assert test_user.usage_minutes == 5  # Only new usage
        assert test_user.transcription_count == 1  # Reset to 1
        assert test_user.current_month_start.month == 8
        
        # Cumulative counters should continue
        assert test_user.total_transcriptions_generated == 1
    
    def test_increment_session_count(
        self,
        db_session: Session,
        tracking_service: UsageTrackingService,
        test_user: User
    ):
        """Test incrementing session count."""
        initial_count = test_user.session_count
        initial_total = test_user.total_sessions_created
        
        tracking_service.increment_session_count(test_user)
        
        db_session.refresh(test_user)
        
        assert test_user.session_count == initial_count + 1
        assert test_user.total_sessions_created == initial_total + 1
    
    @freeze_time("2025-08-15")
    def test_monthly_analytics_creation(
        self,
        db_session: Session,
        tracking_service: UsageTrackingService,
        test_session: SessionModel,
        test_user: User
    ):
        """Test monthly analytics record creation."""
        tracking_service.create_usage_log(
            session=test_session,
            transcription_type=TranscriptionType.ORIGINAL,
            cost_usd=0.08
        )
        
        # Check analytics record was created
        analytics = db_session.query(UsageAnalytics).filter(
            UsageAnalytics.user_id == test_user.id,
            UsageAnalytics.month_year == "2025-08"
        ).first()
        
        assert analytics is not None
        assert analytics.primary_plan == "free"
        assert analytics.transcriptions_completed == 1
        assert analytics.original_transcriptions == 1
        assert float(analytics.total_minutes_processed) == 5.0
        assert float(analytics.total_cost_usd) == 0.08
        assert float(analytics.google_stt_minutes) == 5.0
    
    def test_monthly_analytics_aggregation(
        self,
        db_session: Session,
        tracking_service: UsageTrackingService,
        test_user: User
    ):
        """Test monthly analytics aggregation with multiple sessions."""
        # Create multiple sessions and usage logs
        for i in range(3):
            session = SessionModel(
                id=uuid4(),
                title=f"Session {i}",
                user_id=test_user.id,
                status=SessionStatus.COMPLETED,
                duration_seconds=120 * (i + 1),  # 2, 4, 6 minutes
                stt_provider="google" if i < 2 else "assemblyai"
            )
            db_session.add(session)
            db_session.commit()
            
            tracking_service.create_usage_log(
                session=session,
                cost_usd=0.02 * (i + 1)
            )
        
        # Check aggregated analytics
        month_year = datetime.utcnow().strftime('%Y-%m')
        analytics = db_session.query(UsageAnalytics).filter(
            UsageAnalytics.user_id == test_user.id,
            UsageAnalytics.month_year == month_year
        ).first()
        
        assert analytics.transcriptions_completed == 3
        assert float(analytics.total_minutes_processed) == 12.0  # 2+4+6
        assert float(analytics.total_cost_usd) == 0.12  # 0.02+0.04+0.06
        assert float(analytics.google_stt_minutes) == 6.0  # 2+4
        assert float(analytics.assemblyai_minutes) == 6.0  # 6
    
    def test_get_user_usage_summary(
        self,
        db_session: Session,
        tracking_service: UsageTrackingService,
        test_session: SessionModel,
        test_user: User
    ):
        """Test getting user usage summary."""
        # Create some usage data
        tracking_service.create_usage_log(
            session=test_session,
            cost_usd=0.08
        )
        
        summary = tracking_service.get_user_usage_summary(str(test_user.id))
        
        assert summary["user_id"] == str(test_user.id)
        assert summary["plan"] == "free"
        assert summary["current_month"]["usage_minutes"] == 5
        assert summary["current_month"]["transcription_count"] == 1
        assert summary["lifetime_totals"]["transcriptions_generated"] == 1
        assert summary["lifetime_totals"]["minutes_processed"] == 5.0
        assert len(summary["recent_activity"]) == 1
        assert summary["recent_activity"][0]["duration_minutes"] == 5
    
    def test_get_user_usage_history(
        self,
        db_session: Session,
        tracking_service: UsageTrackingService,
        test_session: SessionModel,
        test_user: User
    ):
        """Test getting user usage history."""
        # Create usage log
        tracking_service.create_usage_log(
            session=test_session,
            cost_usd=0.08
        )
        
        history = tracking_service.get_user_usage_history(str(test_user.id), months=3)
        
        assert history["user_id"] == str(test_user.id)
        assert history["months_requested"] == 3
        assert history["total_logs"] == 1
        assert len(history["usage_history"]) == 1
        assert history["usage_history"][0]["duration_minutes"] == 5
        assert history["usage_history"][0]["stt_provider"] == "google"
    
    def test_get_admin_analytics(
        self,
        db_session: Session,
        tracking_service: UsageTrackingService,
        test_user: User
    ):
        """Test getting admin analytics."""
        # Create multiple users and sessions
        users = []
        for i in range(3):
            user = User(
                id=uuid4(),
                email=f"user{i}@example.com",
                name=f"User {i}",
                plan=UserPlan.FREE if i < 2 else UserPlan.PRO
            )
            db_session.add(user)
            users.append(user)
        db_session.commit()
        
        # Create sessions and usage logs for each user
        for user in users:
            session = SessionModel(
                id=uuid4(),
                title=f"Session for {user.name}",
                user_id=user.id,
                status=SessionStatus.COMPLETED,
                duration_seconds=300,
                stt_provider="google"
            )
            db_session.add(session)
            db_session.commit()
            
            tracking_service.create_usage_log(
                session=session,
                cost_usd=0.08
            )
        
        # Get admin analytics
        analytics = tracking_service.get_admin_analytics()
        
        assert analytics["summary"]["total_transcriptions"] == 3
        assert analytics["summary"]["total_minutes"] == 15  # 3 * 5 minutes
        assert analytics["summary"]["total_cost_usd"] == 0.24  # 3 * 0.08
        assert analytics["unique_users"] == 3
        assert analytics["unique_sessions"] == 3
        
        # Check plan distribution
        assert "free" in analytics["plan_distribution"]
        assert analytics["plan_distribution"]["free"]["count"] == 2
        assert "pro" in analytics["plan_distribution"]
        assert analytics["plan_distribution"]["pro"]["count"] == 1
    
    def test_usage_log_survives_client_deletion(
        self,
        db_session: Session,
        tracking_service: UsageTrackingService,
        test_user: User,
        test_client: Client
    ):
        """Test that usage logs survive client deletion."""
        # Create session with client
        session = SessionModel(
            id=uuid4(),
            title="Client Session",
            user_id=test_user.id,
            status=SessionStatus.COMPLETED,
            duration_seconds=300,
            stt_provider="google"
        )
        # Note: In real implementation, you'd have client_id on session
        db_session.add(session)
        db_session.commit()
        
        # Create usage log
        usage_log = UsageLog(
            id=uuid4(),
            user_id=test_user.id,
            session_id=session.id,
            client_id=test_client.id,
            duration_minutes=5,
            duration_seconds=300,
            cost_usd=Decimal("0.08"),
            stt_provider="google",
            transcription_type=TranscriptionType.ORIGINAL,
            is_billable=True,
            user_plan="free",
            plan_limits={}
        )
        db_session.add(usage_log)
        db_session.commit()
        
        # Delete client (soft delete/anonymization)
        test_client.anonymize(1)
        db_session.commit()
        
        # Usage log should still exist
        retrieved_log = db_session.query(UsageLog).filter_by(id=usage_log.id).first()
        assert retrieved_log is not None
        assert retrieved_log.user_id == test_user.id
        assert retrieved_log.session_id == session.id
        # Client reference preserved but client is anonymized
        assert retrieved_log.client_id == test_client.id
    
    def test_cost_calculation_google(
        self,
        db_session: Session,
        tracking_service: UsageTrackingService,
        test_session: SessionModel,
        test_user: User
    ):
        """Test automatic cost calculation for Google STT."""
        test_session.stt_provider = "google"
        test_session.duration_seconds = 600  # 10 minutes
        db_session.commit()
        
        usage_log = tracking_service.create_usage_log(
            session=test_session,
            cost_usd=None  # Let service calculate
        )
        
        # Google rate: $0.016 per minute
        expected_cost = 10 * 0.016
        assert float(usage_log.cost_usd) == pytest.approx(expected_cost, rel=0.01)
    
    def test_cost_calculation_assemblyai(
        self,
        db_session: Session,
        tracking_service: UsageTrackingService,
        test_session: SessionModel,
        test_user: User
    ):
        """Test automatic cost calculation for AssemblyAI."""
        test_session.stt_provider = "assemblyai"
        test_session.duration_seconds = 600  # 10 minutes
        db_session.commit()
        
        usage_log = tracking_service.create_usage_log(
            session=test_session,
            cost_usd=None  # Let service calculate
        )
        
        # AssemblyAI rate: $0.01 per minute
        expected_cost = 10 * 0.01
        assert float(usage_log.cost_usd) == pytest.approx(expected_cost, rel=0.01)
    
    def test_non_billable_usage_log(
        self,
        db_session: Session,
        tracking_service: UsageTrackingService,
        test_session: SessionModel,
        test_user: User
    ):
        """Test non-billable usage log doesn't affect user counters."""
        initial_usage = test_user.usage_minutes
        initial_cost = float(test_user.total_cost_usd)
        
        tracking_service.create_usage_log(
            session=test_session,
            transcription_type=TranscriptionType.RETRY_FAILED,
            cost_usd=0.08,
            is_billable=False,
            billing_reason="free_retry"
        )
        
        db_session.refresh(test_user)
        
        # Non-billable shouldn't update usage counters
        assert test_user.usage_minutes == initial_usage
        assert float(test_user.total_cost_usd) == initial_cost
        
        # But analytics should still be updated
        month_year = datetime.utcnow().strftime('%Y-%m')
        analytics = db_session.query(UsageAnalytics).filter(
            UsageAnalytics.user_id == test_user.id,
            UsageAnalytics.month_year == month_year
        ).first()
        
        assert analytics.free_retries == 1
        assert analytics.transcriptions_completed == 1
        assert float(analytics.total_cost_usd) == 0.0  # No cost for free retry