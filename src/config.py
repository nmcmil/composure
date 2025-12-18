"""Configuration manager for Composure."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    """
    Singleton configuration manager.
    Handles loading and saving application configuration.
    """
    
    _instance = None
    
    DEFAULT_CONFIG = {
        'shortcuts': {
            'capture-selection': '<Primary><Shift>a',
            'capture-window': '<Primary><Shift>b',
            'capture-screen': '<Primary><Shift>c',
            'copy': '<Primary>c',
            'copy-and-close': '<Primary><Shift>Return'
        },
        'defaults': {
            'preset_id': None
        }
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
            
        self._config_dir = self._get_config_dir()
        self._config_file = self._config_dir / 'config.json'
        self._config = self.DEFAULT_CONFIG.copy()
        
        self.load()
        self._initialized = True
        
    def _get_config_dir(self) -> Path:
        """Get the configuration directory path."""
        config_dir = Path(os.environ.get('XDG_CONFIG_HOME', 
                                          Path.home() / '.config'))
        return config_dir / 'composure'
        
    def load(self) -> None:
        """Load configuration from disk."""
        if not self._config_file.exists():
            return
            
        try:
            with open(self._config_file, 'r') as f:
                saved_config = json.load(f)
                # Deep merge with defaults to ensure all keys exist
                self._merge_config(self._config, saved_config)
        except Exception as e:
            print(f"Failed to load config: {e}")
            
    def _merge_config(self, current: Dict, updates: Dict) -> None:
        """Recursively update dictionary."""
        for key, value in updates.items():
            if isinstance(value, dict) and key in current and isinstance(current[key], dict):
                self._merge_config(current[key], value)
            else:
                current[key] = value
                
    def save(self) -> None:
        """Save configuration to disk."""
        self._config_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self._config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            print(f"Failed to save config: {e}")
            
    def get_shortcut(self, action_name: str) -> str:
        """Get shortcut for an action."""
        return self._config['shortcuts'].get(action_name, '')
        
    def set_shortcut(self, action_name: str, accelerator: str) -> None:
        """Set shortcut for an action."""
        self._config['shortcuts'][action_name] = accelerator
        self.save()
        
    def get_default_preset(self) -> Optional[str]:
        """Get the default preset ID."""
        return self._config['defaults'].get('preset_id')
        
    def set_default_preset(self, preset_id: Optional[str]) -> None:
        """Set the default preset ID."""
        self._config['defaults']['preset_id'] = preset_id
        self.save()
