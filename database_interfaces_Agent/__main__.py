#!/usr/bin/env python3
"""
Main entry point for Database Interface Agent.
Allows running the package with: python -m database_interfaces_Agent
"""

import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the main CLI
from scripts.run_agent import main

if __name__ == "__main__":
    main() 