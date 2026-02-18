#!/usr/bin/env python3
"""
Entry point for Resume Reader AI CLI.
Run: python run.py path/to/resume.pdf
"""

import sys

# Ensure package is importable when run from project root
if __name__ == "__main__":
    from app.main import main

    main()
