#!/usr/bin/env python3
"""
Standalone script to run Greenhouse automation.
Can be run directly: python3 run.py input.json
"""
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from greenhouse_automation.main import main

if __name__ == "__main__":
    main()


