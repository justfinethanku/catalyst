"""Autonomous pipeline Streamlit UI with comprehensive logging."""

# ============================================================================
# ENVIRONMENT VARIABLE SETUP WITH LOGGING - MUST BE FIRST
# ============================================================================
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import logging utilities
from src.core.logging_utils import setup_logging, get_logger, log_config_error
import logging

# Setup logging for the UI
setup_logging(level=logging.INFO)
logger = get_logger(__name__)

# Force load .env file before any other imports
env_paths = [
    project_root / "api_secrets" / ".env",  # api_secrets/.env
    project_root / ".env",                  # root .env
    "api_secrets/.env",                     # relative path
    ".env"                                  # current directory
]

env_loaded = False
for env_path in env_paths:
    if Path(env_path).exists():
        try:
            load_dotenv(dotenv_path=env_path)
            logger.info("Successfully loaded .env from: %s", env_path)
            env_loaded = True
            break
        except Exception as e:
            log_config_error("environment file", str(env_path), e, 
                           "Check file permissions and syntax")

if not env_loaded:
    logger.warning("No .env file found in expected locations:")
    for path in env_paths:
        logger.warning("   - %s", path)
    logger.info("Attempting to load default .env configuration")
    # Still try to load default
    load_dotenv()

# Validate API key configuration with secure logging
logger.info("=" * 50)
logger.info("Environment Variable Validation")
logger.info("=" * 50)

openai_key = os.getenv("OPENAI_API_KEY")
if openai_key:
    # Show first 10 and last 4 characters for security
    masked_key = f"{openai_key[:10]}...{openai_key[-4:]}" if len(openai_key) > 14 else "***HIDDEN***"
    logger.info("OPENAI_API_KEY loaded: %s", masked_key)
    logger.debug("Key length: %d characters", len(openai_key))
else:
    logger.error("OPENAI_API_KEY not found in environment!")
    logger.error("Check that api_secrets/.env exists and contains OPENAI_API_KEY=your_key_here")

# Check if environment variable is being overridden
shell_key = os.environ.get("OPENAI_API_KEY")
if shell_key and shell_key != openai_key:
    logger.warning("WARNING: Shell environment variable differs from .env file!")
    shell_masked = f"{shell_key[:10]}...{shell_key[-4:]}" if len(shell_key) > 14 else "***"
    env_masked = f"{openai_key[:10]}...{openai_key[-4:]}" if openai_key and len(openai_key) > 14 else "***"
    logger.warning("Shell key: %s", shell_masked)
    logger.warning(".env key:  %s", env_masked)
    logger.info("To use .env file, run: unset OPENAI_API_KEY")
elif shell_key:
    logger.info("Source: Shell environment variable (same as .env)")
else:
    logger.info("Source: .env file only")

logger.info("=" * 50)
# ============================================================================

import streamlit as st
from src.ui.initialization import init_autonomous_system


def main():
    """Autonomous pipeline Streamlit app."""
    st.set_page_config(
        page_title="Catalyst Autonomous Research",
        page_icon="C",
        layout="wide"
    )
    
    # Initialize system
    init_autonomous_system()
    
    # Check initialization
    if not st.session_state.get("init_success", False):
        st.error("System Initialization Failed")
        st.write(f"Error: {st.session_state.get('init_error', 'Unknown error')}")
        st.write("Please check your API keys in `api_secrets/.env`")
        st.stop()
    
    st.title("Catalyst Autonomous Research System")
    st.write("By Jonathan Edwards")
    
    # Sidebar - System Status
    from src.ui.sidebar import render_sidebar
    render_sidebar()
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        from src.ui.analysis_form import render_analysis_form
        render_analysis_form()
    
    with col2:
        from src.ui.search_components import render_quick_search
        render_quick_search()
    
    # Enhanced Results section
    clients = st.session_state.storage.get_all_clients()
    if clients:
        from src.ui.database_explorer import render_company_explorer
        render_company_explorer()


if __name__ == "__main__":
    main()