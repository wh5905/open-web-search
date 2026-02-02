import sys
from loguru import logger
from open_web_search.config import LinkerConfig

def configure_logging(config: LinkerConfig):
    # Remove default handler
    logger.remove()
    
    # Stderr handler (Human readable)
    log_level = "DEBUG" if config.observability_level == "full" else "INFO"
    logger.add(sys.stderr, level=log_level, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    
    # File handler (JSON for observability tools)
    if config.observability_level == "full":
        logger.add("open_web_search.log", rotation="10 MB", serialize=True, level="DEBUG")
    else:
        logger.add("open_web_search.log", rotation="10 MB", level="INFO")

def get_logger():
    return logger
