#!/usr/bin/env python3
"""
Test script to verify the Document to Slides POC setup
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔍 Testing Document to Slides POC Setup")
print("=" * 50)

# Test 1: Check Python version
print(f"✓ Python version: {sys.version.split()[0]}")

# Test 2: Check required modules
required_modules = [
    'flask', 'requests', 'openai', 'openpyxl', 
    'pandas', 'pptx', 'docx', 'dotenv'
]

missing_modules = []
for module in required_modules:
    try:
        __import__(module)
        print(f"✓ Module '{module}' is installed")
    except ImportError:
        print(f"✗ Module '{module}' is NOT installed")
        missing_modules.append(module)

# Test 3: Check environment variables
print("\n" + "=" * 50)
print("Environment Variables:")

env_vars = {
    'LLMWHISPERER_API_KEY': 'LLMWhisperer API',
    'LLMWHISPERER_BASE_URL': 'LLMWhisperer Base URL',
    'OPENAI_API_KEY': 'OpenAI API',
    'PORT': 'Server Port'
}

for var, name in env_vars.items():
    value = os.getenv(var)
    if value:
        if 'KEY' in var:
            # Mask API keys for security
            masked = value[:10] + '...' + value[-4:] if len(value) > 14 else '***'
            print(f"✓ {name}: {masked}")
        else:
            print(f"✓ {name}: {value}")
    else:
        print(f"✗ {name}: NOT SET")

# Test 4: Check file structure
print("\n" + "=" * 50)
print("File Structure:")

required_files = [
    'api/generate_slides.py',
    'lib/pdf_extractor.py',
    'lib/excel_extractor.py',
    'lib/word_extractor.py',
    'lib/slide_generator.py',
    'static/presentation.html',
    '.env',
    '.env.example'
]

for file in required_files:
    if os.path.exists(file):
        print(f"✓ {file} exists")
    else:
        print(f"✗ {file} NOT FOUND")

# Summary
print("\n" + "=" * 50)
if missing_modules:
    print("⚠️  Some modules are missing. Run: pip install -r requirements.txt")
else:
    print("✅ All required modules are installed")

if os.getenv('LLMWHISPERER_API_KEY') and os.getenv('OPENAI_API_KEY'):
    print("✅ API keys are configured")
else:
    print("⚠️  Some API keys are missing. Check your .env file")

print("\n🚀 To start the server, run: python start_server.py")
print("=" * 50)