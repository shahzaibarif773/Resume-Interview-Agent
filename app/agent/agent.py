"""
Resume Interview Agent: orchestrates PDF reading, question generation, and interview flow.
"""

import os
from typing import List, Optional

from app.config import (
    ENV_GOOGLE_API_KEY,
    MAX_OUTPUT_TOKENS_FOLLOWUP,
    MAX_OUTPUT_TOKENS_QUESTIONS,
)
from app.agent.memory import InterviewMemory
from app.services.llm_service import GeminiClient
from app.services.resume_parser import extract_text_from_pdf
from app.agent.prompts import build_followup_prompt, build_questions_prompt
from app.services.question_gen import parse_questions, validate_followup
from app.utils.helpers import ask_user, print_summary


class ResumeAgent:
    """
    AI agent that reads PDF resumes and runs interactive interviews.
    Delegates to: pdf_reader, prompts, llm, question_parser, interview session.
    """

    def __init__(self, api_key: Optional[str] = None, debug: bool = False) -> None:
        api_key = api_key or os.getenv(ENV_GOOGLE_API_KEY)
        if not api_key:
            raise ValueError(
                "Google API key is required. "
                f"Set it as {ENV_GOOGLE_API_KEY} or pass it to the constructor."
            )

        self._llm = GeminiClient(api_key)
        self.debug = debug
        self.resume_text: Optional[str] = None

    def read_pdf(self, pdf_path: str) -> str:
        """Load resume text from a PDF file and store it on the agent."""
        self.resume_text = extract_text_from_pdf(pdf_path)
        return self.resume_text

    def generate_questions(self, num_questions: int = 5) -> List[str]:
        """Generate interview questions from the loaded resume using the LLM."""
        if not self.resume_text:
            raise ValueError("No resume loaded. Please read a PDF first.")

        prompt = build_questions_prompt(self.resume_text, num_questions)
        raw = self._llm.generate(
            prompt,
            max_output_tokens=MAX_OUTPUT_TOKENS_QUESTIONS,
            temperature=0.7,
        )

        if self.debug:
            print(f"\n[DEBUG] Full AI response:\n{raw[:500]}...\n" if len(raw) > 500 else f"\n[DEBUG] Full AI response:\n{raw}\n")
            print(f"[DEBUG] Response length: {len(raw)} characters\n")

        questions = parse_questions(raw, num_questions)

        if self.debug:
            print(f"[DEBUG] Extracted {len(questions)} unique questions\n")

        return questions

    def generate_followup(self, conversation_context: str) -> Optional[str]:
        """Generate one follow-up question from the resume and recent conversation."""
        if not self.resume_text:
            return None

        prompt = build_followup_prompt(self.resume_text, conversation_context)
        raw = self._llm.generate_graceful(
            prompt,
            max_output_tokens=MAX_OUTPUT_TOKENS_FOLLOWUP,
            temperature=0.8,
        )

        if raw is None:
            if self.debug:
                print("⚠️  Rate limit exceeded for follow-up question. Skipping...")
            return None

        return validate_followup(raw)

    def conduct_interview(
        self,
        pdf_path: str,
        num_questions: int = 5,
        allow_followups: bool = True,
    ) -> None:
        """Run full interview: load PDF, generate questions, ask user, print summary."""
        print("=" * 60)
        print("📄 Resume Interview Agent")
        print("=" * 60)

        print(f"\n📖 Reading resume from: {pdf_path}")
        try:
            self.read_pdf(pdf_path)
            print(f"✅ Successfully loaded resume ({len(self.resume_text)} characters)")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return

        print(f"\n🤔 Generating {num_questions} questions...")
        try:
            questions = self.generate_questions(num_questions)
            if len(questions) < num_questions and len(questions) > 0:
                print(f"⚠️  Warning: Only generated {len(questions)} questions instead of {num_questions}")
                remaining = num_questions - len(questions)
                print(f"🔄 Attempting to generate {remaining} more questions...")
                extra = self.generate_questions(remaining + 2)
                for q in extra:
                    if q not in questions and len(questions) < num_questions:
                        questions.append(q)
            print(f"✅ Generated {len(questions)} questions\n")
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower():
                print(
                    "❌ API Quota/Rate Limit Error.\n\n"
                    "💡 Solutions:\n"
                    "  1. Wait a few minutes (free tier: 20 requests/day)\n"
                    "  2. Upgrade: https://ai.google.dev/pricing\n"
                    "  3. Usage: https://ai.dev/rate-limit\n"
                    "  4. Try a different model in config"
                )
            else:
                print(f"❌ Error generating questions: {err}")
            return

        print("=" * 60)
        print("💬 Interview Session")
        print("=" * 60)
        print("\n(You can type 'skip' to skip a question, 'quit' to end the interview)\n")

        memory = InterviewMemory()
        seen = set()
        unique_questions = []
        for q in questions:
            if q not in seen:
                seen.add(q)
                unique_questions.append(q)

        for i, question in enumerate(unique_questions, 1):
            print(f"\n[Question {i}/{len(unique_questions)}]")
            response = ask_user(question)
            memory.record_turn(question, response)

            if response.lower() == "quit":
                print("\n👋 Ending interview. Thank you!")
                print_summary(memory.questions_asked, memory.responses_received)
                return
            if response.lower() == "skip":
                print("⏭️  Skipping this question...")
                continue

            if allow_followups:
                context = memory.get_recent_context()
                followup = self.generate_followup(context)
                if followup:
                    followup_response = ask_user(followup)
                    memory.record_turn(followup, followup_response)

                    if followup_response.lower() == "quit":
                        print("\n👋 Ending interview. Thank you!")
                        break

        print_summary(memory.questions_asked, memory.responses_received)
