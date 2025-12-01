# plugins/example_plugin/tool.py
from typing import Optional

# Define a simple tool handler
def coolmath_tool(text: str) -> Optional[str]:
    if not text.lower().startswith("coolmath"):
        return None
    return "Cool math says: 2 + 2 = 4 🔥"

# Export as TOOL object for SuperPluginManager
class ToolHandler:
    def __init__(self, func, priority=15):
        self.func = func
        self.priority = priority

TOOL = ToolHandler(coolmath_tool, priority=15)

