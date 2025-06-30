# Document to Slides POC

Transform data room documents (PDF, Excel, Word) into branded PowerPoint presentations with source attribution.

## Features

- 📄 **Multi-format Support**: PDF, Excel (.xlsx), Word (.docx)
- 🧠 **AI Analysis**: Extract key metrics and insights using OpenAI GPT
- 📊 **Source Attribution**: Track data back to specific cells/pages
- 🎯 **Professional Slides**: Generate branded PowerPoint presentations
- 🔍 **Preview Mode**: Test extraction without generating slides
- 📑 **Advanced PDF Processing**: LLMWhisperer for high-quality PDF extraction with OCR

## Tech Stack

- **Backend**: Python Flask
- **PDF Processing**: LLMWhisperer API (high-quality extraction with OCR support)
- **Excel Processing**: openpyxl with cell-level tracking
- **Word Processing**: python-docx
- **Slide Generation**: python-pptx
- **AI Analysis**: OpenAI GPT-4/GPT-3.5
- **Frontend**: HTML5 with drag-and-drop upload

## Quick Start

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/cklose2000/document-slides-poc.git
   cd document-slides-poc
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

4. **Run the Server**:
   ```bash
   python start_server.py
   ```

5. **Open Web Interface**:
   Visit: http://localhost:5001/static/presentation.html

## Configuration

Create a `.env` file with the following variables:

```env
# LLMWhisperer API Configuration
# Get your API key from: https://unstract.com/llmwhisperer
LLMWHISPERER_API_KEY=your_llmwhisperer_api_key_here

# OpenAI API Configuration
# Get your API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Server Configuration
PORT=5001
```

## File Structure

```
document-slides-poc/
├── lib/
│   ├── pdf_extractor.py       # LLMWhisperer PDF extraction
│   ├── excel_extractor.py     # Excel parsing with cell references
│   ├── word_extractor.py      # Word document structure extraction
│   ├── slide_generator.py     # PowerPoint generation
│   └── llm_slides.py         # AI document analysis
├── api/
│   └── generate_slides.py    # Flask API endpoints
├── static/
│   └── presentation.html     # Web interface
├── templates/
│   └── firm_template.pptx    # PowerPoint template (auto-created)
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
└── start_server.py          # Server startup script
```

## API Endpoints

- `POST /api/generate-slides` - Generate PowerPoint from documents
- `POST /api/generate-slides/preview` - Preview extraction results
- `GET /health` - Health check

## Usage

1. **Upload Documents**: Drag & drop or select PDF/Excel/Word files
2. **Preview Extraction**: Click "Preview Extraction" to see parsed data
3. **Generate Slides**: Click "Generate Slides" to create PowerPoint
4. **Download**: Save the generated presentation

## PDF Processing with LLMWhisperer

The POC uses LLMWhisperer for advanced PDF processing, which provides:

- **High-Quality Extraction**: Preserves document structure and formatting
- **OCR Support**: Handles scanned documents and images
- **Table Detection**: Automatically identifies and extracts tables
- **Section Recognition**: Identifies document sections and headers
- **Metrics Extraction**: Finds financial values, percentages, and KPIs

## Sample Slide Types

- **Financial Summary**: Key metrics with source attribution
- **Company Overview**: Business description and industry
- **Key Insights**: AI-extracted highlights
- **Data Tables**: Structured data from PDFs and Excel files

## Source Attribution

Each data point includes:
- Document name
- Sheet/page reference
- Specific cell/section location
- Table/paragraph context
- Extraction confidence

## Development

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export LLMWHISPERER_API_KEY="your-key"
export OPENAI_API_KEY="your-key"

# Run the development server
python start_server.py
```

### Testing with Sample Files

1. **PDF Files**: Financial reports, pitch decks, business plans
2. **Excel Files**: Financial models, data tables, metrics dashboards
3. **Word Files**: Executive summaries, market analyses, reports

## Development Roadmap

See [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md) for detailed sprint planning and milestones.

### MVP Sprint 1 (High Priority - Demo Critical)
- [Brand Template System](https://github.com/cklose2000/document-slides-poc/issues/2) - PowerPoint template matching
- [Enhanced Source Attribution](https://github.com/cklose2000/document-slides-poc/issues/3) - Document traceability  
- [Professional Slide Generation](https://github.com/cklose2000/document-slides-poc/issues/4) - Business-ready formatting

### MVP Sprint 2 (Enterprise Features)
- [Security & Data Handling](https://github.com/cklose2000/document-slides-poc/issues/5) - Enterprise protection
- [Cost Optimization](https://github.com/cklose2000/document-slides-poc/issues/6) - Smart model usage
- [Advanced Document Processing](https://github.com/cklose2000/document-slides-poc/issues/7) - Financial precision

### MVP Sprint 3 (Production Polish)
- [Professional Dashboard](https://github.com/cklose2000/document-slides-poc/issues/8) - Business UI
- [Batch Processing](https://github.com/cklose2000/document-slides-poc/issues/9) - Multi-document workflow
- [Production Architecture](https://github.com/cklose2000/document-slides-poc/issues/10) - Scalable deployment

## Troubleshooting

### Common Issues

1. **LLMWhisperer API Errors**:
   - Verify API key is correct
   - Check API usage limits
   - Ensure PDF file size is within limits

2. **OpenAI API Errors**:
   - Verify API key is set
   - Check rate limits
   - Fallback to simple extraction works without API

3. **File Processing Errors**:
   - Ensure files are not corrupted
   - Check file permissions
   - Verify file format is supported

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines, coding standards, and contribution workflow.

### Quick Start for Contributors
1. Check [GitHub Issues](https://github.com/cklose2000/document-slides-poc/issues) for available tasks
2. Focus on `demo-critical` and `high-priority` labels first
3. Follow the development workflow in CONTRIBUTING.md
4. Submit PRs with tests and documentation

---

**Status**: Foundation Complete ✅ - Ready for MVP Development

**Next Milestone**: Demo-Ready MVP (2 weeks) - Issues #2, #3, #4