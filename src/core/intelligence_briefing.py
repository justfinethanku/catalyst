"""
Intelligence Briefing Generator for comprehensive client synthesis.

Model names loaded from src/config/models.yaml - no hardcoded model names.
Follows OpenAI Chat Completions API: https://platform.openai.com/docs/api-reference/chat
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from .llm_providers import MultiProviderLLM
from .model_config import get_provider_models
from ..storage import HybridStore
from .logging_utils import get_logger, log_exceptions


logger = get_logger(__name__)


class IntelligenceBriefingGenerator:
    """Generate comprehensive intelligence briefings from all stored client data."""
    
    def __init__(self, storage: HybridStore, llm_provider: Optional[MultiProviderLLM] = None):
        """Initialize briefing generator."""
        self.storage = storage
        self.llm = llm_provider or MultiProviderLLM()
    
    @log_exceptions
    async def generate_briefing(self, 
                               client_name: str,
                               provider: str = "openai",
                               model: str = None) -> Dict[str, Any]:
        """
        Generate comprehensive intelligence briefing for a client.
        
        Args:
            client_name: Client to generate briefing for
            provider: LLM provider to use
            model: Model key from models.yaml
            
        Returns:
            Complete briefing with synthesis, insights, and recommendations
        """
        try:
            # Use default model if none provided, validate it exists in config
            if model is None:
                available_models = get_provider_models(provider)
                model = "gpt-4.1" if "gpt-4.1" in available_models else list(available_models.keys())[0]
                logger.info("Using default model: %s (from models.yaml)", model)
            
            logger.info(f"🧠 Generating Intelligence Briefing for {client_name}")
            
            # 1. Gather all client data
            client_data = await self._gather_client_data(client_name)
            
            if not client_data:
                return {
                    "status": "error",
                    "error": f"No data found for client: {client_name}",
                    "briefing": {}
                }
            
            logger.info(f"📊 Found {len(client_data)} data points")
            
            # 2. Organize data by analysis type
            organized_data = self._organize_data_by_step(client_data)
            
            # 3. Generate synthesis prompt
            synthesis_prompt = self._build_synthesis_prompt(client_name, organized_data)
            
            logger.info(f"🤖 Sending to {provider} for synthesis...")
            
            # 4. Execute LLM synthesis using Chat Completions API
            # Model name loaded from models.yaml, not hardcoded
            config = {
                "model": model,  # Config key, actual model name loaded from models.yaml
                "enable_thinking": True,
                "enable_web_search": False,  # Use stored data only
                "temperature": 0.3,
                "max_tokens": 8000
            }
            
            result = await self.llm.execute_research(
                prompt=synthesis_prompt,
                provider=provider,
                config=config
            )
            
            if result["status"] != "success":
                return {
                    "status": "error",
                    "error": f"LLM synthesis failed: {result.get('error')}",
                    "briefing": {}
                }
            
            logger.info(f"✅ Briefing generated successfully")
            
            # 5. Structure the briefing response
            briefing = {
                "client_name": client_name,
                "generated_at": datetime.now().isoformat(),
                "provider": provider,
                "model": model,  # Model key from models.yaml
                "data_points_analyzed": len(client_data),
                "analysis_steps_covered": list(organized_data.keys()),
                "synthesis": result["raw_response"],
                "thinking_process": result.get("thinking", ""),
                "has_thinking": result.get("has_thinking", False),
                "raw_data_summary": self._create_data_summary(organized_data)
            }
            
            # 6. Store the briefing for future reference
            await self._store_briefing(briefing)
            
            return {
                "status": "success",
                "briefing": briefing
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "briefing": {}
            }
    
    async def _gather_client_data(self, client_name: str) -> List[Dict[str, Any]]:
        """Gather all stored data for a client."""
        # Get all data for this client (search with empty query to get everything)
        client_data = self.storage.search(
            query="",
            filter_client=client_name,
            n_results=50  # Get comprehensive data
        )
        
        return client_data
    
    def _organize_data_by_step(self, client_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Organize client data by analysis step."""
        organized = {}
        
        for item in client_data:
            step = item['metadata'].get('step', 'unknown')
            if step not in organized:
                organized[step] = []
            organized[step].append(item)
        
        return organized
    
    def _build_synthesis_prompt(self, client_name: str, organized_data: Dict[str, List[Dict[str, Any]]]) -> str:
        """Build the comprehensive synthesis prompt."""
        
        # Build data sections
        data_sections = []
        
        for step, items in organized_data.items():
            section_content = []
            for item in items:
                section_content.append(item["content"])
            
            data_sections.append(f"""
## {step.replace('_', ' ').title()} Analysis

{chr(10).join(section_content)}
""")
        
        # Build the comprehensive prompt
        prompt = f"""
You are conducting a STRATEGIC INTELLIGENCE BRIEFING for {client_name.replace('_', ' ').title()}.

Your task is to synthesize ALL the research data below into a comprehensive intelligence briefing that provides actionable strategic insights.

## ANALYTICAL APPROACH

Take time to think through:
- What are the most significant strategic insights across all this data?
- What patterns, opportunities, and risks emerge when you connect findings across different analysis areas?
- What strategic recommendations would be most valuable for stakeholders?
- How does this company compare to patterns you see in the market?

## YOUR INTELLIGENCE BRIEFING

Structure your response as a comprehensive briefing covering:

### EXECUTIVE OVERVIEW
• High-level strategic position and key findings (2-3 paragraphs)
• Most critical insights that leadership needs to know

### STRATEGIC INTELLIGENCE SUMMARY
• **Business Model & Market Position**: Core strategy and competitive positioning
• **Key Differentiators**: What makes this company unique and defensible
• **Target Market & Customer Base**: Who they serve and how effectively
• **Competitive Landscape**: Key competitors and market dynamics
• **Growth Trajectory**: Indicators of momentum and expansion potential

### STRATEGIC OPPORTUNITIES & RISKS
• **High-Impact Opportunities**: Top 3-4 growth levers or strategic moves
• **Key Risk Factors**: Top 3-4 vulnerabilities or challenges
• **Market White Spaces**: Underexplored areas they could exploit

### ACTIONABLE RECOMMENDATIONS
• **Immediate Actions** (0-6 months): Quick wins and urgent priorities
• **Medium-term Strategy** (6-18 months): Key strategic initiatives
• **Long-term Vision** (18+ months): Transformational opportunities

### INTELLIGENCE QUALITY ASSESSMENT
• Data confidence level and any analytical limitations
• Areas where additional intelligence would be valuable

Focus on insights that are:
- **Strategic**: Move beyond surface-level facts to strategic implications
- **Actionable**: Provide clear direction for decision-making
- **Evidence-based**: Ground recommendations in the analyzed data
- **Comprehensive**: Connect insights across all analysis areas

## SOURCE DATA FOR SYNTHESIS

{chr(10).join(data_sections)}

Generate a briefing that transforms this raw intelligence into strategic value.
"""
        
        return prompt
    
    def _create_data_summary(self, organized_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Create summary of the raw data analyzed."""
        summary = {
            "total_steps": len(organized_data),
            "steps_analyzed": list(organized_data.keys()),
            "total_content_length": 0,
            "step_details": {}
        }
        
        for step, items in organized_data.items():
            total_length = sum(len(item["content"]) for item in items)
            summary["total_content_length"] += total_length
            summary["step_details"][step] = {
                "items_count": len(items),
                "content_length": total_length
            }
        
        return summary
    
    @log_exceptions
    async def _store_briefing(self, briefing: Dict[str, Any]) -> None:
        """Store the briefing for future reference."""
        try:
            # Create a summary for storage
            storage_content = f"""
INTELLIGENCE BRIEFING: {briefing['client_name'].replace('_', ' ').title()}
Generated: {briefing['generated_at']}

{briefing['synthesis']}

---
Data Points Analyzed: {briefing['data_points_analyzed']}
Analysis Steps: {', '.join(briefing['analysis_steps_covered'])}
"""
            
            self.storage.store(
                content=storage_content,
                metadata={
                    "client": briefing['client_name'],
                    "type": "intelligence_briefing",
                    "generated_at": briefing['generated_at'],
                    "provider": briefing['provider'],
                    "model": briefing['model'],
                    "data_points": briefing['data_points_analyzed'],
                    "steps_covered": len(briefing['analysis_steps_covered'])
                },
                client_name=briefing['client_name']
            )
            
            logger.info(f"💾 Briefing stored for future reference")
            
        except Exception as e:
            logger.warning(f"⚠️  Warning: Failed to store briefing: {e}")
    
    def get_available_clients(self) -> List[str]:
        """Get list of clients with available data."""
        return self.storage.get_all_clients()
    
    @log_exceptions
    async def list_previous_briefings(self, client_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """List previously generated briefings."""
        query = "intelligence_briefing"
        filter_client = client_name if client_name else None
        
        briefings = self.storage.search(
            query=query,
            filter_client=filter_client,
            n_results=20
        )
        
        # Extract briefing metadata
        briefing_list = []
        for item in briefings:
            if item['metadata'].get('type') == 'intelligence_briefing':
                briefing_list.append({
                    "client": item['metadata'].get('client'),
                    "generated_at": item['metadata'].get('generated_at'),
                    "provider": item['metadata'].get('provider'),
                    "model": item['metadata'].get('model'),
                    "data_points": item['metadata'].get('data_points'),
                    "steps_covered": item['metadata'].get('steps_covered')
                })
        
        return briefing_list