"""
Context synthesis system using OpenAI models for focused, sub-1k token summaries.

Model names loaded from src/config/models.yaml - no hardcoded model names.
Follows OpenAI Chat Completions API: https://platform.openai.com/docs/api-reference/chat
"""
import asyncio
from typing import List, Dict, Any, Optional
from .llm_providers import OpenAIProvider
from .logging_utils import get_logger, log_exceptions


logger = get_logger(__name__)


class ContextSynthesizer:
    """Synthesizes multiple chunks into focused, sub-1000 token context using OpenAI models."""
    
    def __init__(self, openai_provider: OpenAIProvider):
        """Initialize with OpenAI provider - model names loaded from models.yaml."""
        self.llm = openai_provider
        self.max_output_tokens = 950  # Buffer under 1000 token limit
        self.model_key = "gpt-4.1-nano"  # Config key, actual model name from models.yaml
        
        # Load synthesis template
        from pathlib import Path
        self.template_path = Path(__file__).parent.parent.parent / "templates" / "context_synthesizer" / "context_synthesizer_1.txt"
        self.template_content = self._load_template()
    
    def _load_template(self) -> str:
        """Load the synthesis template from file."""
        if not self.template_path.exists():
            raise FileNotFoundError(f"❌ Context synthesis template not found: {self.template_path}")
        
        with open(self.template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"✅ Loaded context synthesis template from {self.template_path.name}")
        return content
    
    @log_exceptions
    async def synthesize_context(self, 
                                chunks: List[str], 
                                step_id: str, 
                                query: str,
                                client_name: str) -> str:
        """
        Synthesize multiple chunks into focused context for step execution.
        
        Args:
            chunks: List of retrieved chunks (up to 500 tokens each)
            step_id: Current step ID for context-aware synthesis
            query: Original search query for relevance
            client_name: Client name for context
            
        Returns:
            Synthesized context under 1000 tokens
        """
        if not chunks:
            return ""
        
        # Count input tokens
        total_input_tokens = sum(self._count_tokens(chunk) for chunk in chunks)
        logger.info(f"🧠 Synthesizing {len(chunks)} chunks ({total_input_tokens} tokens) → <1000 tokens")
        
        # Get step-specific synthesis prompt
        synthesis_prompt = self._get_synthesis_prompt(step_id, chunks, query, client_name)
        
        # Execute synthesis using OpenAI Chat Completions API
        # Model name loaded from models.yaml, not hardcoded
        result = await self.llm.execute_research(
            prompt=synthesis_prompt,
            config={
                "model": self.model_key,  # Config key, actual model name from models.yaml
                "max_tokens": self.max_output_tokens
            }
        )
        
        if result["status"] != "success":
            raise Exception(f"Context synthesis failed: {result.get('error')}")
        
        synthesized_context = result["raw_response"].strip()
        
        # Validate output length
        output_tokens = self._count_tokens(synthesized_context)
        if output_tokens > 1000:
            logger.warning(f"⚠️  Synthesis exceeded 1000 tokens ({output_tokens}), truncating...")
            synthesized_context = self._truncate_to_limit(synthesized_context, 1000)
            output_tokens = self._count_tokens(synthesized_context)
        
        logger.info(f"✅ Synthesis complete: {output_tokens} tokens ({len(chunks)} chunks → focused summary)")
        
        return synthesized_context
    
    def _get_synthesis_prompt(self, 
                             step_id: str, 
                             chunks: List[str], 
                             query: str,
                             client_name: str) -> str:
        """Generate step-specific synthesis prompt using external template."""
        
        # Combine chunks with separators (preserve original logic)
        chunks_text = "\n\n--- CHUNK ---\n\n".join(chunks)
        
        # Get step-specific instructions (preserve original logic)
        step_instructions = self._get_step_instructions(step_id)
        
        # Format client and step names (preserve original logic)
        formatted_client_name = client_name.replace('_', ' ').title()
        formatted_step_name = step_id.replace('_', ' ')
        
        # Substitute template variables
        prompt = self.template_content.format(
            CLIENT_NAME=formatted_client_name,
            STEP_NAME=formatted_step_name,
            STEP_INSTRUCTIONS=step_instructions,
            QUERY=query,
            CHUNKS_TEXT=chunks_text
        )
        
        return prompt
    
    def _get_step_instructions(self, step_id: str) -> str:
        """Get specific synthesis instructions for each step type."""
        
        instructions = {
            "discovery": "Focus on company fundamentals: business model, core products/services, key value propositions, and basic market context. Synthesize into a clear company profile.",
            
            "market_position": "Extract competitive positioning, market differentiation, industry dynamics, and strategic advantages. Create a focused view of how this company competes.",
            
            "audience_insights": "Identify target customer segments, user personas, customer needs, and usage patterns. Synthesize into clear audience understanding.",
            
            "competitive_landscape": "Map out direct competitors, alternative solutions, competitive threats, and market opportunities. Focus on competitive intelligence.",
            
            "strategic_synthesis": "Pull together strategic insights, growth opportunities, key challenges, and actionable recommendations. Create executive-level strategic overview."
        }
        
        return instructions.get(step_id, f"Synthesize key insights relevant to {step_id.replace('_', ' ')} analysis.")
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        try:
            import tiktoken
            encoder = tiktoken.get_encoding("cl100k_base")
            return len(encoder.encode(text))
        except Exception:
            # Fallback estimation
            return len(text) // 4
    
    def _truncate_to_limit(self, text: str, max_tokens: int) -> str:
        """Truncate text to stay under token limit."""
        try:
            import tiktoken
            encoder = tiktoken.get_encoding("cl100k_base")
            tokens = encoder.encode(text)
            
            if len(tokens) <= max_tokens:
                return text
            
            # Truncate and decode
            truncated_tokens = tokens[:max_tokens-10]  # Small buffer
            return encoder.decode(truncated_tokens) + "..."
            
        except Exception:
            # Fallback: character-based truncation
            estimated_chars = max_tokens * 4  # Rough estimation
            return text[:estimated_chars] + "..."
    
    @log_exceptions
    async def synthesize_dependency_context(self,
                                          dependency_chunks: Dict[str, List[str]],
                                          step_id: str,
                                          client_name: str) -> Dict[str, str]:
        """
        Synthesize context for multiple dependencies.
        
        Args:
            dependency_chunks: Dict of {dep_id: [chunks]} 
            step_id: Current step ID
            client_name: Client name
            
        Returns:
            Dict of {dep_id: synthesized_context}
        """
        synthesized_deps = {}
        
        for dep_id, chunks in dependency_chunks.items():
            if chunks:
                query = f"{dep_id} insights for {step_id}"
                synthesized = await self.synthesize_context(
                    chunks=chunks,
                    step_id=dep_id,  # Use dependency ID for focused synthesis
                    query=query,
                    client_name=client_name
                )
                
                if synthesized:
                    synthesized_deps[f"{dep_id}_insights"] = synthesized
        
        return synthesized_deps