"""Initialization module for the autonomous pipeline system."""
import streamlit as st
import logging

from src.core.pipeline.engine import PipelineEngine
from src.storage import HybridStore
from src.core.llm_providers import MultiProviderLLM
from src.core.intelligence_briefing import IntelligenceBriefingGenerator
from src.core.briefing_pdf import IntelligenceBriefingPDF
from src.core.embedding_utils import are_embeddings_available, get_embedding_status_message

logger = logging.getLogger(__name__)


def init_autonomous_system():
    """Initialize the autonomous pipeline system."""
    if "engine" not in st.session_state:
        try:
            # Check embedding availability and store status
            embeddings_available = are_embeddings_available()
            st.session_state.embeddings_available = embeddings_available
            st.session_state.embedding_status_message = get_embedding_status_message()
            
            # Always initialize storage (with graceful degradation for embeddings)
            storage = HybridStore()
            st.session_state.storage = storage
            
            # Initialize pipeline engine (may have limited functionality without embeddings)
            if embeddings_available:
                logger.info("Initializing pipeline engine with full embedding support")
                engine = PipelineEngine(storage)
                st.session_state.engine = engine
                st.session_state.engine_available = True
            else:
                logger.warning("Initializing pipeline engine with limited functionality (no embeddings)")
                st.session_state.engine = None
                st.session_state.engine_available = False
            
            # Initialize multi-provider LLM (independent of embeddings)
            multi_llm = MultiProviderLLM()
            st.session_state.multi_llm = multi_llm
            st.session_state.available_providers = multi_llm.get_available_providers()
            
            
            # Initialize Intelligence Briefing Generator (may work without embeddings)
            briefing_generator = IntelligenceBriefingGenerator(storage, multi_llm)
            st.session_state.briefing_generator = briefing_generator
            
            # Initialize Beautiful Briefing PDF Generator (independent of embeddings)
            briefing_pdf = IntelligenceBriefingPDF()
            st.session_state.briefing_pdf = briefing_pdf
            
            st.session_state.init_success = True
            
            # Log initialization status
            if embeddings_available:
                logger.info("System fully initialized with embedding support")
            else:
                logger.info("System initialized with limited functionality (embeddings disabled)")
                
        except Exception as e:
            st.session_state.init_success = False
            st.session_state.init_error = str(e)
            st.session_state.embeddings_available = False
            st.session_state.engine_available = False
            logger.error(f"System initialization failed: {e}")