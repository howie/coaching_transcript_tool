#!/usr/bin/env python3
"""
Version bumping script for the coaching assistant platform.

This script bumps the version in version.json and syncs all other version files.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Tuple

# Import the sync script for reuse
sys.path.append(str(Path(__file__).parent))
from sync_version import sync_all_versions, GREEN, RED, YELLOW, BLUE, RESET


def parse_version(version: str) -> Tuple[int, int, int]:
    """Parse version string to tuple of integers."""
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)', version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def bump_version(version: str, bump_type: str) -> str:
    """Bump version based on type (major, minor, patch)."""
    major, minor, patch = parse_version(version)

    if bump_type == 'major':
        return f"{major + 1}.0.0"
    elif bump_type == 'minor':
        return f"{major}.{minor + 1}.0"
    elif bump_type == 'patch':
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")


def update_version_json(root_dir: Path, new_version: str, description: str = None):
    """Update version.json with new version and metadata."""
    version_file = root_dir / "version.json"

    # Load current version data
    with open(version_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    old_version = data['version']

    # Update version data
    data['version'] = new_version
    data['displayVersion'] = f"v{new_version}"
    data['releaseDate'] = datetime.now().strftime('%Y-%m-%d')

    if description:
        data['description'] = description
    else:
        # Auto-generate description based on bump type
        if old_version != new_version:
            old_major, old_minor, old_patch = parse_version(old_version)
            new_major, new_minor, new_patch = parse_version(new_version)

            if new_major > old_major:
                data['description'] = "Major Release - Breaking Changes"
            elif new_minor > old_minor:
                data['description'] = "Minor Release - New Features"
            else:
                data['description'] = "Patch Release - Bug Fixes"

    # Keep existing release notes or set placeholder
    if 'releaseNotes' not in data or not data['releaseNotes']:
        data['releaseNotes'] = "To be updated with specific changes..."

    # Write updated version data
    with open(version_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')

    return old_version


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(f"{RED}Usage: python bump-version.py <major|minor|patch> [description]{RESET}")
        sys.exit(1)

    bump_type = sys.argv[1].lower()
    if bump_type not in ['major', 'minor', 'patch']:
        print(f"{RED}Invalid bump type: {bump_type}{RESET}")
        print(f"Use one of: major, minor, patch")
        sys.exit(1)

    description = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else None

    # Get project root
    script_path = Path(__file__).resolve()
    root_dir = script_path.parent.parent

    # Load current version
    version_file = root_dir / "version.json"
    if not version_file.exists():
        print(f"{RED}✗ version.json not found{RESET}")
        sys.exit(1)

    with open(version_file, 'r', encoding='utf-8') as f:
        current_data = json.load(f)
        current_version = current_data['version']

    # Calculate new version
    new_version = bump_version(current_version, bump_type)

    print(f"\n{BLUE}════════════════════════════════════════════════════{RESET}")
    print(f"{BLUE}     Version Bump Tool{RESET}")
    print(f"{BLUE}════════════════════════════════════════════════════{RESET}\n")

    print(f"Current version: {YELLOW}{current_version}{RESET}")
    print(f"New version:     {GREEN}{new_version}{RESET}")
    print(f"Bump type:       {bump_type}")
    if description:
        print(f"Description:     {description}")

    # Confirm with user
    response = input(f"\n{YELLOW}Proceed with version bump? (y/n): {RESET}")
    if response.lower() != 'y':
        print(f"{RED}Version bump cancelled{RESET}")
        sys.exit(0)

    # Update version.json
    print(f"\n{YELLOW}Updating version.json...{RESET}")
    old_version = update_version_json(root_dir, new_version, description)
    print(f"{GREEN}✓ Updated version.json from {old_version} to {new_version}{RESET}")

    # Sync all other version files
    print(f"\n{YELLOW}Synchronizing all version files...{RESET}")
    if sync_all_versions(root_dir):
        print(f"\n{GREEN}✓ Version bump completed successfully!{RESET}")
        print(f"\n{YELLOW}📝 Next steps:{RESET}")
        print(f"  1. Update release notes in version.json")
        print(f"  2. Update CHANGELOG.md with detailed changes")
        print(f"  3. Commit the changes:")
        print(f"     git add -A")
        print(f"     git commit -m \"chore: bump version to {new_version}\"")
        print(f"  4. Create a tag (after merging to main):")
        print(f"     git tag v{new_version}")
        print(f"     git push origin v{new_version}")
    else:
        print(f"{RED}✗ Version synchronization failed{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()