from typing import Dict, List

class InterviewMemory:
    """Tracks questions, responses, and conversation history."""

    def __init__(self) -> None:
        self.questions_asked: List[str] = []
        self.responses_received: List[str] = []
        self.conversation_history: List[Dict[str, str]] = []

    def record_turn(self, question: str, response: str) -> None:
        """Record a question and response pair."""
        self.questions_asked.append(question)
        self.responses_received.append(response)
        self.conversation_history.append({"role": "assistant", "content": question})
        self.conversation_history.append({"role": "user", "content": response})

    def get_recent_context(self, last_n: int = 4) -> str:
        """Format the last N messages for use in follow-up prompts."""
        messages = self.conversation_history[-last_n:]
        return "\n".join(f"{m['role']}: {m['content']}" for m in messages)
