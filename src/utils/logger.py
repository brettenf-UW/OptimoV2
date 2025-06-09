"""
Logger utilities for OptimoV2
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional


def setup_logger(name: str, config: Dict, log_dir: Optional[Path] = None) -> logging.Logger:
    """Setup a logger with file and console handlers"""
    
    logger = logging.getLogger(name)
    
    # Set level from config
    level = getattr(logging, config.get('logging', {}).get('level', 'INFO'))
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Create formatter
    formatter = logging.Formatter(
        config.get('logging', {}).get('format', '%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_dir provided)
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger