"""Autonomous pipeline execution engine."""
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
from dataclasses import dataclass
from enum import Enum

from .config_loader import ConfigLoader, PipelineConfig, StepConfig, StepStatus
from .template_renderer import TemplateRenderer
from .context_builder import ContextBuilder, PipelineContext
from ...storage import HybridStore
from ..llm_providers import MultiProviderLLM, OpenAIProvider
from ..parallel_storage import ParallelStorageManager
from ..smart_context_builder import SmartContextBuilder
from ..model_config import get_provider_models
from ..embedding_utils import check_and_warn_embedding_unavailable
from ..logging_utils import get_logger, log_exceptions


class PipelineStatus(Enum):
    """Pipeline execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class StepResult:
    """Result from executing a pipeline step."""
    step_id: str
    status: str
    content: Dict[str, Any]
    doc_id: str
    execution_time: float
    error: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class PipelineResult:
    """Complete pipeline execution result."""
    pipeline_name: str
    client_name: str
    url: str
    status: PipelineStatus
    step_results: Dict[str, StepResult]
    total_execution_time: float
    started_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None
    
    def get_step_result(self, step_id: str) -> Optional[StepResult]:
        """Get result for a specific step."""
        return self.step_results.get(step_id)
    
    def get_successful_steps(self) -> List[str]:
        """Get list of successfully completed steps."""
        return [
            step_id for step_id, result in self.step_results.items()
            if result.status == "success"
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization."""
        return {
            "pipeline_name": self.pipeline_name,
            "client_name": self.client_name,
            "url": self.url,
            "status": self.status.value,
            "total_execution_time": self.total_execution_time,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "step_results": {
                step_id: {
                    "step_id": result.step_id,
                    "status": result.status,
                    "content": result.content,
                    "doc_id": result.doc_id,
                    "execution_time": result.execution_time,
                    "timestamp": result.timestamp,
                    "error": result.error
                }
                for step_id, result in self.step_results.items()
            }
        }


logger = get_logger(__name__)


class PipelineEngine:
    """Autonomous pipeline execution engine."""
    
    def __init__(self, 
                 storage: HybridStore,
                 config_loader: Optional[ConfigLoader] = None,
                 enable_smart_chunking: bool = True):
        """Initialize pipeline engine with optional smart chunking."""
        self.storage = storage
        self.config_loader = config_loader or ConfigLoader()
        
        # Initialize template renderer with correct path
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent.parent
        templates_path = project_root / "templates"
        self.template_renderer = TemplateRenderer(str(templates_path))
        
        # Initialize OpenAI provider for synthesis
        self.openai_provider = self._initialize_openai_provider()
        
        # Initialize storage systems
        if enable_smart_chunking and check_and_warn_embedding_unavailable("smart chunking system"):
            logger.info("🚀 Initializing smart chunking system...")
            self.parallel_storage = ParallelStorageManager(storage)
            if self.openai_provider:
                self.smart_context_builder = SmartContextBuilder(self.parallel_storage, self.openai_provider)
                logger.info("✅ Smart chunking with synthesis enabled")
                self.use_smart_chunking = True
            else:
                logger.warning("⚠️  OpenAI not available - smart chunking disabled")
                self.context_builder = ContextBuilder(storage)
                self.use_smart_chunking = False
        else:
            logger.warning("⚠️  Smart chunking disabled - embeddings unavailable or disabled")
            self.context_builder = ContextBuilder(storage)
            self.parallel_storage = None
            self.smart_context_builder = None
            self.use_smart_chunking = False
        
        # Use MultiProviderLLM instead of hardcoded LLMInterface
        self.llm_interface = MultiProviderLLM()
        
        # Execution state
        self.current_execution: Optional[PipelineResult] = None
        self.execution_callbacks: List[callable] = []
    
    def _initialize_openai_provider(self) -> Optional[OpenAIProvider]:
        """Initialize OpenAI provider for synthesis."""
        try:
            import sys
            from pathlib import Path
            
            # Add project root to path
            project_root = Path(__file__).parent.parent.parent.parent
            sys.path.insert(0, str(project_root))
            
            from api_secrets.api_keys import OPENAI_API_KEY
            
            if OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here":
                # Get OpenAI models config from centralized configuration
                openai_models = get_provider_models("openai")
                return OpenAIProvider(OPENAI_API_KEY, openai_models)
            else:
                logger.warning("⚠️  Warning: No OpenAI API key found for synthesis")
                return None
                
        except Exception as e:
            logger.warning(f"⚠️  Warning: Could not initialize OpenAI provider: {e}")
            return None
    
    @log_exceptions
    async def execute_pipeline(self,
                              pipeline_name: str,
                              client_name: str,
                              url: str,
                              metadata: Optional[Dict[str, Any]] = None) -> PipelineResult:
        """
        Execute autonomous research pipeline.
        
        Args:
            pipeline_name: Name of pipeline to execute
            client_name: Client identifier
            url: Company URL to analyze
            metadata: Additional metadata
            
        Returns:
            Complete pipeline execution result
        """
        start_time = datetime.now()
        
        try:
            # Load pipeline configuration
            config = self.config_loader.load_pipeline(pipeline_name)
            
            # Override configuration with user-selected model settings if provided
            if metadata:
                user_provider = metadata.get('user_provider')
                user_model = metadata.get('user_model')
                
                if user_provider and user_model:
                    logger.info(f"🎯 User model override: {user_provider} {user_model}")
                    # Override the YAML settings with user selections
                    config.settings['llm_provider'] = user_provider
                    config.settings['model'] = user_model
                    logger.info(f"✅ Pipeline will use: {user_provider} {user_model} (user selection)")
                else:
                    logger.info(f"📋 Using default pipeline settings: {config.settings.get('llm_provider', 'openai')} {config.settings.get('model', 'gpt-4.1')}")
            
            # Initialize pipeline result
            result = PipelineResult(
                pipeline_name=pipeline_name,
                client_name=client_name,
                url=url,
                status=PipelineStatus.RUNNING,
                step_results={},
                total_execution_time=0.0,
                started_at=start_time.isoformat()
            )
            
            self.current_execution = result
            
            # Initialize pipeline context
            pipeline_context = PipelineContext(
                client_name=client_name,
                url=url,
                metadata=metadata or {}
            )
            
            # Get execution order
            execution_order = config.get_execution_order()
            
            logger.info(f"🚀 Starting autonomous pipeline: {config.name}")
            logger.info(f"   Client: {client_name}")
            logger.info(f"   URL: {url}")
            logger.info(f"   Steps: {' → '.join(execution_order)}")
            
            # Execute each step
            for i, step_id in enumerate(execution_order, 1):
                step = config.get_step(step_id)
                
                logger.info(f"📊 Step {i}/{len(execution_order)}: {step.name}")
                
                # Execute step
                step_result = await self._execute_step(
                    step=step,
                    pipeline_context=pipeline_context,
                    config=config
                )
                
                # Store step result
                result.step_results[step_id] = step_result
                
                # Add to pipeline context for next steps
                if step_result.status == "success":
                    pipeline_context.add_step_result(step_id, step_result.content)
                    logger.info(f"✅ Completed: {step.name}")
                else:
                    logger.error(f"❌ Failed: {step.name} - {step_result.error}")
                    result.status = PipelineStatus.FAILED
                    result.error = f"Step {step_id} failed: {step_result.error}"
                    break
                
                # Notify callbacks
                await self._notify_step_complete(step_id, step_result)
            
            # Finalize result
            if result.status == PipelineStatus.RUNNING:
                result.status = PipelineStatus.COMPLETED
                logger.info(f"🎉 Pipeline completed successfully!")
            
            end_time = datetime.now()
            result.total_execution_time = (end_time - start_time).total_seconds()
            result.completed_at = end_time.isoformat()
            
            # Store pipeline result
            await self._store_pipeline_result(result)
            
            return result
            
        except Exception as e:
            # Handle pipeline-level errors
            end_time = datetime.now()
            
            error_result = PipelineResult(
                pipeline_name=pipeline_name,
                client_name=client_name,
                url=url,
                status=PipelineStatus.FAILED,
                step_results=getattr(self.current_execution, 'step_results', {}),
                total_execution_time=(end_time - start_time).total_seconds(),
                started_at=start_time.isoformat(),
                completed_at=end_time.isoformat(),
                error=str(e)
            )
            
            logger.error(f"❌ Pipeline failed: {e}")
            
            return error_result
        
        finally:
            self.current_execution = None
    
    @log_exceptions
    async def _execute_step(self,
                           step: StepConfig,
                           pipeline_context: PipelineContext,
                           config: PipelineConfig) -> StepResult:
        """Execute a single pipeline step."""
        step_start = datetime.now()
        
        try:
            logger.info(f"🔄 Executing: {step.id}")
            
            # Build step context (smart or original)
            if self.use_smart_chunking:
                step_context = await self.smart_context_builder.build_smart_step_context(
                    step=step,
                    pipeline_context=pipeline_context,
                    config=config.settings
                )
            else:
                step_context = await self.context_builder.build_step_context(
                    step=step,
                    pipeline_context=pipeline_context,
                    config=config.settings
                )
            
            logger.info(f"📋 Context built: {len(step_context)} variables")
            
            # Render prompt template
            rendered_prompt = self.template_renderer.render(
                template_path=step.template,
                variables=step_context
            )
            
            # Calculate actual token count
            try:
                import tiktoken
                encoder = tiktoken.get_encoding("cl100k_base")
                prompt_tokens = len(encoder.encode(rendered_prompt))
                logger.info(f"📝 Prompt rendered: {len(rendered_prompt):,} chars (~{prompt_tokens:,} tokens)")
                
                if prompt_tokens > 35000:  # Close to 40k limit
                    logger.warning(f"⚠️  WARNING: Prompt is {prompt_tokens:,} tokens - very close to rate limit!")
                elif prompt_tokens > 25000:
                    logger.warning(f"⚠️  CAUTION: Prompt is {prompt_tokens:,} tokens - approaching rate limit")
            except:
                logger.info(f"📝 Prompt rendered: {len(rendered_prompt):,} chars")
            
            # Execute LLM research using user-selected provider and model
            provider = config.settings.get('llm_provider', 'openai')
            
            # Build combined config with user selections taking precedence
            llm_config = {**config.settings, **step.config}
            
            logger.info(f"🤖 Executing with {provider} using model: {llm_config.get('model', 'default')}")
            
            llm_result = await self.llm_interface.execute_research(
                prompt=rendered_prompt,
                provider=provider,
                config=llm_config
            )
            
            if llm_result["status"] != "success":
                raise Exception(f"LLM execution failed: {llm_result.get('error')}")
            
            logger.info(f"🤖 LLM completed")
            if llm_result.get("tool_calls"):
                logger.info(f"🔧 Tools used: {len(llm_result['tool_calls'])}")
            
            # Store in vector database (smart or original)
            if self.use_smart_chunking:
                storage_report = await self.parallel_storage.store_with_chunking(
                    content=llm_result.get("raw_response", ""),
                    metadata={
                        "client": pipeline_context.client_name,
                        "step": step.id,
                        "pipeline": config.name,
                        "url": pipeline_context.url,
                        **pipeline_context.metadata
                    },
                    client_name=pipeline_context.client_name
                )
                doc_id = storage_report["original_doc_id"]
                
                # Show storage status
                if storage_report["chunks_available"]:
                    logger.info(f"💾 Stored: {doc_id[:8]}... + {len(storage_report['chunk_ids'])} chunks")
                else:
                    logger.info(f"💾 Stored: {doc_id[:8]}... (chunks failed, using original)")
            else:
                doc_id = self.storage.store(
                    content=llm_result.get("raw_response", ""),
                    metadata={
                        "client": pipeline_context.client_name,
                        "step": step.id,
                        "pipeline": config.name,
                        "url": pipeline_context.url,
                        **pipeline_context.metadata
                    },
                    client_name=pipeline_context.client_name
                )
                logger.info(f"💾 Stored: {doc_id[:8]}...")
            
            # Create step result
            step_end = datetime.now()
            execution_time = (step_end - step_start).total_seconds()
            
            return StepResult(
                step_id=step.id,
                status="success",
                content=llm_result["content"],
                doc_id=doc_id,
                execution_time=execution_time,
                timestamp=step_end.isoformat()
            )
            
        except Exception as e:
            step_end = datetime.now()
            execution_time = (step_end - step_start).total_seconds()
            
            return StepResult(
                step_id=step.id,
                status="error",
                content={},
                doc_id="",
                execution_time=execution_time,
                error=str(e),
                timestamp=step_end.isoformat()
            )
    
    async def _store_pipeline_result(self, result: PipelineResult) -> None:
        """Store complete pipeline result."""
        try:
            # Store as summary document
            summary_content = self._create_pipeline_summary(result)
            
            self.storage.store(
                content=summary_content,
                metadata={
                    "client": result.client_name,
                    "type": "pipeline_result",
                    "pipeline": result.pipeline_name,
                    "status": result.status.value,
                    "steps_completed": len(result.get_successful_steps()),
                    "execution_time": result.total_execution_time
                },
                client_name=result.client_name
            )
            
        except Exception as e:
            logger.warning(f"Warning: Failed to store pipeline result: {e}")
    
    def _create_pipeline_summary(self, result: PipelineResult) -> str:
        """Create summary of pipeline execution."""
        successful_steps = result.get_successful_steps()
        
        summary_parts = [
            f"Pipeline Execution Summary for {result.client_name}",
            f"Pipeline: {result.pipeline_name}",
            f"URL: {result.url}",
            f"Status: {result.status.value}",
            f"Execution Time: {result.total_execution_time:.2f} seconds",
            f"Steps Completed: {len(successful_steps)}/{len(result.step_results)}",
            "",
            "Step Results:"
        ]
        
        for step_id, step_result in result.step_results.items():
            summary_parts.append(f"- {step_id}: {step_result.status}")
            if step_result.error:
                summary_parts.append(f"  Error: {step_result.error}")
        
        return "\n".join(summary_parts)
    
    async def _notify_step_complete(self, step_id: str, result: StepResult) -> None:
        """Notify callbacks of step completion."""
        for callback in self.execution_callbacks:
            try:
                await callback(step_id, result)
            except Exception as e:
                logger.warning(f"Warning: Callback error: {e}")
    
    def add_execution_callback(self, callback: callable) -> None:
        """Add callback for step completion events."""
        self.execution_callbacks.append(callback)
    
    def get_current_execution(self) -> Optional[PipelineResult]:
        """Get current execution status."""
        return self.current_execution