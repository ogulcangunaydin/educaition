"""
DEPRECATED: Import from app.core.config instead.

This module re-exports from app.core.config for backward compatibility.
"""

from app.core.config import Environment, Settings, get_settings, settings

__all__ = ["Environment", "Settings", "get_settings", "settings"]
