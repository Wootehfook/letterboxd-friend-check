"""
Configuration manager for the Letterboxd Friend Check application
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Any, Dict, Union

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for the Letterboxd Friend Check application"""

    def __init__(self, config_path: Optional[Union[str, Path]] = None) -> None:
        """Initialize the configuration manager"""
        # Default configuration values
        self._config: Dict[str, Any] = {
            "username": "",
            "remember_user": False,
            "last_sync": None,
            "tmdb_api_key": "",
            "cookie_path": "",
            "database_path": "",
        }

        # Determine config file path
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Use the data directory within the package
            package_dir = Path(__file__).parent
            self.config_path = package_dir / "data" / "config.json"

        # Load config if it exists
        self.load()

    def load(self) -> None:
        """Load configuration from file"""
        if not self.config_path.exists():
            logger.info(f"Configuration file not found: {self.config_path}")
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded_config: Dict[str, Any] = json.load(f)
                self._config.update(loaded_config)
            logger.info(f"Configuration loaded from {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")

    def save(self) -> None:
        """Save configuration to file"""
        try:
            # Ensure directory exists
            os.makedirs(self.config_path.parent, exist_ok=True)

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def __getitem__(self, key: str) -> Any:
        """Get a configuration value"""
        return self._config.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Set a configuration value"""
        self._config[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value with a default"""
        return self._config.get(key, default)

    @property
    def username(self) -> str:
        """Get the username"""
        return self._config.get("username", "")

    @username.setter
    def username(self, value: str) -> None:
        """Set the username"""
        self._config["username"] = value

    @property
    def remember_user(self) -> bool:
        """Get the remember user setting"""
        return self._config.get("remember_user", False)

    @remember_user.setter
    def remember_user(self, value: bool) -> None:
        """Set the remember user setting"""
        self._config["remember_user"] = value

    @property
    def last_sync(self) -> Optional[str]:
        """Get the last sync time"""
        return self._config.get("last_sync")

    @last_sync.setter
    def last_sync(self, value: Optional[str]) -> None:
        """Set the last sync time"""
        self._config["last_sync"] = value
