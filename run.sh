#!/bin/bash
# Document to Slides POC - Run Script

echo "🚀 Starting Document to Slides POC"
echo "=================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Set environment variables (update these with your actual values)
export DATABASE_URL="sqlite:///app.db"  # or your database URL
export JWT_SECRET="your-jwt-secret-here"
# export OPENAI_API_KEY="your-openai-key-here"  # Uncomment and add your key
# export LLMWHISPERER_API_KEY="your-llm-whisperer-key"  # For PDF processing

echo "🌐 Starting server..."
echo "📋 Web interface will be available at: http://localhost:5000/static/presentation.html"
echo "🔍 Health check: http://localhost:5000/health"
echo "📊 Preview API: http://localhost:5000/api/generate-slides/preview"

cd api
python generate_slides.py