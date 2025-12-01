"""
Plugin Loader (Phase 11.2)
--------------------------
Auto-discovers, loads, reloads plugins safely.
"""

from __future__ import annotations

import importlib
import os
import sys
from types import ModuleType
from typing import Dict, Any, List

from godbot.core.logging import get_logger
log = get_logger(__name__)


PLUGIN_PATHS = [
    "godbot/plugins",
    "plugins/custom",
]


class PluginManager:
    def __init__(self):
        self.loaded_plugins: Dict[str, ModuleType] = {}

    # ---------------------------
    # Discover plugin paths
    # ---------------------------
    def discover_plugins(self) -> List[str]:
        found = []
        for path in PLUGIN_PATHS:
            if not os.path.exists(path):
                log.debug(f"Plugin path does not exist: {path}")
                continue
            for file in os.listdir(path):
                if file.endswith(".py") and file not in ["__init__.py", "base_plugin.py", "loader.py"]:
                    # Convert path to module name
                    module_name = f"{path}.{file[:-3]}".replace("/", ".").replace("\\", ".")
                    found.append(module_name)
        return found

    # ---------------------------
    # Load plugin
    # ---------------------------
    def load_plugin(self, module_name: str, bot: Any) -> bool:
        try:
            mod = importlib.import_module(module_name)

            # Must define "Plugin" class
            if not hasattr(mod, "Plugin"):
                log.error(f"Plugin {module_name} missing Plugin class")
                return False

            plugin_class = getattr(mod, "Plugin")
            plugin = plugin_class()

            plugin.on_load(bot)
            self.loaded_plugins[module_name] = mod

            log.info(f"Loaded plugin: {plugin.name} v{plugin.version} by {plugin.author}")
            return True

        except Exception as e:
            log.error(f"Failed to load plugin {module_name}: {e}", exc_info=True)
            return False

    # ---------------------------
    # Reload plugin
    # ---------------------------
    def reload_plugin(self, module_name: str, bot: Any) -> bool:
        if module_name not in self.loaded_plugins:
            log.error(f"Plugin not loaded: {module_name}")
            return False

        try:
            old = self.loaded_plugins[module_name]
            if hasattr(old, "Plugin"):
                plugin_class = getattr(old, "Plugin")
                plugin_instance = plugin_class()
                plugin_instance.on_unload(bot)

            mod = importlib.reload(old)
            plugin_class = getattr(mod, "Plugin")
            plugin_instance = plugin_class()
            plugin_instance.on_reload(bot)

            self.loaded_plugins[module_name] = mod

            log.info(f"Reloaded plugin: {module_name}")
            return True

        except Exception as e:
            log.error(f"Failed to reload plugin {module_name}: {e}", exc_info=True)
            return False

    # ---------------------------
    # List Plugins
    # ---------------------------
    def list_plugins(self) -> List[str]:
        return list(self.loaded_plugins.keys())


# Global plugin manager
plugin_manager = PluginManager()

