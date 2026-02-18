"""
Basic tests for Resume Reader AI (no API calls).
Run from project root: pytest tests/
"""

import os

import pytest


def test_imports():
    """Package and main components can be imported."""
    from resume_reader import ResumeAgent, __version__

    assert __version__ == "0.1.0"
    assert ResumeAgent is not None


def test_agent_requires_api_key():
    """ResumeAgent raises when no API key is provided and env is unset."""
    from resume_reader import ResumeAgent

    key = os.environ.pop("GOOGLE_API_KEY", None)
    try:
        with pytest.raises(ValueError, match="Google API key is required"):
            ResumeAgent(api_key=None)
    finally:
        if key is not None:
            os.environ["GOOGLE_API_KEY"] = key


def test_config_constants():
    """Config module exposes expected constants."""
    from resume_reader.config import DEFAULT_MODEL, ENV_GOOGLE_API_KEY

    assert DEFAULT_MODEL == "gemini-2.5-flash"
    assert ENV_GOOGLE_API_KEY == "GOOGLE_API_KEY"
