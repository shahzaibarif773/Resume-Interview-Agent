import os
import sys
import time
import re
from typing import Optional, List, Dict
import pdfplumber
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ResumeAgent:
    """
    AI agent that reads PDF resumes and asks intelligent questions about them.
    """
    
    def __init__(self, api_key: Optional[str] = None, debug: bool = False):
        """
        Initialize the Resume Agent.
        
        Args:
            api_key: Google API key. If not provided, will try to get from environment.
            debug: Enable debug output (default: False)
        """
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "Google API key is required. "
                "Set it as GOOGLE_API_KEY environment variable or pass it to the constructor."
            )
        
        genai.configure(api_key=api_key)
        # Use gemini-2.5-flash (stable, fast and cost-effective) or gemini-2.5-pro for better quality
        # You can change this to 'gemini-2.5-pro' if you need better quality
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.resume_text: Optional[str] = None
        self.conversation_history: List[Dict[str, str]] = []
        self.debug = debug
        self.questions_asked: List[str] = []
        self.responses_received: List[str] = []
        
    def read_pdf(self, pdf_path: str) -> str:
        """
        Extract text from a PDF resume.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text from the PDF
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
            raise Exception(f"Error reading PDF: {str(e)}")
        
        self.resume_text = "\n\n".join(text_content)
        return self.resume_text
    
    def generate_questions(self, num_questions: int = 5) -> List[str]:
        """
        Generate intelligent questions about the resume using AI.
        
        Args:
            num_questions: Number of questions to generate
            
        Returns:
            List of questions
        """
        if not self.resume_text:
            raise ValueError("No resume loaded. Please read a PDF first.")
        
        prompt = f"""You are a professional recruiter reviewing a resume. Based on the following resume content, generate exactly {num_questions} complete, thoughtful questions.

Resume Content:
{self.resume_text[:4000]}

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

        try:
            full_prompt = f"""You are a professional recruiter who asks insightful questions about resumes.

{prompt}"""
            
            # Retry logic for rate limits and quota errors
            max_retries = 3
            retry_delay = 5  # Start with 5 seconds
            
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(
                        full_prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.7,
                            max_output_tokens=1000  # Increased to ensure complete responses
                        )
                    )
                    break  # Success, exit retry loop
                except Exception as e:
                    error_str = str(e).lower()
                    # Check if it's a quota/rate limit error
                    if '429' in str(e) or 'quota' in error_str or 'rate limit' in error_str:
                        if attempt < max_retries - 1:
                            # Extract retry delay from error if available
                            if 'retry_delay' in error_str or 'retry in' in error_str:
                                # Try to extract seconds from error message
                                delay_match = re.search(r'retry in ([\d.]+)s', error_str)
                                if delay_match:
                                    retry_delay = int(float(delay_match.group(1))) + 2
                                else:
                                    retry_delay = retry_delay * (attempt + 1)  # Exponential backoff
                            
                            print(f"\n⚠️  Rate limit/quota exceeded. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                            time.sleep(retry_delay)
                            continue
                        else:
                            raise Exception(
                                f"Quota/Rate limit exceeded after {max_retries} attempts. "
                                f"Free tier allows 20 requests per day per model. "
                                f"Please wait or upgrade your plan at https://ai.google.dev/gemini-api/docs/rate-limits"
                            )
                    else:
                        # Not a quota error, re-raise immediately
                        raise
            
            questions_text = response.text.strip()
            
            if self.debug:
                print(f"\n[DEBUG] Full AI response:\n{questions_text}\n")
                print(f"[DEBUG] Response length: {len(questions_text)} characters\n")
            
            # Clean up the response - remove any trailing numbers or incomplete lines
            lines = questions_text.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # Remove numbering, bullets, and common prefixes
                cleaned = line.lstrip('0123456789.-*•() ').strip()
                # Skip lines that are just numbers or very short
                if len(cleaned) < 10 or cleaned.isdigit():
                    continue
                cleaned_lines.append(cleaned)
            
            questions_text = '\n'.join(cleaned_lines)
            
            # Split by newlines and extract questions
            questions = []
            seen_questions = set()  # Avoid duplicates
            
            for line in questions_text.split('\n'):
                line = line.strip()
                if not line or len(line) < 10:
                    continue
                
                # Remove any remaining prefixes
                cleaned = line.lstrip('0123456789.-*•() ').strip()
                
                # Check if it's a complete question
                if '?' in cleaned:
                    # Remove any trailing incomplete text after the question mark
                    question_parts = cleaned.split('?')
                    if question_parts:
                        question = question_parts[0].strip() + '?'
                        # Validate it's a proper question (not a statement)
                        question_lower = question.lower()
                        is_valid_question = (
                            len(question) > 15 and 
                            question not in seen_questions and
                            (question_lower.startswith(('what', 'how', 'why', 'when', 'where', 'who', 'can', 'could', 'would', 'did', 'do', 'does', 'have', 'has', 'tell', 'describe', 'explain')) or
                             '?' in question)
                        )
                        if is_valid_question:
                            questions.append(question)
                            seen_questions.add(question)
                # Check if it starts with question words (might be missing ?)
                elif cleaned.lower().startswith(('what', 'how', 'why', 'when', 'where', 'who', 'can you', 'tell me', 'describe', 'explain', 'did you', 'have you', 'would you')):
                    if not cleaned.endswith('?'):
                        cleaned += '?'
                    if len(cleaned) > 15 and cleaned not in seen_questions:
                        questions.append(cleaned)
                        seen_questions.add(cleaned)
            
            # If we still don't have enough questions, try splitting by question marks
            if len(questions) < num_questions:
                parts = questions_text.split('?')
                for part in parts[:-1]:  # Last part might not be a question
                    question = part.strip().lstrip('0123456789.-*•() ').strip()
                    if question and len(question) > 15 and question + '?' not in seen_questions:
                        full_question = question + '?'
                        questions.append(full_question)
                        seen_questions.add(full_question)
            
            # Remove duplicates while preserving order
            unique_questions = []
            for q in questions:
                if q not in unique_questions:
                    unique_questions.append(q)
            
            if self.debug:
                print(f"[DEBUG] Extracted {len(unique_questions)} unique questions\n")
            
            return unique_questions[:num_questions] if unique_questions else []
            
        except Exception as e:
            error_str = str(e)
            if '429' in error_str or 'quota' in error_str.lower():
                raise Exception(
                    f"❌ API Quota/Rate Limit Error: {error_str}\n\n"
                    f"💡 Solutions:\n"
                    f"  1. Wait a few minutes and try again (free tier: 20 requests/day)\n"
                    f"  2. Upgrade your Google AI plan at: https://ai.google.dev/pricing\n"
                    f"  3. Check your quota usage at: https://ai.dev/rate-limit\n"
                    f"  4. Try using a different model (change gemini-2.5-flash in code)"
                )
            raise Exception(f"Error generating questions: {str(e)}")
    
    def ask_question(self, question: str) -> str:
        """
        Ask a question to the user and get their response.
        
        Args:
            question: The question to ask
            
        Returns:
            User's response
        """
        print(f"\n🤖 Agent: {question}")
        response = input("👤 You: ").strip()
        
        # Store in conversation history and track
        self.questions_asked.append(question)
        self.responses_received.append(response)
        
        self.conversation_history.append({
            "role": "assistant",
            "content": question
        })
        self.conversation_history.append({
            "role": "user",
            "content": response
        })
        
        return response
    
    def generate_followup(self, user_response: str) -> Optional[str]:
        """
        Generate a follow-up question based on the user's response.
        
        Args:
            user_response: The user's response to the previous question
            
        Returns:
            A follow-up question or None
        """
        if not self.resume_text:
            return None
        
        # Build context from conversation
        conversation_context = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in self.conversation_history[-4:]  # Last 2 exchanges
        ])
        
        prompt = f"""Based on the resume and the conversation so far, generate ONE insightful follow-up question that digs deeper into what the candidate just said.

Resume Summary:
{self.resume_text[:2000]}

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

        try:
            full_prompt = f"""You are a professional recruiter having a natural conversation.

{prompt}"""
            
            # Retry logic for rate limits and quota errors
            max_retries = 3
            retry_delay = 5
            
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(
                        full_prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.8,
                            max_output_tokens=200  # Increased for complete questions
                        )
                    )
                    break  # Success, exit retry loop
                except Exception as e:
                    error_str = str(e).lower()
                    if '429' in str(e) or 'quota' in error_str or 'rate limit' in error_str:
                        if attempt < max_retries - 1:
                            delay_match = re.search(r'retry in ([\d.]+)s', error_str)
                            if delay_match:
                                retry_delay = int(float(delay_match.group(1))) + 2
                            else:
                                retry_delay = retry_delay * (attempt + 1)
                            time.sleep(retry_delay)
                            continue
                        else:
                            # Don't raise for follow-ups, just return None
                            if self.debug:
                                print(f"⚠️  Rate limit exceeded for follow-up question. Skipping...")
                            return None
                    else:
                        raise
            
            followup = response.text.strip()
            # Clean up if it has quotes or extra formatting
            followup = followup.strip('"').strip("'").strip()
            
            # Remove any trailing incomplete text
            if '?' in followup:
                followup = followup.split('?')[0].strip() + '?'
            
            # Validate it's actually a question (not a statement)
            # Check if it starts with question words or contains question structure
            question_starters = ('what', 'how', 'why', 'when', 'where', 'who', 'can', 'could', 'would', 'did', 'do', 'does', 'have', 'has', 'tell me', 'describe', 'explain')
            is_question = followup.lower().startswith(question_starters) or '?' in followup
            
            # Ensure it's a complete question and not just a statement
            if followup and len(followup) > 15 and is_question:
                if not followup.endswith('?'):
                    followup += '?'
                # Double-check it's not a statement disguised as a question
                if not followup.lower().startswith(('that', 'this', 'it', 'you', 'i', 'we', 'they')):
                    return followup
            return None
            
        except Exception as e:
            print(f"Error generating follow-up: {str(e)}")
            return None
    
    def _print_interview_summary(self):
        """Print a summary of the interview session."""
        print("\n" + "=" * 60)
        print("📊 Interview Summary")
        print("=" * 60)
        
        total_questions = len(self.questions_asked)
        total_responses = len([r for r in self.responses_received if r.lower() not in ['skip', 'quit']])
        skipped = len([r for r in self.responses_received if r.lower() == 'skip'])
        
        print(f"\n✅ Total Questions Asked: {total_questions}")
        print(f"✅ Total Responses Received: {total_responses}")
        if skipped > 0:
            print(f"⏭️  Questions Skipped: {skipped}")
        
        if total_questions > 0:
            print(f"\n📝 Questions Discussed:")
            for i, (q, r) in enumerate(zip(self.questions_asked, self.responses_received), 1):
                if r.lower() not in ['skip', 'quit']:
                    print(f"\n  {i}. {q}")
                    # Truncate long responses for summary
                    response_preview = r[:100] + "..." if len(r) > 100 else r
                    print(f"     💬 Response: {response_preview}")
        
        print("\n" + "=" * 60)
        print("✅ Interview completed successfully!")
        print("=" * 60)
    
    def conduct_interview(self, pdf_path: str, num_questions: int = 5, allow_followups: bool = True):
        """
        Main method to conduct an interview session.
        
        Args:
            pdf_path: Path to the PDF resume
            num_questions: Number of initial questions to ask
            allow_followups: Whether to generate follow-up questions
        """
        print("=" * 60)
        print("📄 Resume Interview Agent")
        print("=" * 60)
        
        # Read the resume
        print(f"\n📖 Reading resume from: {pdf_path}")
        try:
            resume_text = self.read_pdf(pdf_path)
            print(f"✅ Successfully loaded resume ({len(resume_text)} characters)")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return
        
        # Generate initial questions
        print(f"\n🤔 Generating {num_questions} questions...")
        try:
            questions = self.generate_questions(num_questions)
            if len(questions) < num_questions:
                print(f"⚠️  Warning: Only generated {len(questions)} questions instead of {num_questions}")
                # Try to generate more questions if we got fewer than requested
                if len(questions) > 0:
                    remaining = num_questions - len(questions)
                    print(f"🔄 Attempting to generate {remaining} more questions...")
                    additional_questions = self.generate_questions(remaining + 2)  # Generate a few extra
                    # Filter out duplicates
                    for q in additional_questions:
                        if q not in questions and len(questions) < num_questions:
                            questions.append(q)
            print(f"✅ Generated {len(questions)} questions\n")
        except Exception as e:
            print(f"❌ Error generating questions: {str(e)}")
            return
        
        # Ask questions
        print("=" * 60)
        print("💬 Interview Session")
        print("=" * 60)
        print("\n(You can type 'skip' to skip a question, 'quit' to end the interview)\n")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_questions = []
        for q in questions:
            if q not in seen:
                seen.add(q)
                unique_questions.append(q)
        questions = unique_questions
        
        for i, question in enumerate(questions, 1):
            print(f"\n[Question {i}/{len(questions)}]")
            response = self.ask_question(question)
            
            if response.lower() == 'quit':
                print("\n👋 Ending interview. Thank you!")
                break
            elif response.lower() == 'skip':
                print("⏭️  Skipping this question...")
                continue
            
            # Generate follow-up if enabled
            if allow_followups and response.lower() not in ['skip', 'quit']:
                followup = self.generate_followup(response)
                if followup:
                    followup_response = self.ask_question(followup)
                    if followup_response.lower() == 'quit':
                        print("\n👋 Ending interview. Thank you!")
                        break
        
        # Generate success summary
        self._print_interview_summary()


def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="AI Resume Interview Agent - Reads PDF resumes and asks questions"
    )
    parser.add_argument(
        "pdf_path",
        type=str,
        help="Path to the PDF resume file"
    )
    parser.add_argument(
        "--questions",
        type=int,
        default=5,
        help="Number of questions to ask (default: 5)"
    )
    parser.add_argument(
        "--no-followups",
        action="store_true",
        help="Disable follow-up questions"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Google API key (or set GOOGLE_API_KEY env variable)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output"
    )
    
    args = parser.parse_args()
    
    try:
        agent = ResumeAgent(api_key=args.api_key, debug=args.debug)
        agent.conduct_interview(
            pdf_path=args.pdf_path,
            num_questions=args.questions,
            allow_followups=not args.no_followups
        )
    except KeyboardInterrupt:
        print("\n\n👋 Interview interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
