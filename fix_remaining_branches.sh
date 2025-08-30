#!/bin/bash

echo "🔒 Security Fix: Removing .claude/settings.local.json from remaining branches"
echo ""

BRANCHES=("feature-ai-coach" "feature/improve-assembly-with-lemur" "feature/payment" "hotfix/ecpay" "main")
CURRENT_BRANCH=$(git branch --show-current)

# Stash current changes to avoid conflicts
git stash push -u -m "Temporary stash for security fix"

for branch in "${BRANCHES[@]}"; do
  echo "=== Processing branch: $branch ==="
  
  # Checkout branch
  git checkout "$branch"
  
  # Check if file exists
  if git ls-files | grep -q ".claude/settings.local.json"; then
    echo "⚠️  Removing .claude/settings.local.json from $branch"
    
    # Remove from git tracking
    git rm .claude/settings.local.json
    
    # Update gitignore if not already present
    if ! grep -q ".claude/settings.local.json" .gitignore 2>/dev/null; then
      echo "" >> .gitignore
      echo "# Claude Code settings with sensitive data" >> .gitignore
      echo ".claude/settings.local.json" >> .gitignore
      git add .gitignore
    fi
    
    # Commit the security fix
    git commit -m "security: remove .claude/settings.local.json with database credentials

- Remove sensitive database credentials from version control  
- Add .claude/settings.local.json to .gitignore
- Prevent future accidental commits of sensitive data

🔒 Security fix for exposed database URL"
    
    echo "✅ Security fix applied to $branch"
  else
    echo "✅ No .claude/settings.local.json found in $branch"
  fi
  
  echo ""
done

# Return to original branch and restore stash
git checkout "$CURRENT_BRANCH"
git stash pop

echo "🎉 Security fix completed for all branches!"

