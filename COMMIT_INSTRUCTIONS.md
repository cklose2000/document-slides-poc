# Git Commit Instructions

## Option 1: Using Windows Command Prompt or PowerShell

1. Open Command Prompt or PowerShell
2. Navigate to the project directory:
   ```
   cd C:\Users\cklos\document-slides-poc
   ```

3. Run the commit script:
   ```
   commit_changes.bat
   ```

## Option 2: Manual Git Commands

If the batch file doesn't work, run these commands manually:

```bash
# Initialize git (if needed)
git init
git remote add origin https://github.com/cklose2000/document-slides-poc.git

# Add all files except .env
git add -A
git reset .env

# Verify .env is not staged
git status

# Commit changes
git commit -m "Add LLMWhisperer PDF extraction and update documentation

- Implemented PDF extraction using LLMWhisperer v2 API
- Added support for OCR, table detection, and section recognition
- Updated requirements.txt with llmwhisperer-client
- Created comprehensive .env.example with all configuration options
- Updated README.md with complete setup instructions and tech stack
- Modified API endpoints to use new PDF extractor
- Added environment variable configuration with python-dotenv
- Enhanced error handling and fallback mechanisms"

# Push to GitHub
git branch -M main
git push -u origin main
```

## Files Changed

### New Files:
- `lib/pdf_extractor.py` - LLMWhisperer PDF extraction implementation
- `.env.example` - Environment variables template
- `.env` - Local environment file (NOT committed)

### Modified Files:
- `requirements.txt` - Added llmwhisperer-client
- `api/generate_slides.py` - Updated to use new PDF extractor
- `start_server.py` - Updated to use python-dotenv
- `README.md` - Complete documentation update

## Important Notes

- The `.env` file contains your API keys and is properly ignored by git
- Always verify with `git status` that .env is not being committed
- The repository is configured to prevent accidental API key exposure