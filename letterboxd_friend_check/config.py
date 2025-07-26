"""
Configuration manager for the Letterboxd Friend Check application
"""

import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for the Letterboxd Friend Check application"""

    def __init__(self, config_path=None):
        """Initialize the configuration manager"""
        # Default configuration values
        self._config = {
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

    def load(self):
        """Load configuration from file"""
        if not self.config_path.exists():
            logger.info(f"Configuration file not found: {self.config_path}")
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded_config = json.load(f)
                self._config.update(loaded_config)
            logger.info(f"Configuration loaded from {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")

    def save(self):
        """Save configuration to file"""
        try:
            # Ensure directory exists
            os.makedirs(self.config_path.parent, exist_ok=True)

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def __getitem__(self, key):
        """Get a configuration value"""
        return self._config.get(key)

    def __setitem__(self, key, value):
        """Set a configuration value"""
        self._config[key] = value

    def get(self, key, default=None):
        """Get a configuration value with a default"""
        return self._config.get(key, default)

    @property
    def username(self):
        """Get the username"""
        return self._config.get("username", "")

    @username.setter
    def username(self, value):
        """Set the username"""
        self._config["username"] = value

    @property
    def remember_user(self):
        """Get the remember user setting"""
        return self._config.get("remember_user", False)

    @remember_user.setter
    def remember_user(self, value):
        """Set the remember user setting"""
        self._config["remember_user"] = value

    @property
    def last_sync(self):
        """Get the last sync time"""
        return self._config.get("last_sync")

    @last_sync.setter
    def last_sync(self, value):
        """Set the last sync time"""
        self._config["last_sync"] = value
