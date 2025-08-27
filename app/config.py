"""
Configuration settings for Digital Freight Matcher application.

This module contains configuration settings for various components
including the new OSMnx route calculation service.
"""

import os
import logging
from typing import Dict, Any


def setup_logging(level: str = "INFO") -> None:
    """
    Set up logging configuration for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('dfm.log', mode='a')
        ]
    )
    
    # Set specific logger levels
    logging.getLogger('osmnx').setLevel(logging.WARNING)
    logging.getLogger('networkx').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")


def get_osmnx_config() -> Dict[str, Any]:
    """
    Get OSMnx configuration settings.
    
    Returns:
        Dictionary containing OSMnx configuration parameters
    """
    return {
        # Cache settings
        "cache_enabled": os.getenv("OSMNX_CACHE_ENABLED", "true").lower() == "true",
        "cache_max_age_hours": int(os.getenv("OSMNX_CACHE_MAX_AGE_HOURS", "24")),
        
        # Network settings
        "network_timeout_seconds": int(os.getenv("OSMNX_NETWORK_TIMEOUT", "30")),
        "network_type": os.getenv("OSMNX_NETWORK_TYPE", "drive"),
        
        # Fallback settings
        "fallback_speed_kmh": float(os.getenv("OSMNX_FALLBACK_SPEED", "80.0")),
        
        # Bounding box settings
        "base_padding_km": float(os.getenv("OSMNX_BASE_PADDING", "10.0")),
        "min_padding_km": float(os.getenv("OSMNX_MIN_PADDING", "5.0")),
        "max_padding_km": float(os.getenv("OSMNX_MAX_PADDING", "50.0")),
        "adaptive_padding": os.getenv("OSMNX_ADAPTIVE_PADDING", "true").lower() == "true",
        
        # Performance settings
        "batch_size": int(os.getenv("OSMNX_BATCH_SIZE", "10")),
        "max_retries": int(os.getenv("OSMNX_MAX_RETRIES", "3")),
        
        # Development settings
        "debug_mode": os.getenv("OSMNX_DEBUG", "false").lower() == "true",
        "log_level": os.getenv("OSMNX_LOG_LEVEL", "INFO").upper()
    }


def get_database_config() -> Dict[str, Any]:
    """
    Get database configuration settings.
    
    Returns:
        Dictionary containing database configuration parameters
    """
    return {
        "database_url": os.getenv("DATABASE_URL", "sqlite:///logistics.db"),
        "echo": os.getenv("DB_ECHO", "false").lower() == "true"
    }


def get_api_config() -> Dict[str, Any]:
    """
    Get API configuration settings.
    
    Returns:
        Dictionary containing API configuration parameters
    """
    return {
        "host": os.getenv("API_HOST", "0.0.0.0"),
        "port": int(os.getenv("API_PORT", "8000")),
        "debug": os.getenv("API_DEBUG", "false").lower() == "true",
        "reload": os.getenv("API_RELOAD", "false").lower() == "true"
    }


# Initialize logging when module is imported
setup_logging(os.getenv("LOG_LEVEL", "INFO"))

# Create logger for this module
logger = logging.getLogger(__name__)
logger.info("Configuration module loaded")