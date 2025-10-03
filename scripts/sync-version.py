#!/usr/bin/env python3
"""
Version synchronization script to ensure all version files are in sync.

This script reads from version.json as the single source of truth and updates:
- pyproject.toml (Python package version)
- package.json files (Frontend versions)
- Any other version references
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def load_version_json(root_dir: Path) -> Dict[str, Any]:
    """Load the master version from version.json."""
    version_file = root_dir / "version.json"
    if not version_file.exists():
        print(f"{RED}✗ version.json not found at {version_file}{RESET}")
        sys.exit(1)

    with open(version_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def update_pyproject_toml(root_dir: Path, version: str) -> bool:
    """Update version in pyproject.toml."""
    pyproject_file = root_dir / "pyproject.toml"
    if not pyproject_file.exists():
        print(f"{YELLOW}⚠ pyproject.toml not found{RESET}")
        return False

    content = pyproject_file.read_text(encoding='utf-8')
    original_content = content

    # Update version in [project] section
    pattern = r'(version\s*=\s*")[^"]+(")'
    content = re.sub(pattern, f'\\g<1>{version}\\g<2>', content)

    if content != original_content:
        pyproject_file.write_text(content, encoding='utf-8')
        print(f"{GREEN}✓ Updated pyproject.toml to version {version}{RESET}")
        return True
    else:
        print(f"{BLUE}ℹ pyproject.toml already at version {version}{RESET}")
        return False

def update_package_json(file_path: Path, version: str) -> bool:
    """Update version in a package.json file."""
    if not file_path.exists():
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        package_data = json.load(f)

    if package_data.get('version') != version:
        package_data['version'] = version
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(package_data, f, indent=2, ensure_ascii=False)
            f.write('\n')  # Add trailing newline
        print(f"{GREEN}✓ Updated {file_path.relative_to(file_path.parent.parent.parent)} to version {version}{RESET}")
        return True
    else:
        print(f"{BLUE}ℹ {file_path.relative_to(file_path.parent.parent.parent)} already at version {version}{RESET}")
        return False

def find_package_json_files(root_dir: Path) -> List[Path]:
    """Find all package.json files in the project."""
    package_files = []

    # Known locations for package.json files
    known_paths = [
        "apps/web/package.json",
        "package.json",  # Root package.json if exists
    ]

    for path in known_paths:
        full_path = root_dir / path
        if full_path.exists():
            package_files.append(full_path)

    # Also search for any other package.json files
    for package_file in root_dir.glob("**/package.json"):
        # Skip node_modules directories
        if "node_modules" not in str(package_file):
            if package_file not in package_files:
                package_files.append(package_file)

    return package_files

def check_version_consistency(root_dir: Path) -> Tuple[bool, List[str]]:
    """Check if all version files are consistent."""
    version_data = load_version_json(root_dir)
    master_version = version_data['version']
    inconsistencies = []

    # Check pyproject.toml
    pyproject_file = root_dir / "pyproject.toml"
    if pyproject_file.exists():
        content = pyproject_file.read_text(encoding='utf-8')
        match = re.search(r'version\s*=\s*"([^"]+)"', content)
        if match and match.group(1) != master_version:
            inconsistencies.append(f"pyproject.toml: {match.group(1)} (expected {master_version})")

    # Check package.json files
    for package_file in find_package_json_files(root_dir):
        with open(package_file, 'r', encoding='utf-8') as f:
            package_data = json.load(f)
            if package_data.get('version') and package_data['version'] != master_version:
                rel_path = package_file.relative_to(root_dir)
                inconsistencies.append(f"{rel_path}: {package_data['version']} (expected {master_version})")

    return len(inconsistencies) == 0, inconsistencies

def sync_all_versions(root_dir: Path) -> bool:
    """Synchronize all version files with version.json."""
    print(f"\n{BLUE}════════════════════════════════════════════════════{RESET}")
    print(f"{BLUE}     Version Synchronization Tool{RESET}")
    print(f"{BLUE}════════════════════════════════════════════════════{RESET}\n")

    # Load master version
    version_data = load_version_json(root_dir)
    version = version_data['version']
    display_version = version_data.get('displayVersion', f'v{version}')

    print(f"📌 Master version from version.json: {GREEN}{version}{RESET}")
    print(f"📌 Display version: {GREEN}{display_version}{RESET}")
    print(f"📅 Release date: {version_data.get('releaseDate', 'Not specified')}")
    print(f"📝 Description: {version_data.get('description', 'Not specified')}\n")

    changes_made = False

    # Update pyproject.toml
    print(f"{YELLOW}Checking Python package version...{RESET}")
    if update_pyproject_toml(root_dir, version):
        changes_made = True

    # Update package.json files
    print(f"\n{YELLOW}Checking Frontend package versions...{RESET}")
    package_files = find_package_json_files(root_dir)

    if not package_files:
        print(f"{YELLOW}⚠ No package.json files found{RESET}")
    else:
        for package_file in package_files:
            if update_package_json(package_file, version):
                changes_made = True

    # Final consistency check
    print(f"\n{YELLOW}Running final consistency check...{RESET}")
    is_consistent, inconsistencies = check_version_consistency(root_dir)

    if is_consistent:
        print(f"{GREEN}✓ All version files are in sync!{RESET}")
    else:
        print(f"{RED}✗ Version inconsistencies found:{RESET}")
        for inconsistency in inconsistencies:
            print(f"  {RED}• {inconsistency}{RESET}")
        return False

    if changes_made:
        print(f"\n{GREEN}✓ Version synchronization completed successfully!{RESET}")
        print(f"{YELLOW}📝 Remember to commit the changes:{RESET}")
        print(f"   git add -A")
        print(f"   git commit -m \"chore: sync version to {version}\"")
    else:
        print(f"\n{BLUE}ℹ All files were already in sync.{RESET}")

    return True

def main():
    """Main entry point."""
    # Get project root directory
    script_path = Path(__file__).resolve()
    root_dir = script_path.parent.parent

    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--check':
            # Check mode - only verify consistency
            is_consistent, inconsistencies = check_version_consistency(root_dir)
            if is_consistent:
                print(f"{GREEN}✓ All version files are consistent{RESET}")
                sys.exit(0)
            else:
                print(f"{RED}✗ Version inconsistencies found:{RESET}")
                for inconsistency in inconsistencies:
                    print(f"  {RED}• {inconsistency}{RESET}")
                sys.exit(1)
        elif sys.argv[1] == '--help':
            print("Usage: python sync-version.py [OPTIONS]")
            print("\nOptions:")
            print("  --check    Only check for version consistency (exit 1 if inconsistent)")
            print("  --help     Show this help message")
            print("\nWithout options, synchronize all version files with version.json")
            sys.exit(0)

    # Default mode - synchronize versions
    success = sync_all_versions(root_dir)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()