"""Legacy module - imports from new modular structure for backward compatibility."""
from app.services.summarization import (
    format_research_summary,
    summarize_search_results,
    summarize_ambiguity_groups,
    summarize_extracted_documents,
)

__all__ = [
    "summarize_search_results",
    "summarize_ambiguity_groups",
    "summarize_extracted_documents",
    "format_research_summary",
]
