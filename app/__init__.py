"""
Resume-Interview-Agent: AI-powered resume interview agent using Google Gemini.
"""

from app.agent.agent import ResumeAgent
from app.main import main
from app.config import DEFAULT_MODEL, ENV_GOOGLE_API_KEY

__version__ = "0.1.0"
__all__ = ["ResumeAgent", "main", "DEFAULT_MODEL", "ENV_GOOGLE_API_KEY"]
