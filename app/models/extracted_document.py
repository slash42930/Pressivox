from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ExtractedDocument(Base):
    __tablename__ = "extracted_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    url: Mapped[str] = mapped_column(String(2000), index=True)
    final_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    title: Mapped[str] = mapped_column(String(1000))
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    extracted_text: Mapped[str] = mapped_column(Text)
    content_length: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())