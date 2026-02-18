def ask_user(question: str) -> str:
    """Print the question, read user input, and return the response."""
    print(f"\n🤖 Agent: {question}")
    return input("👤 You: ").strip()

def print_summary(questions_asked: list[str], responses_received: list[str]) -> None:
    """Print the interview summary to stdout."""
    print("\n" + "=" * 60)
    print("📊 Interview Summary")
    print("=" * 60)

    total = len(questions_asked)
    responded = len(
        [r for r in responses_received if r.lower() not in ("skip", "quit")]
    )
    skipped = len([r for r in responses_received if r.lower() == "skip"])

    print(f"\n✅ Total Questions Asked: {total}")
    print(f"✅ Total Responses Received: {responded}")
    if skipped > 0:
        print(f"⏭️  Questions Skipped: {skipped}")

    if total > 0:
        print("\n📝 Questions Discussed:")
        for i, (q, r) in enumerate(zip(questions_asked, responses_received), 1):
            if r.lower() not in ("skip", "quit"):
                print(f"\n  {i}. {q}")
                preview = r[:100] + "..." if len(r) > 100 else r
                print(f"     💬 Response: {preview}")

    print("\n" + "=" * 60)
    print("✅ Interview completed successfully!")
    print("=" * 60)
