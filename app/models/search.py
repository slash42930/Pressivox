from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SearchHistory(Base):
    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    query: Mapped[str] = mapped_column(String(500), index=True)
    topic: Mapped[str] = mapped_column(String(50), default="general")
    provider: Mapped[str] = mapped_column(String(50), default="serper")
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    ambiguous: Mapped[bool] = mapped_column(Boolean, default=False)
    selected_source_count: Mapped[int] = mapped_column(Integer, default=0)
    meaning_group_count: Mapped[int] = mapped_column(Integer, default=0)
    has_summary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())