#!/usr/bin/env python3
"""Launch the autonomous pipeline Streamlit app with comprehensive logging."""

import subprocess
import sys
from pathlib import Path

# Setup logging first
sys.path.insert(0, str(Path(__file__).parent))
from src.core.logging_utils import setup_logging, log_exceptions, get_logger, CatalystLogger
import logging

# Configure logging for the entry point
setup_logging(level=logging.INFO)
logger = get_logger(__name__)

@log_exceptions
def main():
    """Launch the autonomous Streamlit app."""
    
    with CatalystLogger("Catalyst System Startup") as startup_logger:
        # Get the project root directory
        project_root = Path(__file__).parent
        startup_logger.info("Project root: %s", project_root)
        
        # Path to the autonomous app
        app_path = project_root / "src" / "ui" / "autonomous_app.py"
        startup_logger.info("App path: %s", app_path)
        
        if not app_path.exists():
            startup_logger.error("App not found at %s", app_path)
            logger.error("Critical error: Autonomous app file not found at %s", app_path)
            sys.exit(1)
        
        startup_logger.success("App file found, launching Catalyst system")
        logger.info("LAUNCHING CATALYST AUTONOMOUS RESEARCH SYSTEM")
        logger.info("=" * 55)
        logger.info("Project: %s", project_root)
        logger.info("App: %s", app_path)
        logger.info("URL: http://localhost:8502")
        logger.info("=" * 55)
        
        # Launch Streamlit
        try:
            startup_logger.info("Starting Streamlit server")
            subprocess.run([
                sys.executable, "-m", "streamlit", "run", 
                str(app_path),
                "--server.port=8502",
                "--server.headless=false",
                "--browser.gatherUsageStats=false"
            ], cwd=str(project_root))
            
        except KeyboardInterrupt:
            logger.info("Autonomous system shutdown (user interrupted)")
            startup_logger.info("System shutdown by user interrupt")
        except Exception as e:
            startup_logger.error("Failed to launch Streamlit: %s", str(e))
            logger.error("Error launching app: %s", str(e))
            sys.exit(1)

if __name__ == "__main__":
    main()