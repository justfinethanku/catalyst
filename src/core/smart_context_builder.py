"""Smart context builder using chunked retrieval with synthesis."""
from typing import Dict, Any, List, Optional
from .parallel_storage import ParallelStorageManager
from .pipeline.config_loader import StepConfig
from .pipeline.context_builder import PipelineContext
from .context_synthesizer import ContextSynthesizer
from .llm_providers import OpenAIProvider
from .logging_utils import get_logger, log_exceptions


logger = get_logger(__name__)


class SmartContextBuilder:
    """Context builder with smart chunked retrieval and synthesis."""
    
    def __init__(self, parallel_storage: ParallelStorageManager, openai_provider: OpenAIProvider):
        """Initialize with parallel storage manager and synthesis capability."""
        self.storage = parallel_storage
        self.synthesizer = ContextSynthesizer(openai_provider)
        self.max_context_tokens = 3000  # Hard limit to prevent rate limiting
    
    @log_exceptions
    async def build_smart_step_context(self,
                                     step: StepConfig,
                                     pipeline_context: PipelineContext,
                                     config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build smart context for step execution.
        
        Uses chunked retrieval when available, falls back to original with limits.
        """
        
        context = {
            # Basic execution variables (unchanged)
            "client_name": pipeline_context.client_name,
            "url": pipeline_context.url,
            "step_id": step.id,
            "step_name": step.name,
        }
        
        # Add pipeline metadata
        context.update(pipeline_context.metadata)
        
        # Add step-specific config
        context.update(step.config)
        
        # SMART DEPENDENCY CONTEXT (replacing the 40k token dump)
        smart_dependency_context = await self._build_smart_dependency_context(
            step, pipeline_context, config
        )
        context.update(smart_dependency_context)
        
        # Limited vector context (if enabled)
        if config.get("enable_vector_insights", True):
            vector_context = await self._build_limited_vector_context(
                step, pipeline_context, config
            )
            context.update(vector_context)
        
        # Add context metrics for monitoring
        context["_context_metrics"] = self._calculate_context_metrics(context)
        
        return context
    
    @log_exceptions
    async def _build_smart_dependency_context(self,
                                            step: StepConfig,
                                            pipeline_context: PipelineContext,
                                            config: Dict[str, Any]) -> Dict[str, Any]:
        """Build smart dependency context using chunked retrieval and synthesis."""
        
        dependency_context = {}
        total_tokens_used = 0
        
        logger.info(f"🧠 Building synthesized context for {step.id} dependencies...")
        
        # Get step-specific search queries
        search_queries = self._get_step_search_queries(step.id)
        
        # Collect chunks for all dependencies first
        dependency_chunks = {}
        
        for dep_id in step.dependencies:
            # Get relevant chunks for this dependency
            chunks = self.storage.get_relevant_chunks(
                query=f"{dep_id} {' '.join(search_queries)}",
                client_name=pipeline_context.client_name,
                max_chunks=5  # Limit chunks per dependency
            )
            
            if chunks:
                dependency_chunks[dep_id] = chunks
                logger.info(f"📋 {dep_id}: {len(chunks)} chunks retrieved")
        
        # Synthesize each dependency's context (guaranteed <1000 tokens each)
        if dependency_chunks:
            synthesized_deps = await self.synthesizer.synthesize_dependency_context(
                dependency_chunks=dependency_chunks,
                step_id=step.id,
                client_name=pipeline_context.client_name
            )
            
            dependency_context.update(synthesized_deps)
            
            # Count total tokens from synthesized content
            for key, content in synthesized_deps.items():
                tokens_used = self._count_tokens(content)
                total_tokens_used += tokens_used
                logger.info(f"✅ {key}: {tokens_used} tokens (synthesized)")
        
        # Add summary of previous context (limited)
        if total_tokens_used < self.max_context_tokens - 500:
            summary_context = self._build_limited_previous_context(
                pipeline_context, 
                max_tokens=min(500, self.max_context_tokens - total_tokens_used)
            )
            if summary_context:
                dependency_context["previous_context"] = summary_context
                total_tokens_used += self._count_tokens(summary_context)
        
        logger.info(f"📊 Total synthesized context: {total_tokens_used} tokens")
        
        return dependency_context
    
    def _get_step_search_queries(self, step_id: str) -> List[str]:
        """Get relevant search queries for each step type."""
        
        queries = {
            "discovery": [
                "company overview",
                "business model", 
                "products services",
                "key features"
            ],
            "market_position": [
                "market position",
                "competitive advantages", 
                "industry analysis",
                "differentiation"
            ],
            "audience_insights": [
                "target audience",
                "customer segments",
                "buyer personas",
                "use cases"
            ],
            "competitive_landscape": [
                "competitors",
                "competitive analysis",
                "market positioning",
                "alternatives"
            ],
            "strategic_synthesis": [
                "strategic insights",
                "key findings",
                "opportunities",
                "recommendations"
            ]
        }
        
        return queries.get(step_id, [f"{step_id} analysis"])
    
    @log_exceptions
    async def _build_limited_vector_context(self,
                                          step: StepConfig,
                                          pipeline_context: PipelineContext,
                                          config: Dict[str, Any]) -> Dict[str, Any]:
        """Build limited vector context using synthesis."""
        
        vector_context = {}
        
        try:
            # Get cross-client chunks for synthesis
            cross_client_query = f"{step.id} insights best practices"
            
            cross_client_chunks = self.storage.get_relevant_chunks(
                query=cross_client_query,
                client_name=None,  # Search across all clients  
                max_chunks=3       # Limited cross-client chunks
            )
            
            if cross_client_chunks:
                # Synthesize cross-client insights
                synthesized_insights = await self.synthesizer.synthesize_context(
                    chunks=cross_client_chunks,
                    step_id=step.id,
                    query=cross_client_query,
                    client_name="cross_client"
                )
                
                if synthesized_insights:
                    vector_context["cross_client_insights"] = synthesized_insights
                    logger.info(f"🌐 Cross-client insights: {self._count_tokens(synthesized_insights)} tokens (synthesized)")
                
        except Exception as e:
            logger.warning(f"⚠️  Vector context building failed: {e}")
            vector_context["vector_context_error"] = str(e)
        
        return vector_context
    
    def _build_limited_previous_context(self,
                                      pipeline_context: PipelineContext,
                                      max_tokens: int) -> Optional[str]:
        """Build limited summary of previous steps."""
        
        all_results = pipeline_context.get_all_results()
        
        if not all_results:
            return None
        
        # Get most recent steps
        recent_steps = list(all_results.keys())[-2:]  # Last 2 steps only
        
        context_parts = []
        current_tokens = 0
        
        for step_id in recent_steps:
            if current_tokens >= max_tokens:
                break
                
            result = all_results[step_id]
            
            # Create very brief summary
            if isinstance(result, dict):
                summary = f"**{step_id}:** "
                
                # Extract just key fields with token awareness
                key_fields = ["company_name", "industry", "key_insights"][:3]
                field_summaries = []
                
                for field in key_fields:
                    if field in result and result[field]:
                        value = str(result[field])[:100]  # Limit field length
                        field_summaries.append(f"{field}: {value}")
                
                summary += "; ".join(field_summaries)
                
                summary_tokens = self._count_tokens(summary)
                if current_tokens + summary_tokens <= max_tokens:
                    context_parts.append(summary)
                    current_tokens += summary_tokens
        
        return "\n".join(context_parts) if context_parts else None
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text with fallback."""
        try:
            import tiktoken
            encoder = tiktoken.get_encoding("cl100k_base")
            return len(encoder.encode(text))
        except ImportError:
            # Fallback: rough estimation (4 chars per token average)
            return len(text) // 4
        except Exception:
            # Any other error, use fallback
            return len(text) // 4
    
    def _calculate_context_metrics(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Calculate context metrics for monitoring."""
        
        total_chars = 0
        total_tokens = 0
        context_items = 0
        
        for key, value in context.items():
            if isinstance(value, str) and not key.startswith('_'):
                total_chars += len(value)
                total_tokens += self._count_tokens(value)
                context_items += 1
        
        return {
            "total_tokens": str(total_tokens),
            "total_chars": str(total_chars),
            "context_items": str(context_items),
            "within_limits": str(total_tokens <= self.max_context_tokens)
        }