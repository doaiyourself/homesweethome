"""Re-export models so `from app.models import Article` works."""
from .article import Article
from .base import Base, TimestampMixin
from .user_action import ActionType, UserAction
from .user_pref import SINGLETON_ID, UserPref, default_weights

__all__ = [
    "Base",
    "TimestampMixin",
    "Article",
    "UserAction",
    "ActionType",
    "UserPref",
    "SINGLETON_ID",
    "default_weights",
]
