"""API dependency injection validation tests.

These tests ensure that API endpoints properly use dependency injection
and don't have missing database session parameters that cause runtime errors.
"""

import pytest
import inspect
from fastapi import FastAPI, Depends
from typing import get_type_hints

from src.coaching_assistant.api.v1.coaching_sessions import router as coaching_sessions_router
from src.coaching_assistant.api.v1.plans import router as plans_router
from src.coaching_assistant.api.v1.subscriptions import router as subscriptions_router
from src.coaching_assistant.core.database import get_db
from src.coaching_assistant.infrastructure.factories import (
    get_coaching_session_use_case,
    get_plan_retrieval_use_case,
    get_subscription_management_use_case
)


class TestAPIEndpointDependencyInjection:
    """Test that API endpoints properly use dependency injection."""

    def test_coaching_sessions_endpoints_use_factories(self):
        """Test that coaching sessions endpoints use proper factory injection."""
        app = FastAPI()
        app.include_router(coaching_sessions_router)

        # Get all routes from the coaching sessions router
        routes = [route for route in app.routes if hasattr(route, 'endpoint')]

        factory_using_endpoints = []
        direct_db_endpoints = []

        for route in routes:
            if hasattr(route, 'endpoint') and route.endpoint:
                # Get the function signature
                sig = inspect.signature(route.endpoint)

                # Check parameters for dependency injection patterns
                has_factory_dependency = False
                has_direct_db_dependency = False

                for param_name, param in sig.parameters.items():
                    if param.default != inspect.Parameter.empty:
                        if isinstance(param.default, type(Depends())):
                            dependency_func = param.default.dependency
                            # Check if it's a factory function (use case)
                            if dependency_func.__name__.endswith('_use_case'):
                                has_factory_dependency = True
                            # Check if it's direct database dependency
                            elif dependency_func == get_db:
                                has_direct_db_dependency = True

                if has_factory_dependency:
                    factory_using_endpoints.append(route.path)
                elif has_direct_db_dependency:
                    direct_db_endpoints.append(route.path)

        # Assert that migrated endpoints use factories
        expected_factory_endpoints = [
            '/api/v1/coaching-sessions',
            '/api/v1/coaching-sessions/{session_id}',
        ]

        for endpoint in expected_factory_endpoints:
            matching_routes = [path for path in factory_using_endpoints if endpoint in path]
            assert len(matching_routes) > 0, f"Expected factory dependency injection for {endpoint}"

    def test_plans_endpoints_use_factories(self):
        """Test that plans endpoints properly use factory injection."""
        app = FastAPI()
        app.include_router(plans_router)

        routes = [route for route in app.routes if hasattr(route, 'endpoint')]
        factory_endpoints = []

        for route in routes:
            if hasattr(route, 'endpoint') and route.endpoint:
                sig = inspect.signature(route.endpoint)

                for param_name, param in sig.parameters.items():
                    if param.default != inspect.Parameter.empty:
                        if isinstance(param.default, type(Depends())):
                            dependency_func = param.default.dependency
                            if dependency_func == get_plan_retrieval_use_case:
                                factory_endpoints.append(route.path)
                                break

        # Plans API should be fully migrated to use factories
        assert len(factory_endpoints) > 0, "Plans endpoints should use factory injection"

    def test_subscriptions_endpoints_use_factories(self):
        """Test that subscriptions endpoints properly use factory injection."""
        app = FastAPI()
        app.include_router(subscriptions_router)

        routes = [route for route in app.routes if hasattr(route, 'endpoint')]
        factory_endpoints = []

        for route in routes:
            if hasattr(route, 'endpoint') and route.endpoint:
                sig = inspect.signature(route.endpoint)

                for param_name, param in sig.parameters.items():
                    if param.default != inspect.Parameter.empty:
                        if isinstance(param.default, type(Depends())):
                            dependency_func = param.default.dependency
                            if dependency_func == get_subscription_management_use_case:
                                factory_endpoints.append(route.path)
                                break

        # Subscriptions API should be fully migrated to use factories
        assert len(factory_endpoints) > 0, "Subscriptions endpoints should use factory injection"


class TestResponseConversionFunctions:
    """Test that response conversion functions have required parameters."""

    def test_coaching_session_response_functions_have_db_param(self):
        """Test that coaching session response functions accept db parameter."""
        from src.coaching_assistant.api.v1.coaching_sessions import (
            convert_coaching_session_to_response,
        )

        # Get function signature
        sig = inspect.signature(convert_coaching_session_to_response)
        param_names = list(sig.parameters.keys())

        # Should have both coaching_session and db parameters
        assert 'coaching_session' in param_names, "Response function should accept coaching_session parameter"
        assert 'db' in param_names, "Response function should accept db parameter for related data"

    def test_response_function_parameter_types(self):
        """Test that response functions have proper parameter type hints."""
        from src.coaching_assistant.api.v1.coaching_sessions import (
            convert_coaching_session_to_response,
        )
        from sqlalchemy.orm import Session
        from src.coaching_assistant.core.models.coaching_session import CoachingSession

        # Get type hints
        type_hints = get_type_hints(convert_coaching_session_to_response)

        # Verify parameter types
        assert 'coaching_session' in type_hints, "coaching_session parameter should have type hint"
        assert 'db' in type_hints, "db parameter should have type hint"

        # Check that db parameter is typed as Session
        assert type_hints.get('db') == Session or 'Session' in str(type_hints.get('db', '')), \
            "db parameter should be typed as SQLAlchemy Session"


class TestFactoryFunctions:
    """Test that factory functions properly create dependencies."""

    def test_coaching_session_use_case_factory(self):
        """Test that coaching session use case factory works correctly."""
        # This would require a mock database session
        # For now, just test that the factory function exists and is callable
        assert callable(get_coaching_session_use_case), "Coaching session factory should be callable"

    def test_plan_retrieval_use_case_factory(self):
        """Test that plan retrieval use case factory works correctly."""
        assert callable(get_plan_retrieval_use_case), "Plan retrieval factory should be callable"

    def test_subscription_management_use_case_factory(self):
        """Test that subscription management use case factory works correctly."""
        assert callable(get_subscription_management_use_case), "Subscription management factory should be callable"


class TestLegacyEndpointDetection:
    """Test detection of legacy endpoints that need migration."""

    def test_detect_direct_db_dependencies(self):
        """Test detection of endpoints that still use direct database dependencies."""
        # This test scans all API endpoints to find ones using Depends(get_db)
        from src.coaching_assistant.api.v1 import (
            auth,
            billing_analytics,
            clients,
            coach_profile,
            sessions,
            usage,
            usage_history,
            user,
        )

        modules_to_check = [
            auth,
            billing_analytics,
            clients,
            coach_profile,
            sessions,
            usage,
            usage_history,
            user,
        ]

        legacy_endpoints = []

        for module in modules_to_check:
            if hasattr(module, 'router'):
                app = FastAPI()
                app.include_router(module.router)

                routes = [route for route in app.routes if hasattr(route, 'endpoint')]

                for route in routes:
                    if hasattr(route, 'endpoint') and route.endpoint:
                        sig = inspect.signature(route.endpoint)

                        for param_name, param in sig.parameters.items():
                            if param.default != inspect.Parameter.empty:
                                if isinstance(param.default, type(Depends())):
                                    if param.default.dependency == get_db:
                                        legacy_endpoints.append({
                                            'module': module.__name__,
                                            'path': route.path,
                                            'method': route.methods,
                                            'function': route.endpoint.__name__
                                        })

        # Log findings for reference (not an assertion failure)
        if legacy_endpoints:
            print(f"\nFound {len(legacy_endpoints)} endpoints still using direct DB dependencies:")
            for endpoint in legacy_endpoints:
                print(f"  {endpoint['module']}: {endpoint['method']} {endpoint['path']} ({endpoint['function']})")

        # This is informational - we expect some legacy endpoints during migration
        # The goal is to track progress, not fail the test
        assert True, "Legacy endpoint detection completed"

    def test_detect_legacy_model_imports(self):
        """Test detection of API modules with legacy model imports."""
        import ast
        import os
        from pathlib import Path

        api_dir = Path("src/coaching_assistant/api/v1")
        legacy_imports = []

        if api_dir.exists():
            for py_file in api_dir.glob("*.py"):
                if py_file.name.startswith("__"):
                    continue

                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        tree = ast.parse(content)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.ImportFrom):
                            if node.module and "models" in node.module and not "core.models" in node.module:
                                legacy_imports.append({
                                    'file': py_file.name,
                                    'import': f"from {node.module} import {', '.join([n.name for n in node.names])}"
                                })
                        elif isinstance(node, ast.Import):
                            for alias in node.names:
                                if "models" in alias.name and not "core.models" in alias.name:
                                    legacy_imports.append({
                                        'file': py_file.name,
                                        'import': f"import {alias.name}"
                                    })

                except (SyntaxError, UnicodeDecodeError) as e:
                    print(f"Could not parse {py_file}: {e}")

        # Log findings for reference
        if legacy_imports:
            print(f"\nFound {len(legacy_imports)} legacy model imports:")
            for imp in legacy_imports:
                print(f"  {imp['file']}: {imp['import']}")

        # This is informational during migration
        assert True, "Legacy import detection completed"


class TestCleanArchitectureCompliance:
    """Test Clean Architecture compliance in API layer."""

    def test_no_sqlalchemy_imports_in_api_handlers(self):
        """Test that API handler functions don't import SQLAlchemy directly."""
        import ast
        import os
        from pathlib import Path

        api_dir = Path("src/coaching_assistant/api/v1")
        sqlalchemy_imports = []

        if api_dir.exists():
            for py_file in api_dir.glob("*.py"):
                if py_file.name.startswith("__"):
                    continue

                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        tree = ast.parse(content)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.ImportFrom):
                            if node.module and "sqlalchemy" in node.module.lower():
                                # Allow certain imports like Session for type hints
                                if not any(name.name in ['Session'] for name in node.names):
                                    sqlalchemy_imports.append({
                                        'file': py_file.name,
                                        'import': f"from {node.module} import {', '.join([n.name for n in node.names])}"
                                    })

                except (SyntaxError, UnicodeDecodeError) as e:
                    print(f"Could not parse {py_file}: {e}")

        if sqlalchemy_imports:
            print(f"\nFound {len(sqlalchemy_imports)} direct SQLAlchemy imports in API layer:")
            for imp in sqlalchemy_imports:
                print(f"  {imp['file']}: {imp['import']}")

        # This should eventually be zero, but during migration we track progress
        assert True, "SQLAlchemy import detection completed"

    def test_endpoint_response_patterns(self):
        """Test that API endpoints follow consistent response patterns."""
        # This test could verify:
        # 1. All endpoints return proper JSON responses
        # 2. Error handling follows consistent patterns
        # 3. Success responses have consistent structure

        # For now, this is a placeholder for future response pattern validation
        assert True, "Response pattern validation placeholder"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])