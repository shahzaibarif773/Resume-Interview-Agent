"""
Prompt templates for question and follow-up generation.
"""

from app.config import RESUME_MAX_CHARS_FOLLOWUP, RESUME_MAX_CHARS_QUESTIONS


def build_questions_prompt(resume_text: str, num_questions: int) -> str:
    """Build the prompt for generating interview questions from resume content."""
    snippet = resume_text[:RESUME_MAX_CHARS_QUESTIONS]
    return f"""You are a professional recruiter who asks insightful questions about resumes.

You are a professional recruiter reviewing a resume. Based on the following resume content, generate exactly {num_questions} complete, thoughtful questions.

Resume Content:
{snippet}

Generate {num_questions} questions that:
1. Clarify specific experiences or achievements mentioned
2. Explore skills and technologies in more depth
3. Understand career transitions or decisions
4. Assess cultural fit and work style
5. Dive deeper into notable accomplishments

CRITICAL FORMATTING RULES:
- Generate EXACTLY {num_questions} complete questions
- Each question must be a FULL, COMPLETE sentence ending with a question mark (?)
- Each question must be on its own line (separated by newlines)
- Do NOT include numbering, bullets, or any prefixes
- Do NOT include any text before or after the questions
- Each question should be 10-30 words long
- Return ONLY the {num_questions} questions, one per line, nothing else

Example of correct format:
What technologies did you use in your Flutter projects?
Can you tell me more about your team leadership experience?
How did you handle the migration to Flutter?
What challenges did you face while working on the e-commerce app?
Why did you decide to transition to mobile development?"""


def build_followup_prompt(resume_text: str, conversation_context: str) -> str:
    """Build the prompt for generating a single follow-up question."""
    snippet = resume_text[:RESUME_MAX_CHARS_FOLLOWUP]
    return f"""You are a professional recruiter having a natural conversation.

Based on the resume and the conversation so far, generate ONE insightful follow-up question that digs deeper into what the candidate just said.

Resume Summary:
{snippet}

Recent Conversation:
{conversation_context}

Generate a single, thoughtful follow-up question that:
- Builds on their previous answer
- Shows genuine interest
- Helps you understand them better
- Is specific and relevant
- MUST start with a question word (What, How, Why, When, Where, Who, Can, Could, Would, Did, etc.)
- MUST be a complete question ending with a question mark

IMPORTANT: Return ONLY the question, nothing else. Do NOT include statements or comments."""
