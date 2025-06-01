# Catalyst v1

AI-powered business intelligence system that autonomously analyzes companies and builds a cumulative knowledge base.

## What it does

- **5-step autonomous analysis**: Discovery → Market Position → Audience Insights → Competitive Landscape → Strategic Synthesis
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
# Create and edit your .env file in api_secrets/
# Edit api_secrets/.env and add:
# OPENAI_API_KEY=sk-...
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
- ChromaDB works out of the box for local use; no extra setup required unless customizing storage

## Architecture

- **ChromaDB**: Vector database for semantic search
- **OpenAI**: GPT-4 for analysis
- **Streamlit**: Web interface
- **WeasyPrint**: PDF generation

Built by Jonathan Edwards.