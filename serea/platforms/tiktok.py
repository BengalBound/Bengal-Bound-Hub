"""
TikTok for Business adapter — STUB.
TikTok requires app approval via the TikTok for Business platform.
All methods return graceful stubs until credentials are configured.
"""
import logging
from typing import Optional

from .base import BasePlatformAdapter, PostResult

logger = logging.getLogger(__name__)


class TikTokAdapter(BasePlatformAdapter):
    """
    Stub adapter for TikTok.
    Full implementation requires:
      - Approved TikTok for Business developer account
      - TIKTOK_CLIENT_KEY + TIKTOK_CLIENT_SECRET in settings
      - OAuth2 PKCE flow for user token acquisition
    """

    STUB_MSG = (
        "TikTok posting is not yet available. "
        "Configure TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET to enable it."
    )

    def post(self, caption: str, media_url: Optional[str] = None,
             hashtags: list = None) -> PostResult:
        logger.info("TikTokAdapter.post called (stub)")
        return PostResult(success=False, error=self.STUB_MSG)

    def fetch_recent_comments(self, limit: int = 50) -> list:
        logger.info("TikTokAdapter.fetch_recent_comments called (stub)")
        return []

    def delete_comment(self, comment_id: str) -> bool:
        logger.info("TikTokAdapter.delete_comment called (stub)")
        return False

    def reply_to_comment(self, comment_id: str, text: str) -> bool:
        logger.info("TikTokAdapter.reply_to_comment called (stub)")
        return False

    def get_account_insights(self) -> dict:
        return {'followers': 0, 'posts': 0, 'engagement_rate': 0.0, 'stub': True}
