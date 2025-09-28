#!/usr/bin/env python3
"""
Pre-commit script to check for dependency injection issues.
This script prevents the AttributeError that occurred in production.
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple


class DependencyInjectionChecker(ast.NodeVisitor):
    """AST visitor to check for dependency injection issues."""

    def __init__(self, filename: str):
        self.filename = filename
        self.errors: List[Tuple[int, str]] = []
        self.imports = {}  # Track imports

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track imports to check for wrong dependency usage."""
        if node.module and "auth" in node.module:
            for alias in node.names:
                self.imports[alias.name] = {"module": node.module, "line": node.lineno}
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Check function parameters for dependency injection issues."""
        # Check if this is an API endpoint function
        if any(
            decorator.id == "router"
            for decorator in node.decorator_list
            if isinstance(decorator, ast.Attribute)
        ):
            self._check_endpoint_dependencies(node)

        self.generic_visit(node)

    def _check_endpoint_dependencies(self, node: ast.FunctionDef):
        """Check that API endpoints use correct dependencies."""
        for arg in node.args.args:
            if arg.arg == "current_user":
                # Check the default value (should be Depends(get_current_user_dependency))
                defaults = node.args.defaults
                if defaults:
                    default = defaults[-1]  # Last default corresponds to current_user
                    if isinstance(default, ast.Call):
                        if (
                            isinstance(default.func, ast.Name)
                            and default.func.id == "Depends"
                            and len(default.args) > 0
                        ):
                            dep_arg = default.args[0]
                            if isinstance(dep_arg, ast.Name):
                                if dep_arg.id == "get_current_user":
                                    self.errors.append(
                                        (
                                            node.lineno,
                                            f"Function '{node.name}' uses 'get_current_user' which returns UserResponse. "
                                            f"Use 'get_current_user_dependency' instead to get User model.",
                                        )
                                    )

    def visit_Attribute(self, node: ast.Attribute):
        """Check for attribute access that would fail with UserResponse."""
        if isinstance(node.value, ast.Name):
            # Look for usage_attributes being accessed
            usage_attrs = ["session_count", "transcription_count", "usage_minutes"]
            if node.attr in usage_attrs:
                # This is potentially problematic if the object is UserResponse
                # We can't be 100% sure from static analysis, but flag for review
                if "current_user" in node.value.id:
                    # Add a warning rather than error
                    pass  # We'll rely on other checks for this

        self.generic_visit(node)


def check_file(filepath: Path) -> List[Tuple[int, str]]:
    """Check a single Python file for dependency injection issues."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=str(filepath))
        checker = DependencyInjectionChecker(str(filepath))
        checker.visit(tree)

        # Additional string-based checks
        lines = content.split("\n")

        # Check for problematic import patterns
        for i, line in enumerate(lines, 1):
            if "from" in line and "auth" in line and "import" in line:
                if "get_current_user," in line or line.strip().endswith(
                    "get_current_user"
                ):
                    if "get_current_user_dependency" not in line:
                        checker.errors.append(
                            (
                                i,
                                "Importing 'get_current_user' without 'get_current_user_dependency'. "
                                "This may cause AttributeError in plan limits.",
                            )
                        )

            # Check for usage of wrong dependency
            if "Depends(get_current_user)" in line:
                checker.errors.append(
                    (
                        i,
                        "Using 'Depends(get_current_user)' which returns UserResponse. "
                        "Use 'Depends(get_current_user_dependency)' to get User model.",
                    )
                )

        return checker.errors

    except Exception as e:
        return [(0, f"Error parsing file: {e}")]


def main():
    """Main function to check all relevant files."""
    if len(sys.argv) > 1:
        # Check specific files (for pre-commit)
        files_to_check = [Path(f) for f in sys.argv[1:] if f.endswith(".py")]
    else:
        # Check all API files
        api_dir = Path("src/coaching_assistant/api")
        if not api_dir.exists():
            print("API directory not found. Run from project root.")
            sys.exit(1)
        files_to_check = list(api_dir.glob("*.py"))

    all_errors = []

    for filepath in files_to_check:
        if not filepath.exists():
            continue

        errors = check_file(filepath)
        if errors:
            all_errors.extend([(str(filepath), line, msg) for line, msg in errors])

    if all_errors:
        print("❌ Dependency injection issues found:")
        print()
        for filepath, line, msg in all_errors:
            print(f"{filepath}:{line}: {msg}")
        print()
        print("To fix these issues:")
        print("1. Import 'get_current_user_dependency' instead of 'get_current_user'")
        print("2. Use 'Depends(get_current_user_dependency)' in API endpoints")
        print("3. This ensures you get a User model with usage attributes")
        print()
        sys.exit(1)
    else:
        print("✅ No dependency injection issues found")


if __name__ == "__main__":
    main()
