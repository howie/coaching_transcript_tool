# Version Management Guide

## Overview

This project uses **`version.json` as the single source of truth** for version information. All other version files (pyproject.toml, package.json, etc.) are automatically synchronized from this master file.

## 📁 Version Files

### Master Version File
- **`version.json`** - Single source of truth containing:
  ```json
  {
    "version": "2.24.3",
    "displayVersion": "v2.24.3",
    "description": "Short description of this release",
    "releaseDate": "2025-10-02",
    "releaseNotes": "Detailed release notes...",
    "author": "Coachly Team"
  }
  ```

### Synchronized Files
These files are automatically updated from `version.json`:
- **`pyproject.toml`** - Python package version
- **`apps/web/package.json`** - Frontend application version
- **Any other `package.json`** files in the project

## 🛠️ Available Commands

### View Current Version
```bash
make version-show
```
Displays the current version from all files to quickly spot any inconsistencies.

### Check Version Consistency
```bash
make version-check
```
Verifies that all version files are in sync. Returns exit code 1 if inconsistent.

### Synchronize Versions
```bash
make version-sync
```
Updates all version files to match `version.json`. Use this after manually editing `version.json`.

### Bump Version

#### Patch Version (Bug Fixes)
```bash
make version-bump-patch
# Example: 2.24.3 → 2.24.4
```

#### Minor Version (New Features)
```bash
make version-bump-minor
# Example: 2.24.3 → 2.25.0
```

#### Major Version (Breaking Changes)
```bash
make version-bump-major
# Example: 2.24.3 → 3.0.0
```

## 📋 Workflows

### 1. Regular Development (Bug Fix)

```bash
# 1. Make your code changes and test
git add .
git commit -m "fix: resolve issue with transcript deletion"

# 2. Bump patch version
make version-bump-patch

# 3. Update release notes in version.json
vim version.json  # Add specific release notes

# 4. Update CHANGELOG.md
vim docs/claude/CHANGELOG.md  # Add detailed changes

# 5. Commit version changes
git add .
git commit -m "chore: bump version to 2.24.4"

# 6. Push and create PR
git push origin feature/your-branch
```

### 2. Feature Release

```bash
# 1. Complete feature development
git add .
git commit -m "feat: add new dashboard analytics"

# 2. Bump minor version
make version-bump-minor

# 3. Update release information
# Edit version.json with feature description and notes
# Update CHANGELOG.md with feature details

# 4. Commit version bump
git add .
git commit -m "chore: bump version to 2.25.0 - Dashboard Analytics"

# 5. Create release tag (after merging to main)
git checkout main
git pull origin main
git tag v2.25.0
git push origin v2.25.0
```

### 3. Manual Version Edit

If you need to manually edit the version (e.g., for a pre-release):

```bash
# 1. Edit version.json directly
vim version.json

# 2. Synchronize all other files
make version-sync

# 3. Verify consistency
make version-check

# 4. Commit changes
git add .
git commit -m "chore: prepare version 2.25.0-beta.1"
```

## 🔒 Pre-commit Hook

A pre-commit hook is available to ensure version consistency. To enable it:

```bash
# Enable the pre-commit hook
git config core.hooksPath .githooks

# Or copy to your .git/hooks directory
cp .githooks/pre-commit .git/hooks/pre-commit
```

The hook will:
- Check version consistency before each commit
- Remind you to update release notes when version.json changes
- Prevent commits with inconsistent versions

To bypass the check (not recommended):
```bash
git commit --no-verify
```

## 🏗️ CI/CD Integration

### GitHub Actions
The version from `version.json` is used in CI/CD pipelines:
- Docker image tags
- Release artifacts
- Deployment version tracking

### Makefile Integration
The Makefile automatically reads version from `version.json`:
```makefile
VERSION = $(shell python3 -c "import json; print(json.load(open('version.json'))['version'])")
```

## 📚 Best Practices

### 1. Version Bump Timing
- Bump version **after** code changes are complete
- Bump version **before** creating release PR
- Never bump version in the middle of development

### 2. Semantic Versioning
Follow [Semantic Versioning 2.0.0](https://semver.org/):
- **MAJOR**: Breaking API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### 3. Release Notes
Always update:
1. `releaseNotes` in `version.json` - User-facing summary
2. `docs/claude/CHANGELOG.md` - Detailed technical changes
3. Git tag message - Brief release summary

### 4. Version Consistency
- Run `make version-check` before pushing
- Use `make version-sync` after any manual edits
- Enable the pre-commit hook for automatic checking

## 🔧 Troubleshooting

### Inconsistent Versions
```bash
# Check what's different
make version-show

# Force sync from version.json
make version-sync

# Verify fix
make version-check
```

### Failed Pre-commit Hook
```bash
# If versions are inconsistent
make version-sync
git add .
git commit  # Try again

# If you must skip (emergency only)
git commit --no-verify
```

### Manual Recovery
If automated tools fail:
```bash
# 1. Check master version
cat version.json | grep version

# 2. Manually update pyproject.toml
vim pyproject.toml  # Update version = "x.y.z"

# 3. Manually update package.json files
vim apps/web/package.json  # Update "version": "x.y.z"

# 4. Verify
make version-check
```

## 📝 Version File Formats

### version.json (Master)
```json
{
  "version": "MAJOR.MINOR.PATCH",
  "displayVersion": "vMAJOR.MINOR.PATCH",
  "description": "One-line description",
  "releaseDate": "YYYY-MM-DD",
  "releaseNotes": "Detailed changes for users",
  "author": "Team name"
}
```

### pyproject.toml
```toml
[project]
version = "MAJOR.MINOR.PATCH"
```

### package.json
```json
{
  "version": "MAJOR.MINOR.PATCH",
  ...
}
```

## 🚀 Automation Scripts

### sync-version.py
- Reads from `version.json`
- Updates all other version files
- Validates consistency
- Provides colored terminal output

### bump-version.py
- Increments version based on type
- Updates `version.json` with new version
- Sets release date to today
- Calls sync-version.py automatically
- Provides next-step instructions

## 💡 Tips

1. **Always use the Make commands** - Don't edit version files manually except `version.json`
2. **Check before pushing** - Run `make version-check` as part of your pre-push routine
3. **Document changes** - Update both version.json and CHANGELOG.md
4. **Tag releases** - Create git tags for all production releases
5. **Use pre-commit hook** - Enable it to catch issues early

## 🔗 Related Documentation

- [CHANGELOG.md](claude/CHANGELOG.md) - Detailed version history
- [Release Process](release-process.md) - Full release workflow
- [CI/CD Pipeline](ci-cd.md) - Automated deployment process