"""Bibliothèque de gabarits de prompts versionnés (Markdown + front-matter YAML)."""

from .load import Prompt, list_prompts, load_prompt

__all__ = ["Prompt", "list_prompts", "load_prompt"]
