"""
Resume Reader AI: AI-powered resume interview agent using Google Gemini.
"""

from .agent import ResumeAgent
from .cli import main
from .config import DEFAULT_MODEL, ENV_GOOGLE_API_KEY

__version__ = "0.1.0"
__all__ = ["ResumeAgent", "main", "DEFAULT_MODEL", "ENV_GOOGLE_API_KEY"]
