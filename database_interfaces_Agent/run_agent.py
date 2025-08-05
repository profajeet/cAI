#!/usr/bin/env python3
"""
Simple launcher for Database Interface Agent.
This script handles Python path setup and launches the agent.
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import and run the main CLI
from scripts.run_agent import main

if __name__ == "__main__":
    main() 