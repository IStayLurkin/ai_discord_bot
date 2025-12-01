# plugins/plugin_loader.py
def load_plugin_code(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

