"""
GodBot main entry point for CLI usage
"""
import os
import sys

# Phase 11.1 logging
from godbot.core.logging import get_logger

log = get_logger(__name__)

def main():
    """Start the Discord bot."""
    log.info("Starting Discord bot...")
    # Add parent directory to path so we can import main.py modules
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    
    try:
        # Import main - this will execute client.run(TOKEN) at module level
        import main
    except Exception as e:
        log.error(f"Bot crashed: {e}", exc_info=True)
        raise
