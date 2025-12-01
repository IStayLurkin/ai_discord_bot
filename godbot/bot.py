"""
GodBot main entry point for CLI usage
"""
import os
import sys

def main():
    """Start the Discord bot."""
    # Add parent directory to path so we can import main.py modules
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    
    # Import main - this will execute client.run(TOKEN) at module level
    import main
