"""
Logging configuration for TAES 2
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from src.config.settings import settings

def setup_logging():
    """Setup application logging"""
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Console output
            RotatingFileHandler(
                settings.LOG_FILE,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
        ]
    )
    
    # Create logger for TAES 2
    logger = logging.getLogger("taes2")
    logger.info("TAES 2 logging system initialized")
    
    return logger

# Initialize logger
logger = setup_logging()
