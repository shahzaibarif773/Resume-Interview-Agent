# AI Resume Interview Agent

An intelligent AI agent that reads PDF resumes and conducts interactive interviews by asking relevant questions about the candidate's experience, skills, and background.

## Features

- 📄 **PDF Resume Reading**: Extracts text from PDF resumes using `pdfplumber`
- 🤖 **AI-Powered Questions**: Uses Google Gemini to generate intelligent, context-aware questions
- 💬 **Interactive Interview**: Conducts a natural conversation flow
- 🔄 **Follow-up Questions**: Generates dynamic follow-up questions based on your responses
- 🎯 **Smart Questioning**: Asks about experiences, skills, career transitions, and achievements

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Google API Key:**
   
   Create a `.env` file in the project directory:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```
   
   Get your API key from: https://makersuite.google.com/app/apikey
   
   Or set it as an environment variable:
   ```bash
   # Windows (PowerShell)
   $env:GOOGLE_API_KEY="your_api_key_here"
   
   # Linux/Mac
   export GOOGLE_API_KEY="your_api_key_here"
   ```

## Usage

### Basic Usage

```bash
python resume_agent.py path/to/resume.pdf
```

### Advanced Usage

```bash
# Ask 10 questions instead of default 5
python resume_agent.py resume.pdf --questions 10

# Disable follow-up questions
python resume_agent.py resume.pdf --no-followups

# Specify API key directly
python resume_agent.py resume.pdf --api-key your_key_here

# Enable debug output to see AI responses
python resume_agent.py resume.pdf --debug
```

### Interactive Commands

During the interview:
- Type your answer normally to respond to questions
- Type `skip` to skip the current question
- Type `quit` to end the interview early

## Example Session

```
============================================================
📄 Resume Interview Agent
============================================================

📖 Reading resume from: john_doe_resume.pdf
✅ Successfully loaded resume (2847 characters)

🤔 Generating 5 questions...
✅ Generated 5 questions

============================================================
💬 Interview Session
============================================================

[Question 1/5]
🤖 Agent: Can you tell me more about your experience leading the cross-functional team at TechCorp?

👤 You: I managed a team of 8 developers and designers to deliver a mobile app that increased user engagement by 40%...

🤖 Agent: What specific challenges did you face while managing that team, and how did you overcome them?

👤 You: The main challenge was aligning different departments...
```

## How It Works

1. **PDF Reading**: The agent uses `pdfplumber` to extract all text from your PDF resume
2. **Question Generation**: Google Gemini analyzes the resume content and generates relevant questions
3. **Interactive Flow**: You answer questions naturally through the command line
4. **Follow-ups**: Based on your responses, the AI generates contextual follow-up questions

## Requirements

- Python 3.8+
- Google API key (get one at https://makersuite.google.com/app/apikey)
- PDF resume file

## Dependencies

- `google-generativeai`: For AI-powered question generation using Google Gemini
- `pdfplumber`: For PDF text extraction
- `python-dotenv`: For environment variable management

## Features

- **Smart Question Parsing**: Automatically extracts and cleans questions from AI responses
- **Interview Summary**: At the end of the interview, you'll see a summary with:
  - Total questions asked
  - Total responses received
  - Questions skipped (if any)
  - Full list of questions and responses discussed
- **Debug Mode**: Use `--debug` flag to see raw AI responses for troubleshooting
- **Robust Error Handling**: Handles incomplete or malformed AI responses gracefully

## Notes

- The agent uses Google Gemini 2.5 Flash model for question generation (stable, fast and cost-effective)
- You can change the model to `gemini-2.5-pro` in the code for better quality if needed
- Resume content is limited to 4000 characters for initial questions to stay within token limits
- Conversation history is maintained for context-aware follow-up questions
- Questions are automatically cleaned and deduplicated

## API Quota & Rate Limits

**Free Tier Limits:**
- 20 requests per day per model
- Rate limits apply

**If you hit quota limits:**
- The script will automatically retry with exponential backoff
- Wait a few minutes between sessions
- Consider upgrading your plan at: https://ai.google.dev/pricing
- Check your usage at: https://ai.dev/rate-limit

**Error Handling:**
- The script includes automatic retry logic for rate limit errors
- Clear error messages will guide you if quota is exceeded

## License

MIT License - Feel free to use and modify as needed!
