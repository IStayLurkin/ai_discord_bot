# plugins/plugin_sandbox.py
def safe_exec(code: str):
    """
    TEMPORARY: run plugin code with normal globals.
    A proper sandbox will be added in Phase 15.
    """
    sandbox_globals = {}
    exec(code, sandbox_globals)
    return sandbox_globals
