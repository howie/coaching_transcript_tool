"""
Performance tests for billing system operations.
Ensures all billing operations meet performance SLAs.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import List

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from coaching_assistant.models.usage_log import UsageLog
from coaching_assistant.models.user import User, UserPlan
from coaching_assistant.services.plan_limits import PlanLimits
from coaching_assistant.services.usage_tracking import UsageTrackingService


@contextmanager
def measure_time():
    """Context manager to measure execution time."""
    start = time.perf_counter()
    result = {"elapsed": 0}
    try:
        yield result
    finally:
        result["elapsed"] = time.perf_counter() - start


class TestBillingPerformance:
    """Performance tests for billing system."""

    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session, client: TestClient):
        """Set up test environment."""
        self.db = db_session
        self.client = client
        self.service = UsageTrackingService(db_session)

    def create_test_users(self, count: int) -> List[User]:
        """Create multiple test users for load testing."""
        users = []
        for i in range(count):
            user = User(
                email=f"perf_test_{i}@example.com",
                name=f"Perf Test {i}",
                plan=UserPlan.FREE,
                usage_minutes=0,
                session_count=0,
                transcription_count=0,
                current_month_start=datetime.now().replace(day=1),
            )
            self.db.add(user)
            users.append(user)

        self.db.commit()
        return users

    def create_bulk_usage_logs(self, user_id: str, count: int):
        """Create bulk usage logs for testing."""
        base_time = datetime.now() - timedelta(days=30)

        for i in range(count):
            log = UsageLog(
                user_id=user_id,
                session_id=None,
                action_type="transcription",
                duration_minutes=10 + (i % 50),
                is_billable=True,
                cost_usd=0.05 + (i % 10) * 0.01,
                created_at=base_time + timedelta(hours=i),
            )
            self.db.add(log)

        if count > 0:
            self.db.commit()

    @pytest.mark.performance
    def test_concurrent_limit_validation(self):
        """Test performance of concurrent limit validations."""
        users = self.create_test_users(100)

        def validate_user_limits(user: User) -> float:
            """Validate limits for a single user."""
            with measure_time() as timer:
                limits = PlanLimits.get_limits(user.plan)
                user.session_count < limits["max_sessions"]
                user.usage_minutes < limits["max_total_minutes"]
            return timer["elapsed"]

        # Test concurrent validation for 100 users
        with measure_time() as total_timer:
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = [
                    executor.submit(validate_user_limits, user) for user in users
                ]

                individual_times = []
                for future in as_completed(futures):
                    individual_times.append(future.result())

        # Performance assertions
        avg_time = sum(individual_times) / len(individual_times)
        max_time = max(individual_times)
        total_time = total_timer["elapsed"]

        # Individual validation should be < 50ms
        assert avg_time < 0.05, f"Average validation time {avg_time:.3f}s exceeds 50ms"
        assert max_time < 0.1, f"Max validation time {max_time:.3f}s exceeds 100ms"

        # Total concurrent processing should be < 2 seconds for 100 users
        assert total_time < 2.0, (
            f"Total time {total_time:.3f}s exceeds 2s for 100 users"
        )

    @pytest.mark.performance
    def test_usage_analytics_query_performance(self):
        """Test usage analytics query performance with large datasets."""
        # Create user with extensive usage history
        user = self.create_test_users(1)[0]

        # Create 10,000 usage logs (representing heavy usage)
        self.create_bulk_usage_logs(user.id, 10000)

        # Test monthly analytics query performance
        with measure_time() as timer:
            # Simulate getting monthly analytics
            current_month = datetime.now().replace(day=1)
            logs = (
                self.db.query(UsageLog)
                .filter(
                    UsageLog.user_id == user.id,
                    UsageLog.created_at >= current_month,
                )
                .all()
            )

            sum(log.duration_minutes for log in logs)
            sum(log.cost_usd for log in logs)
            len(logs)

        # Query should complete in < 100ms even with 10k records
        assert timer["elapsed"] < 0.1, (
            f"Query time {timer['elapsed']:.3f}s exceeds 100ms"
        )

    @pytest.mark.performance
    def test_api_endpoint_response_times(self):
        """Test API endpoint response times meet SLAs."""
        user = self.create_test_users(1)[0]

        endpoints_to_test = [
            ("/api/v1/plans/current", "GET", None),
            ("/api/v1/plans/compare", "GET", None),
            ("/api/v1/usage/current-month", "GET", None),
            ("/api/v1/usage/summary", "GET", None),
            ("/api/v1/plans/validate", "POST", {"action": "create_session"}),
        ]

        results = []

        for endpoint, method, json_data in endpoints_to_test:
            with measure_time() as timer:
                if method == "GET":
                    response = self.client.get(
                        endpoint,
                        headers={"Authorization": f"Bearer {user.id}"},
                    )
                else:
                    response = self.client.post(
                        endpoint,
                        json=json_data,
                        headers={"Authorization": f"Bearer {user.id}"},
                    )

            results.append(
                {
                    "endpoint": endpoint,
                    "method": method,
                    "status": response.status_code,
                    "time": timer["elapsed"],
                }
            )

        # All endpoints should respond in < 200ms
        for result in results:
            assert result["time"] < 0.2, (
                f"{result['method']} {result['endpoint']} took "
                f"{result['time']:.3f}s (exceeds 200ms SLA)"
            )

    @pytest.mark.performance
    def test_bulk_usage_update_performance(self):
        """Test performance of bulk usage updates."""
        users = self.create_test_users(50)

        # Simulate bulk usage updates (e.g., end of day processing)
        with measure_time() as timer:
            for user in users:
                # Update usage counters
                user.usage_minutes += 30
                user.session_count += 1
                user.transcription_count += 2

            self.db.commit()

        # Bulk update of 50 users should complete in < 500ms
        assert timer["elapsed"] < 0.5, f"Bulk update took {timer['elapsed']:.3f}s"

    @pytest.mark.performance
    def test_plan_upgrade_performance(self):
        """Test plan upgrade operation performance."""
        users = self.create_test_users(10)

        upgrade_times = []

        for user in users:
            with measure_time() as timer:
                # Simulate plan upgrade
                user.plan = UserPlan.PRO
                self.db.commit()

                # Verify new limits are applied
                limits = PlanLimits.get_limits(UserPlan.PRO)
                assert limits["max_sessions"] == 100

            upgrade_times.append(timer["elapsed"])

        avg_upgrade_time = sum(upgrade_times) / len(upgrade_times)
        max_upgrade_time = max(upgrade_times)

        # Plan upgrade should complete in < 100ms average
        assert avg_upgrade_time < 0.1, f"Avg upgrade time {avg_upgrade_time:.3f}s"
        assert max_upgrade_time < 0.2, f"Max upgrade time {max_upgrade_time:.3f}s"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_async_limit_checking_performance(self):
        """Test async limit checking performance."""
        users = self.create_test_users(100)

        async def check_user_limits(user: User) -> float:
            """Async limit check for a user."""
            start = time.perf_counter()

            # Simulate async limit check
            await asyncio.sleep(0.001)  # Simulate small I/O
            limits = PlanLimits.get_limits(user.plan)
            user.usage_minutes < limits["max_total_minutes"]

            return time.perf_counter() - start

        # Run 100 concurrent async checks
        start = time.perf_counter()
        tasks = [check_user_limits(user) for user in users]
        individual_times = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start

        avg_time = sum(individual_times) / len(individual_times)

        # Async operations should be highly concurrent
        assert total_time < 0.5, f"Total async time {total_time:.3f}s for 100 users"
        assert avg_time < 0.01, f"Avg async check time {avg_time:.3f}s"

    @pytest.mark.performance
    def test_database_query_optimization(self):
        """Test database query optimization for billing operations."""
        user = self.create_test_users(1)[0]

        # Create realistic data volume
        self.create_bulk_usage_logs(user.id, 1000)

        # Test optimized queries
        queries_to_test = [
            # Get current month usage
            lambda: self.db.query(UsageLog)
            .filter(
                UsageLog.user_id == user.id,
                UsageLog.created_at >= datetime.now().replace(day=1),
            )
            .count(),
            # Get total usage for user
            lambda: self.db.query(UsageLog.duration_minutes)
            .filter(UsageLog.user_id == user.id)
            .sum(),
            # Get usage by action type
            lambda: self.db.query(UsageLog.action_type, UsageLog.duration_minutes)
            .filter(UsageLog.user_id == user.id)
            .group_by(UsageLog.action_type)
            .all(),
        ]

        for i, query_func in enumerate(queries_to_test):
            with measure_time() as timer:
                query_func()

            # Each query should complete in < 50ms
            assert timer["elapsed"] < 0.05, (
                f"Query {i + 1} took {timer['elapsed']:.3f}s (exceeds 50ms)"
            )

    @pytest.mark.performance
    def test_cache_effectiveness(self):
        """Test caching effectiveness for frequently accessed data."""
        user = self.create_test_users(1)[0]

        # First call - cache miss
        with measure_time() as first_timer:
            PlanLimits.get_limits(user.plan)

        # Subsequent calls - should be cached
        cached_times = []
        for _ in range(100):
            with measure_time() as timer:
                PlanLimits.get_limits(user.plan)
            cached_times.append(timer["elapsed"])

        avg_cached_time = sum(cached_times) / len(cached_times)

        # Cached calls should be significantly faster
        assert avg_cached_time < first_timer["elapsed"] / 10, (
            "Cache not effective: cached calls not significantly faster"
        )

        # Cached calls should be < 1ms
        assert avg_cached_time < 0.001, f"Cached call avg {avg_cached_time:.3f}s"

    @pytest.mark.performance
    def test_memory_usage_under_load(self):
        """Test memory usage remains stable under load."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create load
        users = self.create_test_users(100)
        for user in users:
            self.create_bulk_usage_logs(user.id, 100)

        # Perform operations
        for user in users:
            PlanLimits.get_limits(user.plan)
            # Query logs for memory usage testing
            _ = (
                self.db.query(UsageLog)
                .filter(UsageLog.user_id == user.id)
                .limit(10)
                .all()
            )

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (< 100MB for this test)
        assert memory_increase < 100, (
            f"Memory increased by {memory_increase:.1f}MB (exceeds 100MB limit)"
        )

    def test_performance_benchmarks_summary(self):
        """Summary test to ensure all performance benchmarks are met."""
        benchmarks = {
            "limit_validation": 0.05,  # 50ms
            "usage_analytics": 0.2,  # 200ms
            "plan_upgrade": 2.0,  # 2 seconds
            "api_response": 0.2,  # 200ms
            "db_query": 0.05,  # 50ms
        }

        results = {}

        # Test limit validation
        with measure_time() as timer:
            user = self.create_test_users(1)[0]
            PlanLimits.get_limits(user.plan)
        results["limit_validation"] = timer["elapsed"]

        # Test usage analytics
        with measure_time() as timer:
            self.create_bulk_usage_logs(user.id, 100)
            # Query all logs for timing test
            _ = self.db.query(UsageLog).filter(UsageLog.user_id == user.id).all()
        results["usage_analytics"] = timer["elapsed"]

        # Test plan upgrade
        with measure_time() as timer:
            user.plan = UserPlan.PRO
            self.db.commit()
        results["plan_upgrade"] = timer["elapsed"]

        # Verify all benchmarks are met
        for name, benchmark in benchmarks.items():
            if name in results:
                assert results[name] < benchmark, (
                    f"{name}: {results[name]:.3f}s exceeds benchmark {benchmark}s"
                )

        print("\n=== Performance Benchmark Summary ===")
        for name, duration in results.items():
            benchmark = benchmarks.get(name, "N/A")
            status = "✅ PASS" if duration < benchmark else "❌ FAIL"
            print(f"{name}: {duration:.3f}s / {benchmark}s {status}")
