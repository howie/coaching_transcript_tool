#!/bin/bash

echo "🔒 Security Fix: Removing .claude/settings.local.json from all branches"
echo ""

BRANCHES=("feature-ai-coach" "feature/improve-assembly-with-lemur" "feature/payment" "hotfix/ecpay" "main")
CURRENT_BRANCH=$(git branch --show-current)

for branch in "${BRANCHES[@]}"; do
  echo "=== Processing branch: $branch ==="
  
  # Checkout branch
  git checkout "$branch"
  
  # Check if file exists
  if git ls-files | grep -q ".claude/settings.local.json"; then
    echo "⚠️  Removing .claude/settings.local.json from $branch"
    
    # Remove from git tracking
    git rm --cached .claude/settings.local.json
    
    # Update gitignore if not already present
    if ! grep -q ".claude/settings.local.json" .gitignore; then
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

# Return to original branch
git checkout "$CURRENT_BRANCH"

echo "🎉 Security fix completed for all branches!"
echo ""
echo "⚠️  IMPORTANT: You should also:"
echo "1. Rotate the database password immediately"
echo "2. Update all production environment variables"
echo "3. Review access logs for potential unauthorized access"

