"""Modern Intelligence Briefing PDF Generator.

This module generates beautiful intelligence briefing PDFs using a modern workflow:
1. Takes briefing data from intelligence briefing generator
2. Load Markdown template and inject briefing summary
3. Generate professional report content via first OpenAI model
4. Convert Markdown → HTML → PDF using WeasyPrint
5. Apply modern business styling with embedded CSS
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Dependencies for modern workflow
import markdown2
from weasyprint import HTML

# Import model configuration and logging
from .model_config import get_provider_models
from .logging_utils import get_logger

logger = get_logger(__name__)


class IntelligenceBriefingPDF:
    """Generate modern intelligence briefing PDF reports using LLM + WeasyPrint workflow."""
    
    def __init__(self, output_dir: str = "briefings"):
        """Initialize briefing PDF generator with modern workflow."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Load Markdown template
        self.template_path = Path(__file__).parent.parent.parent / "templates" / "briefings" / "intelligence_briefing_1.txt"
        self.template_content = self._load_template()
        
        # Load summarization template
        self.summarization_template_path = Path(__file__).parent.parent.parent / "templates" / "briefings" / "summarize_for_briefing_1.txt"
        self.summarization_template_content = self._load_summarization_template()
        
        logger.info("✅ Intelligence Briefing PDF generator initialized with modern workflow")
    
    def _load_template(self) -> str:
        """Load the Markdown template from file."""
        if not self.template_path.exists():
            raise FileNotFoundError(f"❌ Template file not found: {self.template_path}")
        
        with open(self.template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"✅ Loaded briefing template from {self.template_path.name}")
        return content
    
    def _load_summarization_template(self) -> str:
        """Load the summarization template from file."""
        if not self.summarization_template_path.exists():
            raise FileNotFoundError(f"❌ Summarization template file not found: {self.summarization_template_path}")
        
        with open(self.summarization_template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"✅ Loaded summarization template from {self.summarization_template_path.name}")
        return content
    
    
    def generate_briefing_pdf(self, briefing: Dict[str, Any]) -> str:
        """
        Generate modern intelligence briefing PDF using LLM + WeasyPrint workflow.
        
        Args:
            briefing: Complete briefing data from intelligence briefing generator
            
        Returns:
            Path to generated PDF file
        """
        logger.info(f"🚀 Starting modern briefing PDF generation for {briefing.get('client_name', 'unknown')}")
        
        # Step 1: Summarize briefing data
        briefing_summary = self._summarize_briefing_data(briefing)
        logger.info(f"📊 Briefing data summarized: {len(briefing_summary)} characters")
        
        # Step 2: Load template and inject briefing data
        prompt_content = self.template_content.replace("{CLIENT_SUMMARY}", briefing_summary)
        logger.info(f"📝 Template loaded and briefing data injected")
        
        # Step 3: Generate Markdown content using first OpenAI model
        markdown_content = self._generate_markdown_with_llm(prompt_content)
        
        logger.info(f"🤖 Markdown generated: {len(markdown_content)} characters")
        
        # Step 4: Convert Markdown to HTML
        html_content = self._convert_markdown_to_html(markdown_content, briefing)
        logger.info(f"🌐 HTML converted: {len(html_content)} characters")
        
        # Step 5: Generate PDF using WeasyPrint
        pdf_path = self._generate_pdf_from_html(html_content, briefing)
        logger.info(f"📄 Briefing PDF generated: {pdf_path}")
        
        return pdf_path
    
    def _summarize_briefing_data(self, briefing: Dict[str, Any]) -> str:
        """Summarize briefing data using LLM and summarization template."""
        logger.info("📊 Starting LLM-powered briefing data summarization")
        
        # Convert briefing data to JSON string for the LLM
        import json
        briefing_json = json.dumps(briefing, indent=2, default=str)
        
        # Create prompt using the summarization template
        prompt_content = f"{self.summarization_template_content}\n\n## Input Data:\n{briefing_json}"
        
        # Generate structured summary using LLM
        structured_summary = self._generate_summary_with_llm(prompt_content)
        
        if not structured_summary:
            raise Exception("LLM failed to generate briefing summary")
        
        logger.info(f"✅ LLM generated structured summary: {len(structured_summary)} characters")
        return structured_summary
    
    def _generate_summary_with_llm(self, prompt_content: str) -> str:
        """Generate briefing summary using first OpenAI model from models.yaml."""
        # Always use OpenAI with the FIRST model listed in models.yaml
        provider = "openai"
        
        # Get first OpenAI model from models.yaml (where you keep the best model)
        openai_models = get_provider_models("openai")
        if not openai_models:
            raise Exception("No OpenAI models configured in models.yaml")
        
        # Use the first model in the list (ordered in models.yaml)
        model_key = list(openai_models.keys())[0]
        model_name = openai_models[model_key]
        
        logger.info(f"📊 Briefing data summarization using first OpenAI model: {model_key} → {model_name}")
        
        # Use MultiProviderLLM for consistency
        from .llm_providers import MultiProviderLLM
        llm = MultiProviderLLM()
        
        # Execute with the first OpenAI model
        config = {
            "model": model_key,
            "temperature": 0.2,  # Lower temperature for structured data extraction
            "max_tokens": 2048
        }
        
        logger.info(f"🤖 Generating briefing summary with {provider} {model_key}...")
        
        # Short system prompt for data extraction
        system_prompt = "You are a data extraction engine. Extract and structure the briefing data exactly as requested. Output only the requested format without explanations."
        
        # Combine system and user prompts into single prompt for execute_research
        combined_prompt = f"{system_prompt}\n\n{prompt_content}"
        
        # Execute using MultiProviderLLM
        import asyncio
        result = asyncio.run(llm.execute_research(
            prompt=combined_prompt,
            provider=provider,
            config=config
        ))
        
        # Extract content
        if result["status"] == "success":
            summary_content = result.get("raw_response", "")
            if summary_content:
                logger.info(f"✅ LLM generated briefing summary: {len(summary_content)} characters")
                return summary_content.strip()
        
        raise Exception(f"LLM summary generation failed: {result.get('error', 'Unknown error')}")
    
    
    def _generate_markdown_with_llm(self, prompt_content: str) -> str:
        """Generate Markdown content using first OpenAI model from models.yaml."""
        # Always use OpenAI with the FIRST model listed in models.yaml
        provider = "openai"

        # Get first OpenAI model from models.yaml (where you keep the best model)
        openai_models = get_provider_models("openai")
        if not openai_models:
            raise Exception("No OpenAI models configured in models.yaml")

        # Use the first model in the list (ordered in models.yaml)
        model_key = list(openai_models.keys())[0]
        model_name = openai_models[model_key]

        logger.info(f"📄 Briefing PDF generation using first OpenAI model: {model_key} → {model_name}")

        # Use MultiProviderLLM for consistency
        from .llm_providers import MultiProviderLLM
        llm = MultiProviderLLM()

        # Execute with the first OpenAI model
        config = {
            "model": model_key,
            "temperature": 0.4,
            "max_tokens": 4096
        }

        logger.info(f"🤖 Generating briefing PDF content with {provider} {model_key}...")

        # Short system prompt specifying output rules only
        system_prompt = (
            "You are an expert business analyst and designer. Output only visually impressive Markdown with embedded CSS as needed for PDF/HTML export. "
            "No explanations, no comments, no extra text—just the final report."
        )

        # Combine system and user prompts into single prompt for execute_research
        combined_prompt = f"{system_prompt}\n\n{prompt_content}"

        import asyncio
        result = asyncio.run(llm.execute_research(
            prompt=combined_prompt,
            provider=provider,
            config=config
        ))

        # Extract content
        if result["status"] == "success":
            markdown_content = result.get("raw_response", "")
            if markdown_content:
                logger.info(f"✅ LLM generated {len(markdown_content)} characters of Markdown for briefing")
                return markdown_content.strip()

        raise Exception(f"LLM execution failed: {result.get('error', 'Unknown error')}")
    
    def _convert_markdown_to_html(self, markdown_content: str, briefing: Dict[str, Any]) -> str:
        """Convert Markdown to HTML with minimal HTML structure (no embedded CSS or styling)."""
        # Convert Markdown to HTML
        html_body = markdown2.markdown(
            markdown_content,
            extras=['tables', 'fenced-code-blocks', 'header-ids']
        )
        client_name = briefing.get('client_name', 'Unknown').replace('_', ' ').title()
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Intelligence Briefing - {client_name}</title>
</head>
<body>
{html_body}
</body>
</html>"""
        return html_content
    
    def _generate_pdf_from_html(self, html_content: str, briefing: Dict[str, Any]) -> str:
        """Generate PDF from HTML using WeasyPrint."""
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        client_name = briefing.get('client_name', 'unknown')
        filename = f"intelligence-briefing-{timestamp}-{client_name}.pdf"
        filepath = self.output_dir / filename
        
        logger.info(f"📄 Generating briefing PDF with WeasyPrint: {filename}")
        
        # Generate PDF using WeasyPrint
        html_doc = HTML(string=html_content)
        html_doc.write_pdf(str(filepath))
        
        # Verify file was created
        if not filepath.exists() or filepath.stat().st_size == 0:
            raise Exception("PDF file was not created or is empty")
        
        logger.info(f"✅ Briefing PDF successfully generated: {filepath}")
        return str(filepath)