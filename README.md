# Catalyst v1

AI-powered business intelligence system that autonomously analyzes companies and builds a cumulative knowledge base.

## What it does

- **5-step autonomous analysis**: Discovery → Market Position → Audience Insights → Competitive Landscape → Strategic Synthesis
- **Live web research**: Automatic web search for current market data and company information
- **Cumulative intelligence**: Each analysis makes the system smarter for future companies
- **PDF reports**: Professional intelligence briefings
- **Vector search**: Find patterns across all analyzed companies

## Quick Start

1. **Install**
```bash
git clone <repo>
cd catalyst
python -m venv catalyst_env
source catalyst_env/bin/activate
pip install -r requirements.txt
```

2. **Configure API keys**
```bash
# Edit api_secrets/.env and add:
# OPENAI_API_KEY=sk-...
# BRAVE_API_KEY removed - now using Gemini native research
```

3. **Run**
```bash
# Web interface:
streamlit run src/ui/autonomous_app.py
```

4. **Use**
- Enter company URL and name
- Hit START
- Download PDF report when done

## Requirements

- Python 3.10+
- OpenAI API key
- Google Gemini API key (for enhanced research capabilities)
- ChromaDB works out of the box for local use; no extra setup required unless customizing storage

## Key Features

### Automatic Web Search
- **Gemini Research Integration**: Enhanced research capabilities using Google Gemini
- **GPT-4.1 models**: Automatically enabled for live data access
- **Research steps**: Discovery, market position, and competitive analysis use real-time web data
- **No configuration**: Works out of the box with intelligent defaults (API key required)
- **Manual control**: Override automatic behavior when needed

## Architecture

- **ChromaDB**: Vector database for semantic search
- **OpenAI GPT-4.1**: Advanced analysis with automatic web search tools
- **Streamlit**: Web interface
- **WeasyPrint**: PDF generation

Built by Jonathan Edwards.