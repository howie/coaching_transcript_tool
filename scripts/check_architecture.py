#!/usr/bin/env python3
"""Architecture compliance checker script.

This script validates Clean Architecture compliance and prevents common
cross-domain data type errors by checking:
1. No SQLAlchemy imports in core services
2. No direct database dependencies in migrated API endpoints
3. Enum conversion existence for all enum types
4. Proper dependency direction in Clean Architecture
"""

import ast
import os
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class ArchitectureViolation:
    """Represents an architecture compliance violation."""

    file_path: str
    line_number: int
    violation_type: str
    description: str
    severity: str


@dataclass
class ComplianceReport:
    """Architecture compliance report."""

    violations: List[ArchitectureViolation]
    warnings: List[ArchitectureViolation]
    summary: Dict[str, int]


class ViolationType(Enum):
    """Types of architecture violations."""

    SQLALCHEMY_IN_CORE = "sqlalchemy_in_core"
    DIRECT_DB_DEPENDENCY = "direct_db_dependency"
    LEGACY_MODEL_IMPORT = "legacy_model_import"
    MISSING_ENUM_CONVERTER = "missing_enum_converter"
    WRONG_DEPENDENCY_DIRECTION = "wrong_dependency_direction"


class ArchitectureChecker:
    """Main architecture compliance checker."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.src_dir = self.project_root / "src" / "coaching_assistant"
        self.violations = []
        self.warnings = []

    def check_all(self) -> ComplianceReport:
        """Run all architecture compliance checks."""
        print("🔍 Running Clean Architecture compliance checks...")

        self.check_core_services_sqlalchemy()
        self.check_api_direct_db_dependencies()
        self.check_legacy_model_imports()
        self.check_enum_converters()
        self.check_dependency_direction()

        return self.generate_report()

    def check_core_services_sqlalchemy(self) -> None:
        """Check for SQLAlchemy imports in core services."""
        print("  📋 Checking core services for SQLAlchemy imports...")

        core_services_dir = self.src_dir / "core" / "services"
        if not core_services_dir.exists():
            return

        for py_file in core_services_dir.glob("*.py"):
            violations = self._check_sqlalchemy_imports(py_file)
            for line_num, import_stmt in violations:
                self.violations.append(
                    ArchitectureViolation(
                        file_path=str(py_file.relative_to(self.project_root)),
                        line_number=line_num,
                        violation_type=ViolationType.SQLALCHEMY_IN_CORE.value,
                        description=f"SQLAlchemy import in core service: {import_stmt}",
                        severity="critical",
                    )
                )

    def check_api_direct_db_dependencies(self) -> None:
        """Check for direct database dependencies in API endpoints."""
        print("  🌐 Checking API endpoints for direct DB dependencies...")

        api_dir = self.src_dir / "api" / "v1"
        if not api_dir.exists():
            return

        for py_file in api_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue

            violations = self._check_direct_db_dependencies(py_file)
            for line_num, function_name in violations:
                # Only warn for endpoints not yet migrated
                if self._is_migrated_endpoint(py_file.name):
                    severity = "critical"
                    violation_list = self.violations
                else:
                    severity = "warning"
                    violation_list = self.warnings

                violation_list.append(
                    ArchitectureViolation(
                        file_path=str(py_file.relative_to(self.project_root)),
                        line_number=line_num,
                        violation_type=ViolationType.DIRECT_DB_DEPENDENCY.value,
                        description=f"Direct DB dependency in {function_name}: Depends(get_db)",
                        severity=severity,
                    )
                )

    def check_legacy_model_imports(self) -> None:
        """Check for legacy model imports in API layer."""
        print("  📁 Checking for legacy model imports...")

        api_dir = self.src_dir / "api" / "v1"
        if not api_dir.exists():
            return

        for py_file in api_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue

            violations = self._check_legacy_model_imports(py_file)
            for line_num, import_stmt in violations:
                self.warnings.append(
                    ArchitectureViolation(
                        file_path=str(py_file.relative_to(self.project_root)),
                        line_number=line_num,
                        violation_type=ViolationType.LEGACY_MODEL_IMPORT.value,
                        description=f"Legacy model import: {import_stmt}",
                        severity="warning",
                    )
                )

    def check_enum_converters(self) -> None:
        """Check that all enums have proper converters."""
        print("  🔄 Checking enum converter completeness...")

        # Find all enums in domain and database layers
        domain_enums = self._find_enums(self.src_dir / "core" / "models")
        database_enums = self._find_enums(self.src_dir / "models")
        infrastructure_enums = self._find_enums(
            self.src_dir / "infrastructure" / "db" / "models"
        )

        # Check for missing converters
        all_enums = set(domain_enums + database_enums + infrastructure_enums)

        for enum_name in all_enums:
            if not self._has_enum_converter(enum_name):
                self.warnings.append(
                    ArchitectureViolation(
                        file_path="multiple",
                        line_number=0,
                        violation_type=ViolationType.MISSING_ENUM_CONVERTER.value,
                        description=f"Missing enum converter for {enum_name}",
                        severity="warning",
                    )
                )

    def check_dependency_direction(self) -> None:
        """Check that dependency direction follows Clean Architecture."""
        print("  ↗️ Checking dependency direction...")

        # Check that core doesn't import from infrastructure
        core_dir = self.src_dir / "core"
        if core_dir.exists():
            violations = self._check_infrastructure_imports_in_core(core_dir)
            self.violations.extend(violations)

    def _check_sqlalchemy_imports(self, file_path: Path) -> List[Tuple[int, str]]:
        """Check for SQLAlchemy imports in a Python file."""
        violations = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module and "sqlalchemy" in node.module.lower():
                        import_stmt = f"from {node.module} import {', '.join([n.name for n in node.names])}"
                        violations.append((node.lineno, import_stmt))
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if "sqlalchemy" in alias.name.lower():
                            violations.append((node.lineno, f"import {alias.name}"))

        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"  ⚠️ Could not parse {file_path}: {e}")

        return violations

    def _check_direct_db_dependencies(self, file_path: Path) -> List[Tuple[int, str]]:
        """Check for direct database dependencies in API endpoints."""
        violations = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                if "Depends(get_db)" in line:
                    # Try to extract function name
                    function_name = "unknown"
                    # Look backwards for function definition
                    for j in range(max(0, i - 10), i):
                        if "def " in lines[j - 1]:
                            func_match = re.search(r"def\s+(\w+)", lines[j - 1])
                            if func_match:
                                function_name = func_match.group(1)
                            break

                    violations.append((i, function_name))

        except (UnicodeDecodeError, IOError) as e:
            print(f"  ⚠️ Could not read {file_path}: {e}")

        return violations

    def _check_legacy_model_imports(self, file_path: Path) -> List[Tuple[int, str]]:
        """Check for legacy model imports in API files."""
        violations = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module and "models" in node.module:
                        # Skip core.models imports (these are good)
                        if "core.models" not in node.module:
                            import_stmt = f"from {node.module} import {', '.join([n.name for n in node.names])}"
                            violations.append((node.lineno, import_stmt))

        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"  ⚠️ Could not parse {file_path}: {e}")

        return violations

    def _find_enums(self, directory: Path) -> List[str]:
        """Find all enum definitions in a directory."""
        enums = []

        if not directory.exists():
            return enums

        for py_file in directory.glob("**/*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Check if class inherits from Enum
                        for base in node.bases:
                            if isinstance(base, ast.Name) and base.id == "Enum":
                                enums.append(node.name)
                            elif (
                                isinstance(base, ast.Attribute) and base.attr == "Enum"
                            ):
                                enums.append(node.name)

            except (SyntaxError, UnicodeDecodeError) as e:
                print(f"  ⚠️ Could not parse {py_file}: {e}")

        return enums

    def _has_enum_converter(self, enum_name: str) -> bool:
        """Check if an enum has proper converters."""
        # Look for conversion logic in repository files
        repo_dir = self.src_dir / "infrastructure" / "db" / "repositories"

        if not repo_dir.exists():
            return False

        for py_file in repo_dir.glob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Look for enum conversion patterns
                if f"{enum_name}(" in content or f"Domain{enum_name}" in content:
                    return True

            except (UnicodeDecodeError, IOError):
                continue

        return False

    def _check_infrastructure_imports_in_core(
        self, core_dir: Path
    ) -> List[ArchitectureViolation]:
        """Check for infrastructure imports in core layer."""
        violations = []

        for py_file in core_dir.glob("**/*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and "infrastructure" in node.module:
                            violations.append(
                                ArchitectureViolation(
                                    file_path=str(
                                        py_file.relative_to(self.project_root)
                                    ),
                                    line_number=node.lineno,
                                    violation_type=ViolationType.WRONG_DEPENDENCY_DIRECTION.value,
                                    description=f"Core importing from infrastructure: {node.module}",
                                    severity="critical",
                                )
                            )

            except (SyntaxError, UnicodeDecodeError) as e:
                print(f"  ⚠️ Could not parse {py_file}: {e}")

        return violations

    def _is_migrated_endpoint(self, filename: str) -> bool:
        """Check if an API endpoint file has been migrated to Clean Architecture."""
        # Files known to be migrated
        migrated_files = {
            "plans.py",
            "subscriptions.py",
            "coaching_sessions.py",  # Partially migrated
        }

        return filename in migrated_files

    def generate_report(self) -> ComplianceReport:
        """Generate final compliance report."""
        summary = {
            "critical_violations": len(
                [v for v in self.violations if v.severity == "critical"]
            ),
            "warnings": len(self.warnings),
            "total_issues": len(self.violations) + len(self.warnings),
        }

        return ComplianceReport(
            violations=self.violations, warnings=self.warnings, summary=summary
        )


def print_report(report: ComplianceReport) -> None:
    """Print the architecture compliance report."""
    print("\n" + "=" * 80)
    print("🏛️  CLEAN ARCHITECTURE COMPLIANCE REPORT")
    print("=" * 80)

    # Summary
    print("\n📊 Summary:")
    print(f"  Critical Violations: {report.summary['critical_violations']}")
    print(f"  Warnings: {report.summary['warnings']}")
    print(f"  Total Issues: {report.summary['total_issues']}")

    # Critical violations
    if report.violations:
        print(f"\n❌ Critical Violations ({len(report.violations)}):")
        for violation in report.violations:
            print(f"  {violation.file_path}:{violation.line_number}")
            print(f"    {violation.violation_type}: {violation.description}")
            print()

    # Warnings
    if report.warnings:
        print(f"\n⚠️  Warnings ({len(report.warnings)}):")
        for warning in report.warnings[:10]:  # Limit output
            print(f"  {warning.file_path}:{warning.line_number}")
            print(f"    {warning.violation_type}: {warning.description}")
            print()

        if len(report.warnings) > 10:
            print(f"  ... and {len(report.warnings) - 10} more warnings")

    # Status
    if report.summary["critical_violations"] == 0:
        print("✅ No critical architecture violations found!")
    else:
        print("🚨 Critical architecture violations need immediate attention!")

    print("=" * 80)


def main():
    """Main entry point for architecture checker."""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()

    checker = ArchitectureChecker(project_root)
    report = checker.check_all()

    print_report(report)

    # Exit with error code if there are critical violations
    if report.summary["critical_violations"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
