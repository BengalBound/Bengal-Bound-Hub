"""Abstract base adapter for all Serea social-media platforms."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PostResult:
    success: bool
    platform_post_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None


@dataclass
class CommentAction:
    action: str          # 'delete' | 'reply' | 'flag' | 'ignore'
    comment_id: str
    reply_text: str = ''


class BasePlatformAdapter(ABC):
    """
    Every platform adapter must implement these methods.
    The account arg is a SocialMediaAccount instance.
    """

    def __init__(self, account):
        self.account = account
        self.token = account.access_token
        self.account_id = account.account_id

    @abstractmethod
    def post(self, caption: str, media_url: Optional[str] = None,
             hashtags: list = field(default_factory=list)) -> PostResult:
        """Publish a post. Returns PostResult."""

    @abstractmethod
    def fetch_recent_comments(self, limit: int = 50) -> list[dict]:
        """Return recent comments as list of dicts: {id, text, author, timestamp}."""

    @abstractmethod
    def delete_comment(self, comment_id: str) -> bool:
        """Delete a comment. Returns True on success."""

    @abstractmethod
    def reply_to_comment(self, comment_id: str, text: str) -> bool:
        """Reply to a comment. Returns True on success."""

    @abstractmethod
    def get_account_insights(self) -> dict:
        """Return basic analytics: {followers, posts, engagement_rate}."""
