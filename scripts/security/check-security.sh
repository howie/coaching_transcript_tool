#!/bin/bash

# Security check script to ensure no sensitive files are committed
# Run this before committing changes

echo "🔒 Running security checks..."

# Check for service account key files
if find . -name "coaching-storage-*.json" -o -name "*service-account*.json" -o -name "*credentials*.json" | grep -v node_modules; then
    echo "❌ SECURITY ALERT: Service account key files found!"
    echo "These files contain sensitive credentials and should NEVER be committed."
    echo "Please remove them or add to .gitignore"
    exit 1
fi

# Check for .env files with real values
if find . -name ".env" -not -name ".env.example" | grep -v node_modules; then
    echo "⚠️  WARNING: .env files found (they should be in .gitignore)"
fi

# Check for potential secrets in staged files
if git diff --cached --name-only | xargs grep -l "GOOGLE_APPLICATION_CREDENTIALS_JSON\|base64.*=" 2>/dev/null; then
    echo "❌ SECURITY ALERT: Potential secrets found in staged files!"
    echo "Please review and remove any hardcoded credentials"
    exit 1
fi

# Check for hardcoded API keys or tokens
if git diff --cached | grep -i "api.key\|secret.*=\|token.*=\|password.*=" | grep -v "example\|template\|placeholder"; then
    echo "❌ SECURITY ALERT: Potential hardcoded secrets found!"
    echo "Please review and remove any hardcoded credentials"
    exit 1
fi

echo "✅ Security checks passed!"
echo "Safe to commit."