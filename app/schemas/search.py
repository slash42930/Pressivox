from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    topic: Literal["general", "news", "finance"] = "general"
    language: Literal["english", "romanian"] = "english"
    max_results: int = Field(default=8, ge=1, le=20)

    summarize: bool = False
    extract_top_results: bool = False

    include_domains: list[str] = Field(default_factory=list)
    exclude_domains: list[str] = Field(default_factory=list)

    search_depth: Literal["ultra-fast", "fast", "basic", "advanced"] = "advanced"
    include_answer: bool = True
    include_raw_content: bool = True
    include_images: bool = False
    include_image_descriptions: bool = False
    include_favicon: bool = False
    exact_match: bool = False

    time_range: Literal["day", "week", "month", "year", "d", "w", "m", "y"] | None = None
    start_date: date | None = None
    end_date: date | None = None

    auto_parameters: bool = True


class QueryAnalysisResponse(BaseModel):
    query: str
    topic: str
    token_count: int
    is_short_query: bool
    ambiguous_likely: bool
    recommended_topic: str
    suggested_queries: list[str] = Field(default_factory=list)


class SearchResultItem(BaseModel):
    title: str
    url: HttpUrl
    snippet: str | None = None
    score: float | None = None
    source: str | None = None
    published_date: str | None = None
    favicon: HttpUrl | None = None
    raw_content: str | None = None
    rerank_score: float | None = None


class ResearchSelectedSourceItem(BaseModel):
    meaning: str | None = None
    title: str
    url: HttpUrl
    source: str | None = None
    rerank_score: float | None = None
    favicon: HttpUrl | None = None


class ResearchResultItem(BaseModel):
    title: str
    url: HttpUrl
    snippet: str | None = None
    source: str | None = None
    score: float | None = None
    rerank_score: float | None = None
    published_date: str | None = None
    favicon: HttpUrl | None = None


class ResearchSourceItem(BaseModel):
    title: str
    url: HttpUrl
    source: str | None = None
    snippet: str | None = None
    score: float | None = None
    published_date: str | None = None
    quality_score: int | None = None
    relevance_score: float | None = None


class ResearchSections(BaseModel):
    concise_summary: str
    key_findings: list[str] = Field(default_factory=list)
    detailed_analysis: str = ""
    sources: list[ResearchSourceItem] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    suggested_follow_up_queries: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] | None = None
    omitted_sources: list[str] = Field(default_factory=list)


class SearchResponse(BaseModel):
    query: str
    topic: str
    provider: str

    results: list[SearchResultItem]

    summary: str | None = None
    extracted_summary: str | None = None
    extraction_attempted: bool = False
    extracted_count: int = 0

    answer: str | None = None
    response_time: float | None = None
    request_id: str | None = None
    auto_parameters: dict[str, Any] | None = None
    usage: dict[str, Any] | None = None
    selected_sources: list[ResearchSelectedSourceItem] = Field(default_factory=list)
    ambiguous: bool = False
    meaning_groups: list[dict[str, Any]] = Field(default_factory=list)


class ResearchResponse(BaseModel):
    query: str
    topic: str
    provider: str

    summary: str
    summary_points: list[str] = Field(default_factory=list)
    summary_markdown: str = ""

    results: list[ResearchResultItem] = Field(default_factory=list)
    selected_sources: list[ResearchSelectedSourceItem] = Field(default_factory=list)
    source_count: int = 0
    extracted_count: int = 0
    ambiguous: bool = False
    sections: ResearchSections | None = None

    meaning_groups: list[dict[str, Any]] = Field(default_factory=list)
    request_id: str | None = None
    response_time: float | None = None
    usage: dict[str, Any] | None = None


class SearchHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    query: str
    topic: str
    provider: str
    result_count: int
    answer: str | None = None
    ambiguous: bool = False
    selected_source_count: int = 0
    meaning_group_count: int = 0
    has_summary: bool = False
    created_at: datetime