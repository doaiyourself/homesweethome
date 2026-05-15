"""UserAction model — per-article favorite / hidden flag."""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ActionType(StrEnum):
    FAVORITE = "favorite"
    HIDDEN = "hidden"


class UserAction(Base):
    __tablename__ = "user_actions"
    __table_args__ = (
        UniqueConstraint("article_no", "action_type", name="uq_user_actions_article_action"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_no: Mapped[str] = mapped_column(
        String(32), ForeignKey("articles.article_no", ondelete="CASCADE"), nullable=False, index=True
    )
    action_type: Mapped[str] = mapped_column(String(16), nullable=False)
    note: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
