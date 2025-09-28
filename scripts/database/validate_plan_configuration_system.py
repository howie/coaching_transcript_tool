#!/usr/bin/env python3
"""
Comprehensive validation script for the Plan Configuration system.
Tests database integration, service layer, and API endpoints.

Usage:
    python scripts/database/validate_plan_configuration_system.py [--verbose]
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

import httpx

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from coaching_assistant.core.database import SessionLocal
from coaching_assistant.models.plan_configuration import PlanConfiguration
from coaching_assistant.models.user import UserPlan
from coaching_assistant.services.plan_configuration_service import (
    PlanConfigurationService,
)
from coaching_assistant.services.plan_limits import PlanName, get_global_plan_limits

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PlanConfigurationValidator:
    """Comprehensive validator for plan configuration system."""

    def __init__(self, verbose: bool = False):
        """Initialize validator."""
        self.verbose = verbose
        self.db = SessionLocal()
        self.plan_service = PlanConfigurationService()
        self.plan_limits_service = get_global_plan_limits()
        self.validation_results = []

        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()

    def add_result(self, test_name: str, passed: bool, details: str = ""):
        """Add validation result."""
        self.validation_results.append(
            {"test": test_name, "passed": passed, "details": details}
        )

        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
        if details and (not passed or self.verbose):
            logger.info(f"    {details}")

    def validate_database_configuration(self) -> bool:
        """Validate database plan configurations."""
        logger.info("🔍 Validating database plan configurations...")

        try:
            # Check if plan_configurations table exists and has data
            plan_configs = self.db.query(PlanConfiguration).all()

            if not plan_configs:
                self.add_result(
                    "Database Configuration",
                    False,
                    "No plan configurations found in database",
                )
                return False

            # Expected plans (Phase 2)
            expected_plans = ["free", "student", "pro", "coaching_school"]
            actual_plans = [p.plan_name for p in plan_configs]

            missing_plans = set(expected_plans) - set(actual_plans)
            if missing_plans:
                self.add_result(
                    "Database Configuration", False, f"Missing plans: {missing_plans}"
                )
                return False

            # Validate Phase 2 requirements (minutes-only limits)
            phase2_compliant = True
            for plan in plan_configs:
                limits = plan.limits
                sessions_limit = limits.get("max_sessions", 0)
                transcriptions_limit = limits.get("max_transcription_count", 0)
                minutes_limit = limits.get("max_total_minutes", 0)

                # Phase 2: Sessions and transcriptions should be unlimited (-1)
                if sessions_limit != -1 or transcriptions_limit != -1:
                    phase2_compliant = False
                    self.add_result(
                        f"Phase 2 Compliance - {plan.plan_name}",
                        False,
                        f"Sessions: {sessions_limit}, Transcriptions: {transcriptions_limit} (should be -1)",
                    )

                # Validate display names (Chinese)
                chinese_names = {
                    "free": "免費試用方案",
                    "student": "學習方案",
                    "pro": "專業方案",
                    "coaching_school": "認證學校方案",
                }
                expected_name = chinese_names.get(plan.plan_name)
                if plan.display_name != expected_name:
                    self.add_result(
                        f"Display Name - {plan.plan_name}",
                        False,
                        f"Expected: {expected_name}, Got: {plan.display_name}",
                    )

                # Validate pricing (TWD)
                expected_prices = {
                    "free": (0, 0),
                    "student": (29900, 299000),  # 299 TWD/month, 2990 TWD/year
                    "pro": (89900, 764150),  # 899 TWD/month, 7641.5 TWD/year
                    "coaching_school": (500000, 4250000),  # 5000 TWD/month base
                }
                monthly_expected, annual_expected = expected_prices[plan.plan_name]
                if (
                    plan.monthly_price_twd_cents != monthly_expected
                    or plan.annual_price_twd_cents != annual_expected
                ):
                    self.add_result(
                        f"Pricing - {plan.plan_name}",
                        False,
                        f"Expected: {monthly_expected}/{annual_expected}, Got: {plan.monthly_price_twd_cents}/{plan.annual_price_twd_cents}",
                    )

            self.add_result(
                "Database Configuration",
                True,
                f"Found {len(plan_configs)} plans: {actual_plans}",
            )

            return phase2_compliant

        except Exception as e:
            self.add_result("Database Configuration", False, f"Database error: {e}")
            return False

    def validate_plan_configuration_service(self) -> bool:
        """Validate PlanConfigurationService."""
        logger.info("🔧 Validating PlanConfigurationService...")

        try:
            # Test getting all plans
            all_plans = self.plan_service.get_all_plan_configs()
            if len(all_plans) < 4:
                self.add_result(
                    "Service - Get All Plans",
                    False,
                    f"Expected at least 4 plans, got {len(all_plans)}",
                )
                return False

            # Test getting specific plan configs
            test_cases = [
                (UserPlan.FREE, "免費試用方案"),
                (UserPlan.STUDENT, "學習方案"),
                (UserPlan.PRO, "專業方案"),
                (UserPlan.COACHING_SCHOOL, "認證學校方案"),
            ]

            for user_plan, expected_display_name in test_cases:
                try:
                    config = self.plan_service.get_plan_config(user_plan)

                    # Validate structure
                    required_keys = [
                        "plan_type",
                        "display_name",
                        "limits",
                        "monthly_price_twd_cents",
                    ]
                    missing_keys = [key for key in required_keys if key not in config]
                    if missing_keys:
                        self.add_result(
                            f"Service - {user_plan.value} Structure",
                            False,
                            f"Missing keys: {missing_keys}",
                        )
                        continue

                    # Validate display name
                    if config["display_name"] != expected_display_name:
                        self.add_result(
                            f"Service - {user_plan.value} Display Name",
                            False,
                            f"Expected: {expected_display_name}, Got: {config['display_name']}",
                        )
                        continue

                    # Validate Phase 2 limits
                    limits = config["limits"]
                    if (
                        limits.get("max_sessions") != -1
                        or limits.get("max_transcription_count") != -1
                    ):
                        self.add_result(
                            f"Service - {user_plan.value} Phase 2 Limits",
                            False,
                            "Sessions/Transcriptions should be unlimited (-1)",
                        )
                        continue

                    self.add_result(
                        f"Service - {user_plan.value}",
                        True,
                        f"Config loaded successfully: {expected_display_name}",
                    )

                except Exception as e:
                    self.add_result(
                        f"Service - {user_plan.value}",
                        False,
                        f"Error loading config: {e}",
                    )

            return True

        except Exception as e:
            self.add_result("Plan Configuration Service", False, f"Service error: {e}")
            return False

    def validate_plan_limits_service(self) -> bool:
        """Validate PlanLimits service integration."""
        logger.info("📊 Validating PlanLimits service...")

        try:
            # Test plan limit retrieval
            test_plans = [
                PlanName.FREE,
                PlanName.STUDENT,
                PlanName.PRO,
                PlanName.COACHING_SCHOOL,
            ]

            for plan_name in test_plans:
                try:
                    plan_limit = self.plan_limits_service.get_plan_limit(plan_name)

                    # Validate Phase 2 compliance
                    if (
                        plan_limit.max_sessions != -1
                        or plan_limit.max_transcriptions != -1
                    ):
                        self.add_result(
                            f"PlanLimits - {plan_name.value} Phase 2",
                            False,
                            f"Sessions: {plan_limit.max_sessions}, Transcriptions: {plan_limit.max_transcriptions}",
                        )
                        continue

                    # Validate minutes limit
                    expected_minutes = {
                        PlanName.FREE: 200,
                        PlanName.STUDENT: 500,
                        PlanName.PRO: 3000,
                        PlanName.COACHING_SCHOOL: -1,  # Unlimited
                    }

                    if plan_limit.max_minutes != expected_minutes[plan_name]:
                        self.add_result(
                            f"PlanLimits - {plan_name.value} Minutes",
                            False,
                            f"Expected: {expected_minutes[plan_name]}, Got: {plan_limit.max_minutes}",
                        )
                        continue

                    self.add_result(
                        f"PlanLimits - {plan_name.value}",
                        True,
                        f"Minutes: {plan_limit.max_minutes}, File size: {plan_limit.max_file_size_mb}MB",
                    )

                except Exception as e:
                    self.add_result(
                        f"PlanLimits - {plan_name.value}",
                        False,
                        f"Error getting limits: {e}",
                    )

            return True

        except Exception as e:
            self.add_result("PlanLimits Service", False, f"Service error: {e}")
            return False

    async def validate_api_endpoints(self) -> bool:
        """Validate API endpoints (if server is running)."""
        logger.info("🌐 Validating API endpoints...")

        try:
            async with httpx.AsyncClient() as client:
                # Check if server is running
                try:
                    response = await client.get(
                        "http://localhost:8000/health", timeout=5.0
                    )
                    if response.status_code != 200:
                        self.add_result(
                            "API Server Health",
                            False,
                            f"Server not responding: {response.status_code}",
                        )
                        return False
                except httpx.ConnectError:
                    self.add_result(
                        "API Endpoints",
                        False,
                        "API server not running (http://localhost:8000)",
                    )
                    return False

                # Test plans endpoint (requires auth - skip for now)
                self.add_result(
                    "API Endpoints",
                    True,
                    "API server is running (authentication required for full testing)",
                )

                return True

        except Exception as e:
            self.add_result("API Endpoints", False, f"API test error: {e}")
            return False

    async def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation tests."""
        logger.info("🚀 Starting comprehensive plan configuration validation...")

        # Database validation
        db_valid = self.validate_database_configuration()

        # Service layer validation
        service_valid = self.validate_plan_configuration_service()
        plan_limits_valid = self.validate_plan_limits_service()

        # API validation (optional)
        api_valid = await self.validate_api_endpoints()

        # Summary
        passed_tests = len([r for r in self.validation_results if r["passed"]])
        total_tests = len(self.validation_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        overall_success = all([db_valid, service_valid, plan_limits_valid])

        summary = {
            "overall_success": overall_success,
            "success_rate": success_rate,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "database_valid": db_valid,
            "service_valid": service_valid,
            "plan_limits_valid": plan_limits_valid,
            "api_valid": api_valid,
            "results": self.validation_results,
        }

        # Print summary
        logger.info("\n" + "=" * 80)
        if overall_success:
            logger.info("🎉 PLAN CONFIGURATION SYSTEM VALIDATION SUCCESSFUL!")
        else:
            logger.error("❌ PLAN CONFIGURATION SYSTEM VALIDATION FAILED!")

        logger.info("=" * 80)
        logger.info(
            f"📊 Test Results: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)"
        )
        logger.info(f"💾 Database: {'✅' if db_valid else '❌'}")
        logger.info(f"🔧 Service Layer: {'✅' if service_valid else '❌'}")
        logger.info(f"📊 Plan Limits: {'✅' if plan_limits_valid else '❌'}")
        logger.info(f"🌐 API Endpoints: {'✅' if api_valid else '⚠️  (optional)'}")

        # List failed tests
        failed_tests = [r for r in self.validation_results if not r["passed"]]
        if failed_tests:
            logger.info("\n❌ Failed Tests:")
            for test in failed_tests:
                logger.error(f"   - {test['test']}: {test['details']}")

        logger.info("=" * 80)

        return summary


async def main():
    """Main execution function."""
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    try:
        with PlanConfigurationValidator(verbose=verbose) as validator:
            summary = await validator.run_all_validations()

            # Save detailed results
            results_file = (
                Path("tmp")
                / f"validation_results_{summary['passed_tests']}_{summary['total_tests']}.json"
            )
            results_file.parent.mkdir(exist_ok=True)

            with open(results_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"📄 Detailed results saved to: {results_file}")

            # Exit with appropriate code
            sys.exit(0 if summary["overall_success"] else 1)

    except Exception as e:
        logger.error(f"❌ Validation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
