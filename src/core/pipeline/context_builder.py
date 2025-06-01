"""Context builder for autonomous pipeline execution."""
from typing import Dict, Any, List, Optional
from ..pipeline.config_loader import StepConfig
from ...storage import HybridStore
from ..logging_utils import get_logger, log_exceptions


logger = get_logger(__name__)


class PipelineContext:
    """Context container for pipeline execution."""
    
    def __init__(self, 
                 client_name: str, 
                 url: str, 
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize pipeline context."""
        self.client_name = client_name
        self.url = url
        self.metadata = metadata or {}
        self.step_results: Dict[str, Any] = {}
        self.execution_log: List[Dict[str, Any]] = []
    
    def add_step_result(self, step_id: str, result: Dict[str, Any]) -> None:
        """Add result from a completed step."""
        self.step_results[step_id] = result
        
        # Log the execution
        self.execution_log.append({
            "step_id": step_id,
            "timestamp": result.get("timestamp"),
            "status": "completed",
            "output_size": len(str(result))
        })
    
    def get_step_result(self, step_id: str) -> Optional[Dict[str, Any]]:
        """Get result from a specific step."""
        return self.step_results.get(step_id)
    
    def has_step_result(self, step_id: str) -> bool:
        """Check if step result exists."""
        return step_id in self.step_results
    
    def get_all_results(self) -> Dict[str, Any]:
        """Get all step results."""
        return self.step_results.copy()


class ContextBuilder:
    """Builds execution context for pipeline steps."""
    
    def __init__(self, storage: HybridStore):
        """Initialize context builder with storage backend."""
        self.storage = storage
    
    @log_exceptions
    async def build_step_context(self,
                                step: StepConfig,
                                pipeline_context: PipelineContext,
                                config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build complete context for step execution.
        
        Args:
            step: Step configuration
            pipeline_context: Current pipeline execution context
            config: Pipeline-level configuration
            
        Returns:
            Complete context for step execution
        """
        context = {
            # Basic execution variables
            "client_name": pipeline_context.client_name,
            "url": pipeline_context.url,
            "step_id": step.id,
            "step_name": step.name,
        }
        
        # Add pipeline metadata
        context.update(pipeline_context.metadata)
        
        # Add step-specific config
        context.update(step.config)
        
        # Add dependency results
        dependency_context = await self._build_dependency_context(
            step, pipeline_context, config
        )
        context.update(dependency_context)
        
        # Add vector database insights if enabled
        if config.get("enable_vector_insights", True):
            vector_context = await self._build_vector_context(
                step, pipeline_context, config
            )
            context.update(vector_context)
        
        return context
    
    async def _build_dependency_context(self,
                                      step: StepConfig,
                                      pipeline_context: PipelineContext,
                                      config: Dict[str, Any]) -> Dict[str, Any]:
        """Build context from step dependencies."""
        dependency_context = {}
        
        # Add results from direct dependencies
        for dep_id in step.dependencies:
            dep_result = pipeline_context.get_step_result(dep_id)
            if dep_result:
                # Add the dependency result under its step name
                dependency_context[dep_id] = dep_result
                
                # Extract key insights for easier access
                if "key_insights" in dep_result:
                    context_key = f"{dep_id}_insights"
                    dependency_context[context_key] = dep_result["key_insights"]
        
        # Add summary of all previous results for context window
        context_window = config.get("context_window", 2)
        if context_window > 0:
            previous_context = self._build_previous_context(
                pipeline_context, context_window
            )
            if previous_context:
                dependency_context["previous_context"] = previous_context
        
        return dependency_context
    
    async def _build_vector_context(self,
                                  step: StepConfig,
                                  pipeline_context: PipelineContext,
                                  config: Dict[str, Any]) -> Dict[str, Any]:
        """Build context from vector database insights."""
        vector_context = {}
        
        try:
            # Build search query based on step type and current context
            search_query = self._build_vector_search_query(step, pipeline_context)
            
            if search_query:
                # Search for similar research
                similar_research = self.storage.search(
                    query=search_query,
                    n_results=config.get("vector_context_limit", 5),
                    filter_client=None  # Search across all clients
                )
                
                if similar_research:
                    # Format similar research for context
                    formatted_similar = self._format_similar_research(
                        similar_research, pipeline_context.client_name
                    )
                    vector_context["similar_research"] = formatted_similar
            
            # Get cross-client insights for this step type
            cross_client_insights = self._get_cross_client_insights(
                step, pipeline_context, config
            )
            if cross_client_insights:
                vector_context["cross_client_insights"] = cross_client_insights
                
        except Exception as e:
            # Don't fail step execution if vector context fails
            logger.warning(f"Warning: Vector context building failed for step {step.id}: {e}")
            vector_context["vector_context_error"] = str(e)
        
        return vector_context
    
    def _build_previous_context(self,
                              pipeline_context: PipelineContext,
                              window_size: int) -> Optional[str]:
        """Build summary context from previous steps."""
        all_results = pipeline_context.get_all_results()
        
        if not all_results:
            return None
        
        # Get the most recent results up to window size
        recent_steps = list(all_results.keys())[-window_size:]
        
        context_parts = []
        for step_id in recent_steps:
            result = all_results[step_id]
            
            # Create summary of step result
            summary = f"**{step_id} Summary:**\n"
            
            # Add key findings if available
            if isinstance(result, dict):
                # Look for common summary fields
                summary_fields = [
                    "company_name", "industry", "market_position", 
                    "key_insights", "primary_audiences", "main_competitors"
                ]
                
                for field in summary_fields:
                    if field in result and result[field]:
                        value = result[field]
                        if isinstance(value, list):
                            summary += f"- {field}: {', '.join(str(v) for v in value[:3])}\n"
                        else:
                            summary += f"- {field}: {str(value)[:200]}\n"
            
            context_parts.append(summary)
        
        return "\n".join(context_parts) if context_parts else None
    
    def _build_vector_search_query(self,
                                 step: StepConfig,
                                 pipeline_context: PipelineContext) -> Optional[str]:
        """Build search query for vector database."""
        # Get basic context
        client_name = pipeline_context.client_name
        
        # Try to extract industry from previous results
        industry = None
        for result in pipeline_context.step_results.values():
            if isinstance(result, dict) and "industry" in result:
                industry = result["industry"]
                break
        
        # Build query based on step type
        step_queries = {
            "discovery": f"company analysis website research {client_name}",
            "market_position": f"market position analysis {industry or 'business'} competitive landscape",
            "audience_insights": f"target audience customer analysis {industry or 'business'} personas",
            "competitive_landscape": f"competitor analysis {industry or 'business'} competitive intelligence",
            "strategic_synthesis": f"strategic analysis recommendations {industry or 'business'} insights"
        }
        
        return step_queries.get(step.id, f"{step.id} research analysis")
    
    def _format_similar_research(self,
                               similar_research: List[Dict[str, Any]],
                               current_client: str) -> List[Dict[str, str]]:
        """Format similar research for context inclusion."""
        formatted = []
        
        for research in similar_research:
            content = research.get("content", "")
            metadata = research.get("metadata", {})
            
            # Skip if it's from the same client
            if metadata.get("client") == current_client:
                continue
            
            formatted_item = {
                "client": metadata.get("client", "Unknown"),
                "industry": metadata.get("industry", "Unknown"),
                "step": metadata.get("step", "Unknown"),
                "insight": content[:300] + "..." if len(content) > 300 else content,
                "relevance": f"{(1 - research.get('distance', 1)) * 100:.1f}%"
            }
            
            formatted.append(formatted_item)
        
        return formatted
    
    def _get_cross_client_insights(self,
                                 step: StepConfig,
                                 pipeline_context: PipelineContext,
                                 config: Dict[str, Any]) -> Optional[List[str]]:
        """Get insights from similar steps across other clients."""
        try:
            # Search for similar steps
            step_query = f"{step.id} insights patterns trends"
            
            results = self.storage.search(
                query=step_query,
                n_results=10,
                filter_client=None
            )
            
            if not results:
                return None
            
            # Extract common patterns or insights
            insights = []
            for result in results:
                metadata = result.get("metadata", {})
                
                # Skip same client
                if metadata.get("client") == pipeline_context.client_name:
                    continue
                
                # Skip different step types
                if metadata.get("step") != step.id:
                    continue
                
                content = result.get("content", "")
                if len(content) > 50:  # Only include substantial insights
                    insight = f"From {metadata.get('client', 'previous research')}: {content[:200]}..."
                    insights.append(insight)
            
            return insights[:3]  # Return top 3 insights
            
        except Exception as e:
            logger.warning(f"Error getting cross-client insights: {e}")
            return None