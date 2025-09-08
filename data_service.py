#!/usr/bin/env python3
"""
Hybrid Data Service for Digital Freight Matching System
Supports both direct database access and API mode
"""

import os
import sys
import argparse
import yaml
import requests
import logging
from typing import Dict, List, Union, Optional
from sqlmodel import Session

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import engine
from db_manager import DatabaseManager, SystemStatus

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataConfig:
    """Configuration management with multiple source priority"""

    def __init__(self, cli_args=None):
        self.config_file_path = os.path.join(os.path.dirname(__file__), 'config', 'settings.yaml')
        self._config_data = self._load_config()
        self._cli_args = cli_args or {}

        # Set configuration with priority: CLI args > Env vars > Config file > Defaults
        self.environment = self._get_environment()
        self.mode = self._get_mode()
        self.api_url = self._get_api_url()
        self.api_timeout = self._get_api_timeout()
        self.database_path = self._get_database_path()

        logger.info(f"DataConfig initialized: mode={self.mode}, env={self.environment}")

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(self.config_file_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.config_file_path}")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing config file: {e}")
            return {}

    def _get_environment(self) -> str:
        """Get current environment"""
        return (
            self._cli_args.get('environment') or
            os.environ.get('DFM_ENV') or
            self._config_data.get('dashboard', {}).get('default_environment', 'development')
        )

    def _get_mode(self) -> str:
        """Get data access mode with priority"""
        env_config = self._config_data.get(self.environment, {}).get('data_access', {})
        default_config = self._config_data.get('data_access', {})

        return (
            self._cli_args.get('mode') or
            os.environ.get('DFM_DATA_MODE') or
            env_config.get('mode') or
            default_config.get('mode', 'direct')
        )

    def _get_api_url(self) -> str:
        """Get API URL with priority"""
        env_config = self._config_data.get(self.environment, {}).get('data_access', {})
        default_config = self._config_data.get('data_access', {})

        return (
            self._cli_args.get('api_url') or
            os.environ.get('DFM_API_URL') or
            env_config.get('api_url') or
            default_config.get('api_url', 'http://localhost:8000')
        )

    def _get_api_timeout(self) -> int:
        """Get API timeout with priority"""
        env_config = self._config_data.get(self.environment, {}).get('data_access', {})
        default_config = self._config_data.get('data_access', {})

        timeout_str = (
            self._cli_args.get('api_timeout') or
            os.environ.get('DFM_API_TIMEOUT') or
            str(env_config.get('api_timeout', '')) or
            str(default_config.get('api_timeout', 30))
        )

        try:
            return int(timeout_str)
        except ValueError:
            return 30

    def _get_database_path(self) -> str:
        """Get database path with priority"""
        env_config = self._config_data.get(self.environment, {}).get('data_access', {})
        default_config = self._config_data.get('data_access', {})

        return (
            self._cli_args.get('database_path') or
            os.environ.get('DFM_DATABASE_PATH') or
            env_config.get('database_path') or
            default_config.get('database_path', 'logistics.db')
        )


class APIClient:
    """HTTP client wrapper for API mode"""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Cannot connect to API at {self.base_url}")
        except requests.exceptions.Timeout:
            raise TimeoutError(f"API request timed out after {self.timeout}s")
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"API error: {e.response.status_code} - {e.response.text}")

    # CRUD Operations
    def get_all(self, entity_type: str) -> List[Dict]:
        """Get all entities of a specific type"""
        return self._make_request('GET', f'/{entity_type}')

    def get_by_id(self, entity_type: str, entity_id: int) -> Dict:
        """Get entity by ID"""
        return self._make_request('GET', f'/{entity_type}/{entity_id}')

    def create(self, entity_type: str, data: Dict) -> Dict:
        """Create new entity"""
        return self._make_request('POST', f'/{entity_type}', json=data)

    def update(self, entity_type: str, entity_id: int, data: Dict) -> Dict:
        """Update entity"""
        return self._make_request('PUT', f'/{entity_type}/{entity_id}', json=data)

    def delete(self, entity_type: str, entity_id: int) -> Dict:
        """Delete entity"""
        return self._make_request('DELETE', f'/{entity_type}/{entity_id}')

    def health_check(self) -> Dict:
        """Check API health"""
        return self._make_request('GET', '/health')

    def get_summary(self) -> Dict:
        """Get system summary"""
        return self._make_request('GET', '/summary')


class DataService:
    """Unified data service supporting both direct DB and API modes"""

    def __init__(self, config: DataConfig):
        self.config = config
        self.mode = config.mode

        if self.mode == "api":
            self.api_client = APIClient(config.api_url, config.api_timeout)
            self.db_manager = None
            logger.info(f"DataService initialized in API mode: {config.api_url}")
        else:
            self.api_client = None
            # Initialize DB manager with session
            self.session = Session(engine)
            self.db_manager = DatabaseManager(self.session)
            logger.info("DataService initialized in direct database mode")

    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'session') and self.session:
            self.session.close()

    def health_check(self) -> Dict:
        """Check system health"""
        if self.mode == "api":
            try:
                return self.api_client.health_check()
            except Exception as e:
                return {"status": "error", "message": str(e)}
        else:
            try:
                # Test database connection
                from sqlmodel import text
                with Session(engine) as session:
                    session.execute(text("SELECT 1"))
                return {"status": "healthy", "message": "Database connection OK"}
            except Exception as e:
                return {"status": "error", "message": f"Database error: {e}"}

    def get_system_status(self) -> Union[Dict, SystemStatus]:
        """Get system status - returns different formats based on mode"""
        if self.mode == "api":
            return self.api_client.get_summary()
        else:
            return self.db_manager.get_system_status()

    def initialize_database(self, force_reinit: bool = False) -> bool:
        """Initialize database (direct mode only)"""
        if self.mode == "api":
            raise RuntimeError("Database initialization not available in API mode")
        return self.db_manager.initialize_database(force_reinit)

    def verify_integrity(self) -> Dict:
        """Verify database integrity"""
        if self.mode == "api":
            return self.api_client.get_summary()
        else:
            return self.db_manager.verify_integrity()

    def reset_database(self, confirm: bool = False) -> bool:
        """Reset database (direct mode only)"""
        if self.mode == "api":
            raise RuntimeError("Database reset not available in API mode")
        return self.db_manager.reset_database(confirm)

    # CRUD Operations (unified interface)
    def get_all(self, entity_type: str) -> List[Dict]:
        """Get all entities of a specific type"""
        if self.mode == "api":
            return self.api_client.get_all(entity_type)
        else:
            # Map entity types to database queries
            entity_mapping = {
                'trucks': 'trucks',
                'orders': 'orders',
                'routes': 'routes',
                'clients': 'clients',
                'locations': 'locations',
                'packages': 'packages',
                'cargo': 'cargo_loads'
            }

            if entity_type in entity_mapping:
                # For now, return empty list - would need to implement DB queries
                # TODO: Implement direct database CRUD operations
                return []
            else:
                raise ValueError(f"Unknown entity type: {entity_type}")

    def create_entity(self, entity_type: str, data: Dict) -> Dict:
        """Create new entity"""
        if self.mode == "api":
            return self.api_client.create(entity_type, data)
        else:
            # TODO: Implement direct database creation
            raise NotImplementedError("Direct database CRUD not yet implemented")


def parse_cli_args() -> Dict:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Digital Freight Matching Data Service')
    parser.add_argument('--mode', choices=['direct', 'api'],
                       help='Data access mode')
    parser.add_argument('--api-url', dest='api_url',
                       help='API URL (for API mode)')
    parser.add_argument('--api-timeout', dest='api_timeout', type=int,
                       help='API timeout in seconds')
    parser.add_argument('--database-path', dest='database_path',
                       help='Database file path (for direct mode)')
    parser.add_argument('--environment', choices=['development', 'production'],
                       help='Environment configuration')

    args = parser.parse_args()
    return {k: v for k, v in vars(args).items() if v is not None}


def create_data_service(cli_args=None) -> DataService:
    """Factory function to create configured DataService"""
    config = DataConfig(cli_args)
    return DataService(config)


if __name__ == "__main__":
    # Test the data service
    cli_args = parse_cli_args()
    service = create_data_service(cli_args)

    print(f"DataService created in {service.mode} mode")

    # Test health check
    health = service.health_check()
    print(f"Health check: {health}")

    # Test system status
    try:
        status = service.get_system_status()
        print(f"System status: {status}")
    except Exception as e:
        print(f"Error getting system status: {e}")
