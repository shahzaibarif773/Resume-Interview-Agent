"""
Configuration and constants for Resume Reader AI.
"""

# Default Gemini model (stable, fast, cost-effective)
DEFAULT_MODEL = "gemini-2.5-flash"

# Resume text limits for prompts (characters)
RESUME_MAX_CHARS_QUESTIONS = 4000
RESUME_MAX_CHARS_FOLLOWUP = 2000

# Generation defaults
DEFAULT_NUM_QUESTIONS = 5
MAX_OUTPUT_TOKENS_QUESTIONS = 1000
MAX_OUTPUT_TOKENS_FOLLOWUP = 200

# Retry settings for rate limits
MAX_RETRIES = 3
INITIAL_RETRY_DELAY_SECONDS = 5

# Environment
ENV_GOOGLE_API_KEY = "GOOGLE_API_KEY"
