from __future__ import annotations

import re
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from readability import Document
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.extracted_document import ExtractedDocument


class ExtractionService:
    BLOCKED_EXTERNAL_LINKS = "external links"
    BLOCKED_FURTHER_READING = "further reading"
    BLOCKED_ARCHIVED = "archived from the original"

    def __init__(self, db: Session) -> None:
        self.settings = get_settings()
        self.db = db
        self._headers = {
            "User-Agent": (
                "WebSearchBackend/0.1 "
                "(learning project; contact: vladzagoni@example.com) "
                "Python-httpx"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _normalize_whitespace(self, text: str) -> str:
        text = text.replace("\xa0", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _clean_inline_noise(self, text: str) -> str:
        text = re.sub(r"\[\s*\d+\s*\]", "", text)
        text = re.sub(r"\[\s*[a-zA-Z]\s*\]", "", text)
        text = re.sub(r"\[\s*page needed\s*\]", "", text)
        text = re.sub(r"\{\{\s*cite[^}]*\}\}", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _is_noise_line(self, line: str) -> bool:
        low = line.lower().strip()

        blocked_exact = {
            "jump to content",
            "read",
            "talk",
            "notes",
            "references",
            self.BLOCKED_EXTERNAL_LINKS,
            "see also",
            self.BLOCKED_FURTHER_READING,
            "bibliography",
            "books",
            "articles",
            "websites",
            "news",
            "other",
        }

        if not low:
            return True

        if low in blocked_exact:
            return True

        if re.fullmatch(r"\[[^\]]+\]", line):
            return True

        if len(line) < 3:
            return True

        if sum(ch.isalnum() for ch in line) < 2:
            return True

        if self.BLOCKED_ARCHIVED in low:
            return True

        if "retrieved " in low and len(line) < 140:
            return True

        if "isbn" in low and len(line) < 180:
            return True

        if "doi :" in low or "doi:" in low:
            return True

        if "pmid" in low or "issn" in low or "oclc" in low:
            return True

        if low.startswith("^ "):
            return True

        if low.startswith("citation ") or low.startswith("cs1 maint"):
            return True

        return False

    def _extract_structured_text(self, readable_html: str) -> str:
        soup = BeautifulSoup(readable_html, "html.parser")

        for bad in soup(["script", "style", "nav", "footer", "aside"]):
            bad.decompose()

        blocks: list[str] = []

        for tag in soup.find_all(["h1", "h2", "h3", "p", "li"]):
            text = tag.get_text(" ", strip=True)
            text = self._clean_inline_noise(text)

            if not text:
                continue

            if tag.name == "li" and len(text) < 35:
                continue

            blocks.append(text)

        return "\n\n".join(blocks)

    def _cut_at_reference_sections(self, text: str) -> str:
        stop_headings = [
            "references",
            self.BLOCKED_EXTERNAL_LINKS,
            "see also",
            self.BLOCKED_FURTHER_READING,
            "bibliography",
            "books",
            "articles",
            "websites",
            "notes",
            "sources",
        ]

        lines = text.splitlines()
        kept: list[str] = []

        for line in lines:
            low = line.strip().lower()

            if low in stop_headings:
                break

            # stop if a references-like section starts in practice
            if low.startswith("references ") or low.startswith("bibliography "):
                break

            kept.append(line)

        return "\n".join(kept).strip()

    def _clean_lines(self, text: str) -> str:
        lines = [line.strip() for line in text.splitlines()]
        cleaned: list[str] = []

        for line in lines:
            line = self._clean_inline_noise(line)

            if self._is_noise_line(line):
                continue

            cleaned.append(line)

        text = "\n".join(cleaned)
        text = self._cut_at_reference_sections(text)
        return self._normalize_whitespace(text)

    def _fallback_extract_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")

        for bad in soup(["script", "style", "nav", "footer", "aside"]):
            bad.decompose()

        body = soup.body or soup
        text = body.get_text("\n", strip=True)
        text = self._clean_lines(text)
        return text

    def _split_paragraphs(self, text: str) -> list[str]:
        parts = re.split(r"\n{2,}", text)
        paragraphs: list[str] = []

        for part in parts:
            value = " ".join(part.split()).strip()
            if not value:
                continue

            low = value.lower()

            if len(value) < 80:
                continue

            if low in {
                "references",
                self.BLOCKED_EXTERNAL_LINKS,
                "bibliography",
                self.BLOCKED_FURTHER_READING,
            }:
                continue

            if " isbn " in f" {low} ":
                continue

            if " doi " in f" {low} " or "doi:" in low or "doi :" in low:
                continue

            if "pmid" in low or "issn" in low or "oclc" in low:
                continue

            if self.BLOCKED_ARCHIVED in low:
                continue

            paragraphs.append(value)

        return paragraphs

    def _truncate_passage(self, paragraph: str, max_chars: int = 420) -> str:
        paragraph = " ".join(paragraph.split()).strip()

        if len(paragraph) <= max_chars:
            return paragraph

        truncated = paragraph[:max_chars]

        sentence_endings = [
            truncated.rfind(". "),
            truncated.rfind("! "),
            truncated.rfind("? "),
        ]
        best_end = max(sentence_endings)

        if best_end >= 140:
            return truncated[: best_end + 1].strip()

        last_space = truncated.rfind(" ")
        if last_space >= 140:
            return truncated[:last_space].strip() + "..."

        return truncated.strip() + "..."

    def _first_sentence(self, paragraph: str) -> str:
        match = re.split(r"(?<=[.!?])\s+", paragraph, maxsplit=1)
        first = match[0].strip()
        if len(first) >= 90:
            return first
        return paragraph

    def _paragraph_score(self, paragraph: str, query: str | None = None, position: int = 0) -> float:
        score = 0.0
        text = paragraph.lower()

        length = len(paragraph)
        if 140 <= length <= 500:
            score += 30
        elif 501 <= length <= 800:
            score += 20
        elif 80 <= length <= 1000:
            score += 8

        if position == 0:
            score += 40
        elif position == 1:
            score += 22
        elif position == 2:
            score += 14
        elif position <= 5:
            score += 6

        strong_good_terms = [
            " is ",
            " are ",
            " refers to ",
            " defined as ",
            " consists of ",
            " belongs to ",
            " evolved ",
            " largest ",
            " known for ",
            " protected ",
        ]
        for term in strong_good_terms:
            if term in text:
                score += 4

        if re.search(r"\b\d{4}\b", paragraph):
            score += 2

        if query:
            query_terms = [t for t in re.findall(r"[a-z0-9]+", query.lower()) if len(t) > 2]
            overlap = sum(1 for term in query_terms if term in text)
            score += overlap * 12

            # exact topic mention bonus
            query_phrase = query.lower().strip()
            if query_phrase and query_phrase in text:
                score += 20

        bad_terms = [
            "click the arrow",
            "includes audio",
            "play the video",
            "bibliography",
            "references",
            self.BLOCKED_FURTHER_READING,
            self.BLOCKED_ARCHIVED,
            "retrieved ",
            "isbn",
            "doi",
            "pmid",
            "issn",
            "oclc",
        ]
        for term in bad_terms:
            if term in text:
                score -= 35

        # penalize very niche/off-topic sections a bit for generic queries
        niche_terms = [
            "whale fall",
            "whale watching",
            "in captivity",
            "in myth",
            "literature and art",
            "bibliography",
        ]
        for term in niche_terms:
            if term in text and position > 0:
                score -= 10

        return score

    def _select_important_passages(self, text: str, query: str | None = None, max_passages: int = 3) -> list[str]:
        paragraphs = self._split_paragraphs(text)

        ranked: list[dict] = []
        for idx, paragraph in enumerate(paragraphs):
            ranked.append(
                {
                    "paragraph": paragraph,
                    "score": self._paragraph_score(paragraph, query=query, position=idx),
                    "index": idx,
                }
            )

        ranked.sort(key=lambda item: item["score"], reverse=True)

        selected: list[dict] = []
        seen_signatures: set[str] = set()

        for item in ranked:
            paragraph = item["paragraph"]
            compact = self._truncate_passage(paragraph)

            # for the very first paragraph, prefer a richer compact version
            if item["index"] == 0:
                compact = self._truncate_passage(paragraph, max_chars=520)

            signature = re.sub(r"[^a-z0-9 ]", "", compact.lower())[:120]
            if signature in seen_signatures:
                continue

            seen_signatures.add(signature)
            selected.append(
                {
                    "paragraph": compact,
                    "index": item["index"],
                }
            )

            if len(selected) >= max_passages:
                break

        selected.sort(key=lambda item: item["index"])

        final_passages = [item["paragraph"] for item in selected]

        # if the first selected passage is too short/generic, try to expand it
        if final_passages:
            first = final_passages[0]
            if len(first) < 140 and paragraphs:
                final_passages[0] = self._truncate_passage(paragraphs[0], max_chars=520)

        return final_passages

    async def _extract_with_tavily(self, url: str, query: str | None = None) -> dict | None:
        if not self.settings.tavily_api_key or self.settings.tavily_api_key == "replace_me":
            return None

        endpoint = f"{self.settings.tavily_base_url}/extract"
        headers = {
            "Authorization": f"Bearer {self.settings.tavily_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "urls": [url],
            "extract_depth": "basic",
            "include_images": False,
            "format": "markdown",
        }

        if query:
            payload["query"] = query
            payload["chunks_per_source"] = 3

        async with httpx.AsyncClient(
            timeout=self.settings.http_timeout_seconds,
            trust_env=False,
        ) as client:
            response = await client.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        results = data.get("results") or []
        if not results:
            return None

        item = results[0]
        raw_text = item.get("raw_content") or item.get("content") or ""
        cleaned_text = self._clean_lines(raw_text)

        if not cleaned_text.strip():
            return None

        final_url = item.get("url") or url
        title = item.get("title") or "Untitled"

        return {
            "url": url,
            "final_url": final_url,
            "title": title,
            "source": urlparse(final_url).hostname,
            "extracted_text": cleaned_text,
            "important_passages": self._select_important_passages(
                cleaned_text,
                query=query or title,
                max_passages=3,
            ),
            "content_length": len(cleaned_text),
        }

    async def _extract_with_readability(self, url: str, query: str | None = None) -> dict:
        async with httpx.AsyncClient(
            timeout=self.settings.http_timeout_seconds,
            follow_redirects=True,
            trust_env=False,
            headers=self._headers,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

        html = response.text
        final_url = str(response.url)

        doc = Document(html)
        title = doc.short_title() or "Untitled"
        readable_html = doc.summary(html_partial=True)

        extracted_text = self._extract_structured_text(readable_html)
        cleaned_text = self._clean_lines(extracted_text)

        if not cleaned_text.strip():
            cleaned_text = self._fallback_extract_text(html)

        return {
            "url": url,
            "final_url": final_url,
            "title": title,
            "source": urlparse(final_url).hostname,
            "extracted_text": cleaned_text,
            "important_passages": self._select_important_passages(
                cleaned_text,
                query=query or title,
                max_passages=3,
            ),
            "content_length": len(cleaned_text),
        }

    async def extract_from_url(
        self,
        url: str,
        query: str | None = None,
        user_id: int | None = None,
    ) -> dict:
        tavily_result = None

        try:
            tavily_result = await self._extract_with_tavily(url, query=query)
        except Exception:
            tavily_result = None

        result = tavily_result or await self._extract_with_readability(url, query=query)
        self._save_document(result, user_id=user_id)
        return result

    def _save_document(self, data: dict, user_id: int | None = None) -> None:
        row = ExtractedDocument(
            user_id=user_id,
            url=data["url"],
            final_url=data.get("final_url"),
            title=data["title"],
            source=data.get("source"),
            extracted_text=data["extracted_text"],
            content_length=data["content_length"],
        )
        self.db.add(row)
        self.db.commit()

    def list_history(self, limit: int = 20, user_id: int | None = None) -> list[ExtractedDocument]:
        query = self.db.query(ExtractedDocument)
        if user_id is not None:
            query = query.filter(ExtractedDocument.user_id == user_id)

        return query.order_by(ExtractedDocument.created_at.desc()).limit(limit).all()