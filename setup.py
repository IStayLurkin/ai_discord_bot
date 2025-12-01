#!/usr/bin/env python3
"""
Quick setup script to verify installation
"""
import sys
import subprocess

def check_python():
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ required")
        return False
    print("✅ Python version OK")
    return True

def check_ollama():
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama installed")
            return True
    except:
        pass
    print("⚠️  Ollama not found - install from https://ollama.com/download")
    return False

def check_dependencies():
    required = [
        "discord.py",
        "requests",
        "flask",
        "flask_cors"
    ]
    missing = []
    for dep in required:
        try:
            __import__(dep.replace("-", "_"))
        except ImportError:
            missing.append(dep)
    
    if missing:
        print(f"⚠️  Missing: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    print("✅ Core dependencies installed")
    return True

def main():
    print("Checking setup...\n")
    checks = [
        check_python(),
        check_ollama(),
        check_dependencies()
    ]
    
    if all(checks):
        print("\n✅ Setup complete! Edit main.py and set your Discord bot token.")
        print("Then run: python main.py")
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")

if __name__ == "__main__":
    main()

