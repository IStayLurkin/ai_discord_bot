# plugins/plugin_manager.py
import os
import json
import time
import importlib
from types import ModuleType
from typing import Dict, Optional

from deterministic.registry import register_handler
from .plugin_sandbox import safe_exec
from .plugin_loader import load_plugin_code

PLUGIN_DIR = os.path.join(os.getcwd(), "plugins")

class Plugin:
    def __init__(self, name: str, folder: str, manifest: dict):
        self.name = name
        self.folder = folder
        self.manifest = manifest
        self.module: Optional[ModuleType] = None
        self.behavior_injection = None
        self.last_loaded = 0

class SuperPluginManager:
    def __init__(self) -> None:
        self.plugins: Dict[str, Plugin] = {}
        self.behavior_injections = []
        self.scan_and_load_all()

    # --------------------------------------------------------
    # MAIN LOADERS
    # --------------------------------------------------------
    def scan_and_load_all(self):
        if not os.path.exists(PLUGIN_DIR):
            os.makedirs(PLUGIN_DIR, exist_ok=True)
            return

        for name in os.listdir(PLUGIN_DIR):
            folder = os.path.join(PLUGIN_DIR, name)
            if os.path.isdir(folder):
                self.load_plugin_from_folder(folder)

    def load_plugin_from_folder(self, folder: str):
        manifest_path = os.path.join(folder, "manifest.json")
        if not os.path.exists(manifest_path):
            return

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        name = manifest.get("name")
        if not name:
            print(f"[Plugin] Manifest missing name in {folder}")
            return

        plugin = Plugin(name, folder, manifest)
        self.plugins[name] = plugin
        self.reload_plugin(plugin)

    # --------------------------------------------------------
    # HOT RELOAD LOGIC
    # --------------------------------------------------------
    def reload_plugin(self, plugin: Plugin):
        tool_path = os.path.join(plugin.folder, "tool.py")
        behavior_path = os.path.join(plugin.folder, "behavior.txt")

        # Skip if file hasn't changed
        if not os.path.exists(tool_path):
            return False

        mtime = os.path.getmtime(tool_path)
        if mtime <= plugin.last_loaded:
            return False

        plugin.last_loaded = mtime
        print(f"[Plugin] Reloading {plugin.name}")

        plugin_code = load_plugin_code(tool_path)
        sandbox_globals = safe_exec(plugin_code)

        # Register deterministic tools
        if "TOOL" in sandbox_globals:
            handler_obj = sandbox_globals["TOOL"]
            if hasattr(handler_obj, "func") and hasattr(handler_obj, "priority"):
                register_handler(priority=handler_obj.priority)(handler_obj.func)
            elif callable(handler_obj):
                # Fallback: if TOOL is directly a function, register with default priority
                register_handler(priority=100)(handler_obj)

        # Load behavior injection
        if os.path.exists(behavior_path):
            with open(behavior_path, "r", encoding="utf-8") as f:
                behavior = f.read().strip()
                plugin.behavior_injection = behavior
                if behavior not in self.behavior_injections:
                    self.behavior_injections.append(behavior)

        plugin.module = sandbox_globals
        return True

    # --------------------------------------------------------
    # AUTO UPDATE LOOP
    # --------------------------------------------------------
    def auto_update(self):
        for plugin in self.plugins.values():
            self.reload_plugin(plugin)

    # --------------------------------------------------------
    # COMPATIBILITY METHODS (for existing code)
    # --------------------------------------------------------
    def load_all(self):
        """Compatibility method - already done in __init__"""
        pass

    def list_plugins(self):
        return list(self.plugins.keys())

    def install_from_folder(self, src):
        name = os.path.basename(src)
        dst = os.path.join(PLUGIN_DIR, name)
        if os.path.exists(dst):
            import shutil
            shutil.rmtree(dst)
        import shutil
        shutil.copytree(src, dst)
        self.load_plugin_from_folder(dst)
        return name

    def remove(self, name):
        path = os.path.join(PLUGIN_DIR, name)
        if os.path.exists(path):
            import shutil
            shutil.rmtree(path)
            if name in self.plugins:
                del self.plugins[name]
            return True
        return False
