# Resume Reader AI

An intelligent AI agent that reads PDF resumes and conducts interactive interviews by asking relevant questions about the candidate's experience, skills, and background.

## Features

- **PDF Resume Reading**: Extracts text from PDF resumes using `pdfplumber`
- **AI-Powered Questions**: Uses Google Gemini to generate intelligent, context-aware questions
- **Interactive Interview**: Conducts a natural conversation flow
- **Follow-up Questions**: Generates dynamic follow-up questions based on your responses
- **Smart Questioning**: Asks about experiences, skills, career transitions, and achievements
- **Interview Summary**: End-of-session summary with questions and responses
- **Rate Limit Handling**: Automatic retry with backoff for API quota errors

## Project Structure

```
Resume Reader AI/
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── requirements.txt
├── pyproject.toml
├── run.py                 # CLI entry point (python run.py resume.pdf)
├── src/
│   └── resume_reader/
│       ├── __init__.py
│       ├── agent.py       # ResumeAgent logic
│       ├── cli.py         # Argument parsing and main()
│       └── config.py      # Constants and settings
└── tests/
    ├── __init__.py
    └── test_agent.py
```

## Installation

1. **Clone or navigate to the project:**
   ```bash
   cd "Resume Reader AI"
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # source .venv/bin/activate  # Linux/macOS
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   Or install the package in editable mode (enables `resume-reader` command):
   ```bash
   pip install -e .
   ```

4. **Set up Google API key**
   - Copy `.env.example` to `.env`
   - Add your key: `GOOGLE_API_KEY=your_api_key_here`
   - Get a key from: https://makersuite.google.com/app/apikey

## Usage

### Basic (from project root)

```bash
python run.py path/to/resume.pdf
```

### With options

```bash
# More questions
python run.py resume.pdf --questions 10

# No follow-ups
python run.py resume.pdf --no-followups

# API key and debug
python run.py resume.pdf --api-key YOUR_KEY --debug
```

### If installed with `pip install -e .`

```bash
resume-reader path/to/resume.pdf
resume-reader resume.pdf --questions 10 --debug
```

### Interactive commands

- Type your answer to respond
- `skip` — skip current question
- `quit` — end the interview

## How It Works

1. **PDF Reading**: `pdfplumber` extracts text from your PDF resume.
2. **Question Generation**: Google Gemini (configurable in `src/resume_reader/config.py`) generates questions from the resume.
3. **Interview**: You answer in the terminal; optional follow-up questions are generated from your answers.
4. **Summary**: At the end you see total questions, responses, and a recap.

## Configuration

- **Model**: Edit `DEFAULT_MODEL` in `src/resume_reader/config.py` (e.g. `gemini-2.5-pro`).
- **Resume length**: `RESUME_MAX_CHARS_QUESTIONS` and `RESUME_MAX_CHARS_FOLLOWUP` in `config.py`.
- **Environment**: Use `.env` or `GOOGLE_API_KEY` in your environment.

## Requirements

- Python 3.8+
- Google API key
- PDF resume file

## API Quota & Rate Limits

- **Free tier**: 20 requests per day per model.
- The app retries on rate limit errors with backoff.
- Upgrade or check usage: https://ai.google.dev/pricing, https://ai.dev/rate-limit

## Tests

From project root:

```bash
pip install -e ".[dev]"
pytest tests/
```

## License

MIT License.
