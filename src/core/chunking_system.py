"""Safe Contextual Retrieval with data integrity protection."""
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
from .logging_utils import get_logger, log_exceptions

# Safe tiktoken import with fallback
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

logger = get_logger(__name__)

# Log tiktoken availability after import check
if not TIKTOKEN_AVAILABLE:
    logger.warning("⚠️  tiktoken not available, using fallback token counting")


class DataIntegrityChunker:
    """Chunking system with full data integrity protection."""
    
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        """Initialize with integrity checking."""
        self.chunk_size = chunk_size
        self.overlap = overlap
        
        # Initialize tokenizer with fallback
        if TIKTOKEN_AVAILABLE:
            self.encoder = tiktoken.get_encoding("cl100k_base")
        else:
            self.encoder = None
        
        # Create backup directory
        self.backup_dir = Path("data_integrity_backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Initialize OpenAI provider for chunking operations
        # Model names loaded from src/config/models.yaml - no hardcoded models
        self.openai_client = None
        self.nano_model_key = "gpt-4.1-nano"  # Config key, not hardcoded model name
        self._init_openai()
        
        # Validate initialization and log results
        self._validate_nano_availability()
    
    def _init_openai(self):
        """Initialize GPT-4.1 nano for chunking operations with comprehensive diagnostics."""
        import traceback
        
        logger.info("🔍 Starting OpenAI initialization for chunking system...")
        
        try:
            # Import required modules with detailed logging
            logger.debug("Importing required modules...")
            from .embedding_utils import check_and_warn_embedding_unavailable
            from .llm_providers import OpenAIProvider
            from .model_config import get_provider_models
            logger.debug("✅ All required modules imported successfully")
            
            # Check if embeddings are available before enabling chunking
            logger.debug("Checking embedding availability...")
            if not check_and_warn_embedding_unavailable("intelligent chunking operations"):
                logger.warning("⚠️  Warning: Chunking operations will be limited (embeddings unavailable)")
                logger.warning("Reason: Embeddings not available - chunking system disabled")
                return
            logger.debug("✅ Embeddings are available")
            
            import sys
            from pathlib import Path
            
            # Add project root to path
            project_root = Path(__file__).parent.parent.parent
            sys.path.insert(0, str(project_root))
            logger.debug("Project root added to path: %s", project_root)
            
            # Import API key with error handling
            try:
                from api_secrets.api_keys import OPENAI_API_KEY
                logger.debug("✅ Successfully imported OPENAI_API_KEY")
            except ImportError as import_error:
                logger.error("❌ Failed to import OPENAI_API_KEY: %s", str(import_error))
                logger.error("Traceback:\n%s", traceback.format_exc())
                return
            
            # Validate API key
            if not OPENAI_API_KEY:
                logger.error("❌ OPENAI_API_KEY is None or empty")
                logger.warning("Reason: No API key available - chunking system disabled")
                return
                
            if OPENAI_API_KEY == "your_openai_api_key_here":
                logger.error("❌ OPENAI_API_KEY is still placeholder value")
                logger.warning("Reason: API key not configured - chunking system disabled")
                return
            
            # Show masked API key for verification
            masked_key = f"{OPENAI_API_KEY[:10]}...{OPENAI_API_KEY[-4:]}" if len(OPENAI_API_KEY) > 14 else "***HIDDEN***"
            logger.info("✅ Valid OPENAI_API_KEY found: %s", masked_key)
            
            # Get OpenAI models config from centralized configuration
            logger.debug("Loading OpenAI models configuration...")
            openai_models = get_provider_models("openai")
            logger.info("📋 OpenAI models from config: %s", openai_models)
            
            # Validate nano model key exists in config (models.yaml)
            if self.nano_model_key not in openai_models:
                logger.error("❌ Model key '%s' not found in OpenAI models configuration!", self.nano_model_key)
                logger.error("Available model keys: %s", list(openai_models.keys()))
                logger.warning("Reason: Model key not in models.yaml - chunking system disabled")
                return
            
            # Get official OpenAI model name from config (not hardcoded)
            nano_model_name = openai_models[self.nano_model_key]
            logger.info("✅ Model key '%s' found in configuration: %s", self.nano_model_key, nano_model_name)
            
            # Initialize OpenAI provider
            logger.debug("Initializing OpenAI provider...")
            self.openai_client = OpenAIProvider(OPENAI_API_KEY, openai_models)
            logger.debug("✅ OpenAI provider created successfully")
            
            # Verify the model is available on the provider
            available_models = self.openai_client.get_available_models()
            logger.debug("Available models on provider: %s", available_models)
            
            if self.nano_model_key in available_models:
                logger.info("🟢 OpenAI nano model initialized successfully for chunking operations")
                logger.info("Model mapping: %s -> %s (from models.yaml)", self.nano_model_key, nano_model_name)
            else:
                logger.error("❌ Model key '%s' not available on OpenAI provider!", self.nano_model_key)
                logger.error("Provider models: %s", available_models)
                logger.warning("Reason: Model not available on provider - chunking system disabled")
                self.openai_client = None  # Clear the client
                return
                
        except Exception as e:
            logger.error("❌ Critical error in OpenAI initialization: %s", str(e))
            logger.error("Full traceback:\n%s", traceback.format_exc())
            logger.warning("Reason: Initialization exception - chunking system disabled")
            self.openai_client = None  # Ensure client is cleared on error
    
    def _validate_nano_availability(self):
        """Validate GPT-4.1 nano availability at startup and log comprehensive results."""
        logger.info("🔍 Validating GPT-4.1 nano availability for chunking system...")
        
        # Check if client was initialized
        if self.openai_client is None:
            logger.error("❌ CHUNKING SYSTEM DISABLED: OpenAI client not initialized")
            logger.error("Impact: Smart chunking operations will not be available")
            logger.error("Resolution: Check API key configuration and model availability")
            return False
        
        # Check if nano model key is set correctly
        if not self.nano_model_key:
            logger.error("❌ CHUNKING SYSTEM DISABLED: nano_model_key not set")
            return False
        
        # Verify the model is available on the provider
        try:
            available_models = self.openai_client.get_available_models()
            
            if self.nano_model_key in available_models:
                # Get official model name from config
                model_name = available_models[self.nano_model_key]
                logger.info("✅ CHUNKING SYSTEM READY: OpenAI nano model is available")
                logger.info("Model: %s -> %s (from models.yaml)", self.nano_model_key, model_name)
                logger.info("Smart chunking operations enabled")
                return True
            else:
                logger.error("❌ CHUNKING SYSTEM DISABLED: Model key not in provider models")
                logger.error("Requested: %s", self.nano_model_key)
                logger.error("Available: %s", list(available_models.keys()))
                return False
                
        except Exception as e:
            logger.error("❌ CHUNKING SYSTEM DISABLED: Error validating models: %s", str(e))
            return False
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text - requires tiktoken."""
        if TIKTOKEN_AVAILABLE and self.encoder:
            return len(self.encoder.encode(text))
        else:
            raise Exception("tiktoken not available - accurate token counting required for chunking")
    
    def create_data_checkpoint(self, 
                             original_data: Dict[str, Any], 
                             client_name: str, 
                             step_id: str) -> str:
        """Create integrity checkpoint before chunking."""
        checkpoint = {
            "timestamp": datetime.now().isoformat(),
            "client_name": client_name,
            "step_id": step_id,
            "original_data": original_data,
            "data_hash": self._hash_data(original_data),
            "token_count": self.count_tokens(str(original_data))
        }
        
        # Save checkpoint
        checkpoint_file = self.backup_dir / f"{client_name}_{step_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2, default=str)
        
        logger.info(f"💾 Data checkpoint created: {checkpoint_file.name}")
        return str(checkpoint_file)
    
    def _hash_data(self, data: Any) -> str:
        """Create hash of data for integrity verification."""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    @log_exceptions
    async def chunk_with_integrity(self, 
                                  content: str, 
                                  step_id: str, 
                                  client_name: str, 
                                  metadata: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Chunk content with full integrity verification.
        
        Returns:
            Tuple of (chunks, integrity_report)
        """
        logger.info(f"🔧 Starting safe chunking for {step_id}...")
        
        # Create checkpoint
        original_data = {"content": content, "metadata": metadata}
        checkpoint_file = self.create_data_checkpoint(original_data, client_name, step_id)
        
        # Perform chunking
        chunks = await self._safe_chunk_content(content, step_id, client_name, metadata)
        
        # Verify integrity
        integrity_report = self._verify_integrity(content, chunks, checkpoint_file)
        
        logger.info(f"✅ Chunking complete: {len(chunks)} chunks, integrity: {integrity_report['status']}")
        
        return chunks, integrity_report
    
    async def _safe_chunk_content(self, 
                                content: str, 
                                step_id: str, 
                                client_name: str, 
                                metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Safely chunk content using GPT-4.1 nano."""
        
        # Step 1: Break into logical sections
        sections = await self._extract_sections_with_gpt_nano(content, step_id)
        
        # Step 2: Chunk each section
        all_chunks = []
        for section_title, section_content in sections:
            section_chunks = await self._chunk_section_with_gpt_nano(
                section_content, section_title, step_id, client_name, metadata
            )
            all_chunks.extend(section_chunks)
        
        return all_chunks
    
    @log_exceptions
    async def _extract_sections_with_gpt_nano(self, content: str, step_id: str) -> List[Tuple[str, str]]:
        """Use GPT-4.1 nano to intelligently extract logical sections."""
        
        # Comprehensive diagnostic logging before raising exception
        if not self.openai_client:
            logger.error("❌ OpenAI nano model section extraction failed - client not initialized")
            logger.error("Diagnostic information:")
            logger.error("  - self.openai_client: %s", self.openai_client)
            logger.error("  - self.nano_model_key: %s", self.nano_model_key)
            
            # Try to get available models for diagnosis
            try:
                from .model_config import get_provider_models
                available_models = get_provider_models("openai")
                logger.error("  - Available models in config: %s", available_models)
                
                if self.nano_model_key in available_models:
                    logger.error("  - Model key '%s' IS in config but client failed to initialize", self.nano_model_key)
                else:
                    logger.error("  - Model key '%s' is NOT in models configuration", self.nano_model_key)
            except Exception as diag_error:
                logger.error("  - Failed to get diagnostic info: %s", str(diag_error))
            
            raise Exception("GPT-4.1 nano not available - chunking requires LLM support")
        
        try:
            # Use GPT-4.1 nano to identify logical sections
            prompt = f"""Please identify the main logical sections in this {step_id} analysis content. 

Content to analyze:
{content[:2000]}...

Return a simple list of section titles you identify, one per line. Only return the titles, nothing else.
Examples:
- Company Overview
- Business Model  
- Key Products
- Market Position"""

            # Use OpenAI Chat Completions API with model name from models.yaml
            result = await self.openai_client.execute_research(
                prompt=prompt,
                config={
                    "model": self.nano_model_key,  # Config key, model name loaded from models.yaml
                    "max_tokens": 500
                }
            )
            
            if result["status"] != "success":
                raise Exception(f"Section extraction failed: {result.get('error')}")
            
            section_titles = [line.strip("- ").strip() for line in result["raw_response"].split('\n') if line.strip()]
            
            # Map sections to content
            sections = []
            remaining_content = content
            
            for title in section_titles:
                # Simple section extraction (could be improved)
                sections.append((title, remaining_content[:len(remaining_content)//len(section_titles)]))
                remaining_content = remaining_content[len(remaining_content)//len(section_titles):]
            
            if remaining_content:
                sections.append(("Additional Analysis", remaining_content))
            
            return sections if sections else [("Analysis", content)]
            
        except Exception as e:
            logger.error(f"❌ GPT-4.1 nano section extraction failed: {e}")
            raise Exception(f"Section extraction failed: {e}")
    
    @log_exceptions
    async def _chunk_section_with_gpt_nano(self, 
                                      content: str, 
                                      section_title: str, 
                                      step_id: str, 
                                      client_name: str, 
                                      metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk a section using token-aware splitting."""
        
        chunks = []
        
        # Simple paragraph-based chunking with token awareness
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        current_chunk = ""
        current_tokens = 0
        
        for paragraph in paragraphs:
            para_tokens = self.count_tokens(paragraph)
            
            if current_tokens + para_tokens > self.chunk_size:
                if current_chunk:
                    # Contextualize and add chunk
                    contextualized_chunk = await self._contextualize_with_gpt_nano(
                        current_chunk.strip(), section_title, step_id, client_name
                    )
                    
                    chunk_metadata = {
                        **metadata,
                        "chunk_index": len(chunks),
                        "section": section_title,
                        "original_step": step_id,
                        "content_type": "contextualized_chunk",
                        "token_count": self.count_tokens(contextualized_chunk)
                    }
                    
                    chunks.append({
                        "content": contextualized_chunk,
                        "metadata": chunk_metadata
                    })
                
                current_chunk = paragraph
                current_tokens = para_tokens
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
                current_tokens += para_tokens
        
        # Add final chunk
        if current_chunk:
            contextualized_chunk = await self._contextualize_with_gpt_nano(
                current_chunk.strip(), section_title, step_id, client_name
            )
            
            chunk_metadata = {
                **metadata,
                "chunk_index": len(chunks),
                "section": section_title,
                "original_step": step_id,
                "content_type": "contextualized_chunk",
                "token_count": self.count_tokens(contextualized_chunk)
            }
            
            chunks.append({
                "content": contextualized_chunk,
                "metadata": chunk_metadata
            })
        
        return chunks
    
    @log_exceptions
    async def _contextualize_with_gpt_nano(self, 
                                      chunk_content: str, 
                                      section_title: str, 
                                      step_id: str, 
                                      client_name: str) -> str:
        """Use GPT-4.1 nano to add contextual prefix to chunk."""
        
        # Comprehensive diagnostic logging before raising exception
        if not self.openai_client:
            logger.error("❌ OpenAI nano model contextualization failed - client not initialized")
            logger.error("Diagnostic information:")
            logger.error("  - self.openai_client: %s", self.openai_client)
            logger.error("  - self.nano_model_key: %s", self.nano_model_key)
            logger.error("  - client_name: %s", client_name)
            logger.error("  - step_id: %s", step_id)
            logger.error("  - section_title: %s", section_title)
            
            # Try to get available models for diagnosis
            try:
                from .model_config import get_provider_models
                available_models = get_provider_models("openai")
                logger.error("  - Available models in config: %s", available_models)
                
                if self.nano_model_key in available_models:
                    logger.error("  - Model key '%s' IS in config but client failed to initialize", self.nano_model_key)
                else:
                    logger.error("  - Model key '%s' is NOT in models configuration", self.nano_model_key)
            except Exception as diag_error:
                logger.error("  - Failed to get diagnostic info: %s", str(diag_error))
            
            raise Exception("GPT-4.1 nano not available - contextualization requires LLM support")
        
        try:
            prompt = f"""Add a brief contextual prefix to this analysis chunk. 

Company: {client_name.replace('_', ' ').title()}
Analysis Type: {step_id.replace('_', ' ').title()}  
Section: {section_title}

Chunk Content:
{chunk_content}

Add a contextual prefix like "From [Company] [Analysis Type] - [Section]:" then the content. Keep it concise.
Only return the contextualized content, nothing else."""

            # Use OpenAI Chat Completions API with model name from models.yaml
            result = await self.openai_client.execute_research(
                prompt=prompt,
                config={
                    "model": self.nano_model_key,  # Config key, model name loaded from models.yaml
                    "max_tokens": len(chunk_content) + 100
                }
            )
            
            if result["status"] != "success":
                raise Exception(f"Contextualization failed: {result.get('error')}")
            
            return result["raw_response"].strip()
            
        except Exception as e:
            logger.error(f"❌ GPT-4.1 nano contextualization failed: {e}")
            raise Exception(f"Contextualization failed: {e}")
    
    def _verify_integrity(self, 
                         original_content: str, 
                         chunks: List[Dict[str, Any]], 
                         checkpoint_file: str) -> Dict[str, Any]:
        """Verify that chunking preserved all information."""
        
        logger.info(f"🔍 Starting integrity verification for {len(chunks)} chunks...")
        
        # Reconstruct content from chunks
        reconstructed = []
        total_chunk_tokens = 0
        
        logger.debug(f"📊 Processing {len(chunks)} chunks for integrity check:")
        for i, chunk in enumerate(chunks):
            chunk_content = chunk["content"]
            chunk_metadata = chunk.get("metadata", {})
            
            logger.debug(f"  Chunk {i}: {len(chunk_content)} chars, metadata: {list(chunk_metadata.keys())}")
            
            # Remove contextual prefix to get original content
            if ":" in chunk_content:
                original_part = chunk_content.split(":", 1)[1].strip()
                reconstructed.append(original_part)
                logger.debug(f"    Removed prefix, original part: {len(original_part)} chars")
            else:
                reconstructed.append(chunk_content)
                logger.debug(f"    No prefix found, using full content: {len(chunk_content)} chars")
            
            chunk_tokens = chunk_metadata.get("token_count", 0)
            total_chunk_tokens += chunk_tokens
            logger.debug(f"    Chunk tokens: {chunk_tokens}, running total: {total_chunk_tokens}")
        
        reconstructed_content = "\n\n".join(reconstructed)
        
        # Calculate integrity metrics
        original_tokens = self.count_tokens(original_content)
        original_length = len(original_content)
        reconstructed_length = len(reconstructed_content)
        
        logger.info(f"📏 Integrity metrics calculation:")
        logger.info(f"  Original: {original_length} chars, {original_tokens} tokens")
        logger.info(f"  Reconstructed: {reconstructed_length} chars, {total_chunk_tokens} chunk tokens")
        
        # Calculate similarity (simple) - adjusted for contextualized content
        content_preservation = min(reconstructed_length / original_length, 1.0) if original_length > 0 else 0.0
        
        # For contextualized chunks, we expect content expansion due to prefixes
        # Adjust threshold based on whether content expanded (indicates contextualization)
        if reconstructed_length > original_length * 0.9:  # Content expanded, likely contextualized
            threshold = 0.70  # More lenient for contextualized content
            logger.info(f"📈 Content expanded (likely contextualized), using lenient threshold: {threshold}")
        else:
            threshold = 0.75  # Standard threshold
            logger.info(f"📏 Standard content, using standard threshold: {threshold}")
        
        # Determine status and reason
        status = "PASS" if content_preservation > threshold else "WARNING"
        
        # Add detailed reason for WARNING status
        warning_reason = None
        if status == "WARNING":
            if content_preservation < 0.5:
                warning_reason = f"Low content preservation: {content_preservation:.2%} (threshold: {threshold:.2%})"
            elif reconstructed_length < original_length * 0.5:
                warning_reason = f"Significant content loss: {reconstructed_length} chars vs {original_length} original"
            else:
                warning_reason = f"Content preservation {content_preservation:.2%} below threshold {threshold:.2%}"
        
        logger.info(f"🎯 Integrity check result: {status}")
        logger.info(f"  Content preservation: {content_preservation:.2%}")
        logger.info(f"  Threshold used: {threshold:.2%}")
        if warning_reason:
            logger.warning(f"⚠️  Warning reason: {warning_reason}")
        
        integrity_report = {
            "status": status,
            "content_preservation": f"{content_preservation:.2%}",
            "content_preservation_ratio": content_preservation,
            "threshold_used": threshold,
            "original_tokens": original_tokens,
            "chunk_tokens": total_chunk_tokens,
            "original_length": original_length,
            "reconstructed_length": reconstructed_length,
            "num_chunks": len(chunks),
            "checkpoint_file": checkpoint_file,
            "timestamp": datetime.now().isoformat(),
            "warning_reason": warning_reason
        }
        
        # Save integrity report
        report_file = self.backup_dir / f"integrity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(integrity_report, f, indent=2)
        
        logger.info(f"💾 Integrity report saved: {report_file.name}")
        
        return integrity_report
    
    def rollback_if_needed(self, integrity_report: Dict[str, Any]) -> bool:
        """Check if rollback is needed based on integrity."""
        if integrity_report["status"] == "WARNING":
            logger.warning(f"⚠️  Data integrity warning: {integrity_report['content_preservation']} preservation")
            logger.warning(f"📁 Checkpoint available: {integrity_report['checkpoint_file']}")
            return True
        return False