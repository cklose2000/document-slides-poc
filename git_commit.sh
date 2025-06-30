#!/bin/bash

# Script to commit and push changes to GitHub
# This script ensures API keys in .env are not committed

echo "🔍 Checking git status..."

# Initialize git if needed
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    git remote add origin https://github.com/cklose2000/document-slides-poc.git
fi

# Check if .env is properly ignored
if ! grep -q "^\.env$" .gitignore 2>/dev/null; then
    echo "⚠️  WARNING: .env is not in .gitignore!"
    exit 1
fi

echo "✅ .env is properly ignored"

# Stage all changes except .env
git add -A
git reset .env

echo "📋 Files to be committed:"
git status --short

echo ""
echo "📝 Creating commit..."
git commit -m "Add LLMWhisperer PDF extraction and update documentation

- Implemented PDF extraction using LLMWhisperer v2 API
- Added support for OCR, table detection, and section recognition
- Updated requirements.txt with llmwhisperer-client
- Created comprehensive .env.example with all configuration options
- Updated README.md with complete setup instructions and tech stack
- Modified API endpoints to use new PDF extractor
- Added environment variable configuration with python-dotenv
- Enhanced error handling and fallback mechanisms"

echo ""
echo "🚀 Pushing to GitHub..."
git branch -M main
git push -u origin main

echo ""
echo "✅ Successfully committed and pushed to GitHub!"
echo "🔒 API keys in .env were NOT committed"