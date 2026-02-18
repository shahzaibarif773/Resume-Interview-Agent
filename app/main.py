"""
Command-line interface for Resume Reader AI.
"""

import sys

from dotenv import load_dotenv

from app.agent.agent import ResumeAgent

# Load .env so GOOGLE_API_KEY is available
load_dotenv()


def main() -> None:
    """Main entry point for the CLI."""
    import argparse

    parser = argparse.ArgumentParser(
        description="AI Resume Interview Agent - Reads PDF resumes and asks questions",
        prog="resume-reader",
    )
    parser.add_argument(
        "pdf_path",
        type=str,
        help="Path to the PDF resume file",
    )
    parser.add_argument(
        "--questions",
        type=int,
        default=5,
        help="Number of questions to ask (default: 5)",
    )
    parser.add_argument(
        "--no-followups",
        action="store_true",
        help="Disable follow-up questions",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Google API key (or set GOOGLE_API_KEY env variable)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output",
    )

    args = parser.parse_args()

    try:
        agent = ResumeAgent(api_key=args.api_key, debug=args.debug)
        agent.conduct_interview(
            pdf_path=args.pdf_path,
            num_questions=args.questions,
            allow_followups=not args.no_followups,
        )
    except KeyboardInterrupt:
        print("\n\n👋 Interview interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
