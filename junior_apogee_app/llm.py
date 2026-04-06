from __future__ import annotations


def call_llm(prompt: str, model: str = "claude-2") -> str:
    """Return a mocked LLM response for the given prompt."""
    return f"[mocked {model} answer] {prompt}"
