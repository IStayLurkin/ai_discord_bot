"""
Base Plugin Class (Phase 11.2)
------------------------------
All GodBot plugins must inherit from BasePlugin.
"""

from __future__ import annotations

from typing import Optional, Any, Dict


class BasePlugin:
    """
    Every plugin MUST implement:
        - name (str)
        - version (str)
        - author (str)

    Optional:
        - on_load(bot)
        - on_unload(bot)
        - on_reload(bot)
    """

    name: str = "Unknown Plugin"
    version: str = "0.0.0"
    author: str = "Unknown"

    def on_load(self, bot: Any) -> None:
        pass

    def on_unload(self, bot: Any) -> None:
        pass

    def on_reload(self, bot: Any) -> None:
        pass

