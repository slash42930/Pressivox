from app.services.summarization.snippet_processing import clean_summary_snippet


def test_clean_summary_snippet_removes_heading_artifacts() -> None:
    text = "### Mercury\nMercury is the smallest planet in the solar system."

    cleaned = clean_summary_snippet(text, max_chars=200, title="Mercury", is_snippet=True)

    assert "###" not in cleaned
    assert "smallest planet" in cleaned.lower()


def test_clean_summary_snippet_returns_empty_for_disambiguation_like_non_snippet() -> None:
    text = "Mercury may refer to many topics and list pages in disambiguation contexts."

    cleaned = clean_summary_snippet(text, max_chars=200, title="Mercury", is_snippet=False)

    assert cleaned == ""
