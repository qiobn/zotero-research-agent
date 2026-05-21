"""LLM abstraction — wraps LiteLLM for unified model access."""

from research_core.llm.client import llm_completion, llm_completion_stream

__all__ = ["llm_completion", "llm_completion_stream"]
