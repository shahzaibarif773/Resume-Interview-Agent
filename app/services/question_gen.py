"""
Parse and validate questions from raw LLM output.
"""

from typing import List, Optional

# Words that indicate a proper question (not a statement)
QUESTION_STARTERS = (
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
    "can you",
    "tell me",
    "did you",
    "have you",
    "would you",
)

STATEMENT_STARTERS = ("that", "this", "it", "you", "i", "we", "they")


def _clean_line(line: str) -> str:
    """Remove numbering, bullets, and extra whitespace."""
    return line.lstrip("0123456789.-*•() ").strip()


def parse_questions(raw_text: str, num_questions: int) -> List[str]:
    """
    Extract a list of valid questions from raw LLM output.

    Args:
        raw_text: Raw response from the model.
        num_questions: Maximum number of questions to return.

    Returns:
        List of cleaned, deduplicated questions (each ending with '?').
    """
    lines = raw_text.split("\n")
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        cleaned = _clean_line(line)
        if len(cleaned) < 10 or cleaned.isdigit():
            continue
        cleaned_lines.append(cleaned)

    text = "\n".join(cleaned_lines)
    questions = []
    seen = set()

    for line in text.split("\n"):
        line = line.strip()
        if not line or len(line) < 10:
            continue
        cleaned = _clean_line(line)

        if "?" in cleaned:
            question = cleaned.split("?")[0].strip() + "?"
            ql = question.lower()
            if (
                len(question) > 15
                and question not in seen
                and (ql.startswith(QUESTION_STARTERS) or "?" in question)
            ):
                questions.append(question)
                seen.add(question)
        elif cleaned.lower().startswith(QUESTION_STARTERS):
            if not cleaned.endswith("?"):
                cleaned += "?"
            if len(cleaned) > 15 and cleaned not in seen:
                questions.append(cleaned)
                seen.add(cleaned)

    # Fallback: split by '?' and reconstruct
    if len(questions) < num_questions:
        for part in text.split("?")[:-1]:
            question = _clean_line(part)
            if question and len(question) > 15 and question + "?" not in seen:
                full = question + "?"
                questions.append(full)
                seen.add(full)

    # Deduplicate while preserving order
    unique = []
    for q in questions:
        if q not in unique:
            unique.append(q)

    return unique[:num_questions] if unique else []


def validate_followup(raw_text: str) -> Optional[str]:
    """
    Validate and clean a single follow-up question from the LLM.

    Returns:
        A valid question string (ending with '?'), or None if not a valid question.
    """
    text = raw_text.strip().strip('"').strip("'").strip()
    if "?" in text:
        text = text.split("?")[0].strip() + "?"

    if not text or len(text) <= 15:
        return None

    if not text.endswith("?"):
        text += "?"

    lower = text.lower()
    if not (lower.startswith(QUESTION_STARTERS) or "?" in text):
        return None
    if lower.startswith(STATEMENT_STARTERS):
        return None

    return text
