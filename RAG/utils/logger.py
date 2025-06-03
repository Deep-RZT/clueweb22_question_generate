import logging
import os
from datetime import datetime
from config import OUTPUT_DIRS

def setup_logger(name="energy_crawler", level=logging.INFO):
    """
    Setup logger for the energy crawler
    """
    # Create logs directory if it doesn't exist
    os.makedirs(OUTPUT_DIRS["logs"], exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create file handler
    log_file = os.path.join(
        OUTPUT_DIRS["logs"], 
        f"crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_progress(logger, current, total, source=""):
    """
    Log progress information
    """
    percentage = (current / total) * 100 if total > 0 else 0
    logger.info(f"{source} Progress: {current}/{total} ({percentage:.1f}%)") 