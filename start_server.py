#!/usr/bin/env python3
"""
Simple launcher for the Document to Slides POC
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Get port from environment or use default
port = int(os.getenv('PORT', 5001))

print("🚀 Starting Document to Slides POC")
print("=" * 50)

# Check for API keys
if os.getenv('LLMWHISPERER_API_KEY'):
    print("✅ LLMWhisperer API Key configured")
else:
    print("⚠️  LLMWhisperer API Key not set (PDF extraction will be limited)")

if os.getenv('OPENAI_API_KEY'):
    print("✅ OpenAI API Key configured")
else:
    print("⚠️  OpenAI API Key not set (AI analysis will be disabled)")

print(f"📋 Web interface: http://localhost:{port}/static/presentation.html")
print(f"🔍 Health check: http://localhost:{port}/health")
print(f"📊 Preview API: http://localhost:{port}/api/generate-slides/preview")
print("=" * 50)

# Import and run the Flask app
if __name__ == "__main__":
    from api.generate_slides import app
    app.run(debug=True, host='0.0.0.0', port=port)