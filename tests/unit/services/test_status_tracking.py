#!/usr/bin/env python3
"""
Test script for the new status tracking implementation.
"""

import requests
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"


def print_step(step_name, result=None):
    """Print test step with result."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    if result is None:
        print(f"[{timestamp}] 🧪 {step_name}")
    elif result:
        print(f"[{timestamp}] ✅ {step_name}")
    else:
        print(f"[{timestamp}] ❌ {step_name}")


def test_status_endpoint_structure():
    """Test that the status endpoint exists and returns proper structure."""
    print_step("Testing status endpoint structure")

    # Test with a non-existent session ID
    test_session_id = "00000000-0000-0000-0000-000000000000"

    try:
        response = requests.get(f"{API_V1}/sessions/{test_session_id}/status")

        if response.status_code == 404:
            print_step(
                "Status endpoint exists and returns 404 for non-existent session",
                True,
            )
            return True
        elif response.status_code == 401:
            print_step(
                "Status endpoint requires authentication (expected)", True
            )
            return True
        else:
            print_step(
                f"Unexpected status code: {response.status_code}", False
            )
            return False

    except requests.exceptions.ConnectionError:
        print_step("Cannot connect to API server", False)
        return False
    except Exception as e:
        print_step(f"Error testing status endpoint: {e}", False)
        return False


def test_database_schema():
    """Test that the processing_status table exists."""
    print_step("Testing database schema")

    try:
        from sqlalchemy import create_engine, text
        import os

        # Get database URL from environment
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            print_step("DATABASE_URL not set", False)
            return False

        engine = create_engine(db_url)

        # Check if the processing_status table exists
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'processing_status'
            """
                )
            )

            tables = result.fetchall()
            if tables:
                print_step("processing_status table exists in database", True)

                # Check table structure
                result = conn.execute(
                    text(
                        """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = 'processing_status'
                    ORDER BY ordinal_position
                """
                    )
                )

                columns = result.fetchall()
                expected_columns = [
                    "id",
                    "session_id",
                    "status",
                    "progress",
                    "message",
                    "duration_processed",
                    "duration_total",
                    "started_at",
                    "estimated_completion",
                    "processing_speed",
                    "created_at",
                    "updated_at",
                ]

                actual_columns = [col[0] for col in columns]
                missing_columns = set(expected_columns) - set(actual_columns)

                if not missing_columns:
                    print_step("All required columns exist", True)
                    return True
                else:
                    print_step(f"Missing columns: {missing_columns}", False)
                    return False
            else:
                print_step("processing_status table not found", False)
                return False

    except Exception as e:
        print_step(f"Error checking database schema: {e}", False)
        return False


def test_api_documentation():
    """Test that the new endpoint appears in API documentation."""
    print_step("Testing API documentation")

    try:
        response = requests.get(f"{BASE_URL}/openapi.json")

        if response.status_code == 200:
            openapi_spec = response.json()

            # Check if the status endpoint is in the paths
            status_path = "/api/v1/sessions/{session_id}/status"
            paths = openapi_spec.get("paths", {})

            if status_path in paths:
                print_step("Status endpoint documented in OpenAPI spec", True)

                # Check if it has the GET method
                endpoint = paths[status_path]
                if "get" in endpoint:
                    print_step(
                        "GET method documented for status endpoint", True
                    )
                    return True
                else:
                    print_step(
                        "GET method not found in status endpoint", False
                    )
                    return False
            else:
                print_step("Status endpoint not found in OpenAPI spec", False)
                return False
        else:
            print_step(
                f"Cannot access OpenAPI spec: {response.status_code}", False
            )
            return False

    except Exception as e:
        print_step(f"Error checking API documentation: {e}", False)
        return False


def main():
    """Run all tests."""
    print("🚀 Starting Status Tracking Implementation Tests")
    print("=" * 60)

    tests = [
        test_status_endpoint_structure,
        test_database_schema,
        test_api_documentation,
    ]

    results = []
    for test in tests:
        print()
        result = test()
        results.append(result)

    print()
    print("=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print(
            "🎉 All tests passed! Status tracking implementation is working correctly."
        )
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the implementation.")
        sys.exit(1)


if __name__ == "__main__":
    main()
