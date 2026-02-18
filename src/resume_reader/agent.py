"""
Resume Interview Agent: reads PDF resumes and conducts AI-powered interviews.
"""

import os
import re
import time
from typing import Dict, List, Optional

import google.generativeai as genai
import pdfplumber

from .config import (
    DEFAULT_MODEL,
    ENV_GOOGLE_API_KEY,
    INITIAL_RETRY_DELAY_SECONDS,
    MAX_OUTPUT_TOKENS_FOLLOWUP,
    MAX_OUTPUT_TOKENS_QUESTIONS,
    MAX_RETRIES,
    RESUME_MAX_CHARS_FOLLOWUP,
    RESUME_MAX_CHARS_QUESTIONS,
)


class ResumeAgent:
    """
    AI agent that reads PDF resumes and asks intelligent questions about them.
    """

    def __init__(self, api_key: Optional[str] = None, debug: bool = False):
        """
        Initialize the Resume Agent.

        Args:
            api_key: Google API key. If not provided, read from environment.
            debug: Enable debug output (default: False).
        """
        api_key = api_key or os.getenv(ENV_GOOGLE_API_KEY)
        if not api_key:
            raise ValueError(
                "Google API key is required. "
                f"Set it as {ENV_GOOGLE_API_KEY} environment variable or pass it to the constructor."
            )

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(DEFAULT_MODEL)
        self.resume_text: Optional[str] = None
        self.conversation_history: List[Dict[str, str]] = []
        self.debug = debug
        self.questions_asked: List[str] = []
        self.responses_received: List[str] = []

    def read_pdf(self, pdf_path: str) -> str:
        """
        Extract text from a PDF resume.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            Extracted text from the PDF.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        text_content = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}") from e

        self.resume_text = "\n\n".join(text_content)
        return self.resume_text

    def generate_questions(self, num_questions: int = 5) -> List[str]:
        """
        Generate intelligent questions about the resume using AI.

        Args:
            num_questions: Number of questions to generate.

        Returns:
            List of questions.
        """
        if not self.resume_text:
            raise ValueError("No resume loaded. Please read a PDF first.")

        resume_snippet = self.resume_text[:RESUME_MAX_CHARS_QUESTIONS]
        prompt = f"""You are a professional recruiter reviewing a resume. Based on the following resume content, generate exactly {num_questions} complete, thoughtful questions.

Resume Content:
{resume_snippet}

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

        full_prompt = "You are a professional recruiter who asks insightful questions about resumes.\n\n" + prompt
        retry_delay = INITIAL_RETRY_DELAY_SECONDS

        for attempt in range(MAX_RETRIES):
            try:
                response = self.model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,
                        max_output_tokens=MAX_OUTPUT_TOKENS_QUESTIONS,
                    ),
                )
                break
            except Exception as e:
                error_str = str(e).lower()
                if "429" in str(e) or "quota" in error_str or "rate limit" in error_str:
                    if attempt < MAX_RETRIES - 1:
                        delay_match = re.search(r"retry in ([\d.]+)s", error_str)
                        if delay_match:
                            retry_delay = int(float(delay_match.group(1))) + 2
                        else:
                            retry_delay = retry_delay * (attempt + 1)
                        print(
                            f"\n⚠️  Rate limit/quota exceeded. Retrying in {retry_delay} seconds... "
                            f"(Attempt {attempt + 1}/{MAX_RETRIES})"
                        )
                        time.sleep(retry_delay)
                        continue
                    raise Exception(
                        f"Quota/Rate limit exceeded after {MAX_RETRIES} attempts. "
                        "Free tier allows 20 requests per day per model. "
                        "Please wait or upgrade your plan at https://ai.google.dev/gemini-api/docs/rate-limits"
                    ) from e
                raise

        questions_text = response.text.strip()

        if self.debug:
            print(f"\n[DEBUG] Full AI response:\n{questions_text}\n")
            print(f"[DEBUG] Response length: {len(questions_text)} characters\n")

        lines = questions_text.split("\n")
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            cleaned = line.lstrip("0123456789.-*•() ").strip()
            if len(cleaned) < 10 or cleaned.isdigit():
                continue
            cleaned_lines.append(cleaned)

        questions_text = "\n".join(cleaned_lines)
        questions = []
        seen_questions = set()
        question_starters = (
            "what",
            "how",
            "why",
            "when",
            "where",
            "who",
            "can",
            "could",
            "would",
            "did",
            "do",
            "does",
            "have",
            "has",
            "tell",
            "describe",
            "explain",
        )

        for line in questions_text.split("\n"):
            line = line.strip()
            if not line or len(line) < 10:
                continue
            cleaned = line.lstrip("0123456789.-*•() ").strip()

            if "?" in cleaned:
                question_parts = cleaned.split("?")
                if question_parts:
                    question = question_parts[0].strip() + "?"
                    ql = question.lower()
                    is_valid = (
                        len(question) > 15
                        and question not in seen_questions
                        and (ql.startswith(question_starters) or "?" in question)
                    )
                    if is_valid:
                        questions.append(question)
                        seen_questions.add(question)
            elif cleaned.lower().startswith(
                (
                    "what",
                    "how",
                    "why",
                    "when",
                    "where",
                    "who",
                    "can you",
                    "tell me",
                    "describe",
                    "explain",
                    "did you",
                    "have you",
                    "would you",
                )
            ):
                if not cleaned.endswith("?"):
                    cleaned += "?"
                if len(cleaned) > 15 and cleaned not in seen_questions:
                    questions.append(cleaned)
                    seen_questions.add(cleaned)

        if len(questions) < num_questions:
            for part in questions_text.split("?")[:-1]:
                question = part.strip().lstrip("0123456789.-*•() ").strip()
                if question and len(question) > 15 and question + "?" not in seen_questions:
                    full_question = question + "?"
                    questions.append(full_question)
                    seen_questions.add(full_question)

        unique_questions = []
        for q in questions:
            if q not in unique_questions:
                unique_questions.append(q)

        if self.debug:
            print(f"[DEBUG] Extracted {len(unique_questions)} unique questions\n")

        return unique_questions[:num_questions] if unique_questions else []

    def ask_question(self, question: str) -> str:
        """Ask a question to the user and return their response."""
        print(f"\n🤖 Agent: {question}")
        response = input("👤 You: ").strip()

        self.questions_asked.append(question)
        self.responses_received.append(response)
        self.conversation_history.append({"role": "assistant", "content": question})
        self.conversation_history.append({"role": "user", "content": response})
        return response

    def generate_followup(self, user_response: str) -> Optional[str]:
        """Generate a follow-up question based on the user's response."""
        if not self.resume_text:
            return None

        conversation_context = "\n".join(
            f"{msg['role']}: {msg['content']}"
            for msg in self.conversation_history[-4:]
        )
        resume_snippet = self.resume_text[:RESUME_MAX_CHARS_FOLLOWUP]

        prompt = f"""Based on the resume and the conversation so far, generate ONE insightful follow-up question that digs deeper into what the candidate just said.

Resume Summary:
{resume_snippet}

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

        full_prompt = "You are a professional recruiter having a natural conversation.\n\n" + prompt
        retry_delay = INITIAL_RETRY_DELAY_SECONDS

        for attempt in range(MAX_RETRIES):
            try:
                response = self.model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.8,
                        max_output_tokens=MAX_OUTPUT_TOKENS_FOLLOWUP,
                    ),
                )
                break
            except Exception as e:
                error_str = str(e).lower()
                if "429" in str(e) or "quota" in error_str or "rate limit" in error_str:
                    if attempt < MAX_RETRIES - 1:
                        delay_match = re.search(r"retry in ([\d.]+)s", error_str)
                        if delay_match:
                            retry_delay = int(float(delay_match.group(1))) + 2
                        else:
                            retry_delay = retry_delay * (attempt + 1)
                        time.sleep(retry_delay)
                        continue
                    if self.debug:
                        print("⚠️  Rate limit exceeded for follow-up question. Skipping...")
                    return None
                raise

        followup = response.text.strip().strip('"').strip("'").strip()
        if "?" in followup:
            followup = followup.split("?")[0].strip() + "?"

        question_starters = (
            "what",
            "how",
            "why",
            "when",
            "where",
            "who",
            "can",
            "could",
            "would",
            "did",
            "do",
            "does",
            "have",
            "has",
            "tell me",
            "describe",
            "explain",
        )
        statement_starters = ("that", "this", "it", "you", "i", "we", "they")

        if followup and len(followup) > 15:
            is_question = followup.lower().startswith(question_starters) or "?" in followup
            if is_question:
                if not followup.endswith("?"):
                    followup += "?"
                if not followup.lower().startswith(statement_starters):
                    return followup
        return None

    def _print_interview_summary(self) -> None:
        """Print a summary of the interview session."""
        print("\n" + "=" * 60)
        print("📊 Interview Summary")
        print("=" * 60)

        total_questions = len(self.questions_asked)
        total_responses = len(
            [r for r in self.responses_received if r.lower() not in ("skip", "quit")]
        )
        skipped = len([r for r in self.responses_received if r.lower() == "skip"])

        print(f"\n✅ Total Questions Asked: {total_questions}")
        print(f"✅ Total Responses Received: {total_responses}")
        if skipped > 0:
            print(f"⏭️  Questions Skipped: {skipped}")

        if total_questions > 0:
            print("\n📝 Questions Discussed:")
            for i, (q, r) in enumerate(zip(self.questions_asked, self.responses_received), 1):
                if r.lower() not in ("skip", "quit"):
                    print(f"\n  {i}. {q}")
                    response_preview = r[:100] + "..." if len(r) > 100 else r
                    print(f"     💬 Response: {response_preview}")

        print("\n" + "=" * 60)
        print("✅ Interview completed successfully!")
        print("=" * 60)

    def conduct_interview(
        self,
        pdf_path: str,
        num_questions: int = 5,
        allow_followups: bool = True,
    ) -> None:
        """
        Run a full interview session: load resume, generate questions, ask user, show summary.

        Args:
            pdf_path: Path to the PDF resume.
            num_questions: Number of initial questions to ask.
            allow_followups: Whether to generate follow-up questions.
        """
        print("=" * 60)
        print("📄 Resume Interview Agent")
        print("=" * 60)

        print(f"\n📖 Reading resume from: {pdf_path}")
        try:
            resume_text = self.read_pdf(pdf_path)
            print(f"✅ Successfully loaded resume ({len(resume_text)} characters)")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return

        print(f"\n🤔 Generating {num_questions} questions...")
        try:
            questions = self.generate_questions(num_questions)
            if len(questions) < num_questions and len(questions) > 0:
                print(
                    f"⚠️  Warning: Only generated {len(questions)} questions instead of {num_questions}"
                )
                remaining = num_questions - len(questions)
                print(f"🔄 Attempting to generate {remaining} more questions...")
                additional = self.generate_questions(remaining + 2)
                for q in additional:
                    if q not in questions and len(questions) < num_questions:
                        questions.append(q)
            print(f"✅ Generated {len(questions)} questions\n")
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                print(
                    "❌ API Quota/Rate Limit Error.\n\n"
                    "💡 Solutions:\n"
                    "  1. Wait a few minutes and try again (free tier: 20 requests/day)\n"
                    "  2. Upgrade at: https://ai.google.dev/pricing\n"
                    "  3. Check usage: https://ai.dev/rate-limit\n"
                    "  4. Try a different model in config (e.g. gemini-2.5-pro)"
                )
            else:
                print(f"❌ Error generating questions: {str(e)}")
            return

        print("=" * 60)
        print("💬 Interview Session")
        print("=" * 60)
        print("\n(You can type 'skip' to skip a question, 'quit' to end the interview)\n")

        seen = set()
        unique_questions = []
        for q in questions:
            if q not in seen:
                seen.add(q)
                unique_questions.append(q)

        for i, question in enumerate(unique_questions, 1):
            print(f"\n[Question {i}/{len(unique_questions)}]")
            response = self.ask_question(question)

            if response.lower() == "quit":
                print("\n👋 Ending interview. Thank you!")
                break
            if response.lower() == "skip":
                print("⏭️  Skipping this question...")
                continue

            if allow_followups:
                followup = self.generate_followup(response)
                if followup:
                    followup_response = self.ask_question(followup)
                    if followup_response.lower() == "quit":
                        print("\n👋 Ending interview. Thank you!")
                        break

        self._print_interview_summary()
