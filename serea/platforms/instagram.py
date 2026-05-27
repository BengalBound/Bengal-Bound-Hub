"""
Instagram Graph API adapter for Serea.
Instagram posting goes through the Facebook Graph API using the Instagram
Business Account linked to the Facebook Page (auto-detected during OAuth).
"""
import logging
from typing import Optional

import requests

from .base import BasePlatformAdapter, PostResult

logger = logging.getLogger(__name__)

GRAPH = 'https://graph.facebook.com/v18.0'


class InstagramAdapter(BasePlatformAdapter):
    """
    Requires:
      account.account_id  = Instagram Business Account ID (IG-scoped)
      account.access_token = Facebook Page access token (grants IG API access)
    """

    def post(self, caption: str, media_url: Optional[str] = None,
             hashtags: list = None) -> PostResult:
        hashtags = hashtags or []
        full_text = caption
        if hashtags:
            full_text += '\n\n' + ' '.join(f'#{h.lstrip("#")}' for h in hashtags)

        if not media_url:
            return PostResult(success=False, error="Instagram requires a media_url for every post.")

        try:
            # Step 1: Create media container
            container_resp = requests.post(
                f'{GRAPH}/{self.account_id}/media',
                params={
                    'image_url': media_url,
                    'caption': full_text,
                    'access_token': self.token,
                },
                timeout=20,
            )
            container_data = container_resp.json()
            container_id = container_data.get('id')
            if not container_id:
                return PostResult(
                    success=False,
                    error=container_data.get('error', {}).get('message', 'Container creation failed'),
                )

            # Step 2: Publish the container
            publish_resp = requests.post(
                f'{GRAPH}/{self.account_id}/media_publish',
                params={
                    'creation_id': container_id,
                    'access_token': self.token,
                },
                timeout=20,
            )
            pub_data = publish_resp.json()
            if 'id' in pub_data:
                return PostResult(success=True, platform_post_id=pub_data['id'])
            return PostResult(
                success=False,
                error=pub_data.get('error', {}).get('message', 'Publish failed'),
            )
        except Exception as exc:
            logger.exception("InstagramAdapter.post error")
            return PostResult(success=False, error=str(exc))

    def fetch_recent_comments(self, limit: int = 50) -> list:
        try:
            # Get recent media
            media_resp = requests.get(
                f'{GRAPH}/{self.account_id}/media',
                params={
                    'fields': 'id,timestamp',
                    'limit': 10,
                    'access_token': self.token,
                },
                timeout=15,
            )
            comments = []
            for media in media_resp.json().get('data', []):
                c_resp = requests.get(
                    f'{GRAPH}/{media["id"]}/comments',
                    params={
                        'fields': 'id,text,username,timestamp',
                        'access_token': self.token,
                    },
                    timeout=10,
                )
                for c in c_resp.json().get('data', []):
                    comments.append({
                        'id': c['id'],
                        'text': c.get('text', ''),
                        'author': c.get('username', ''),
                        'timestamp': c.get('timestamp', ''),
                        'post_id': media['id'],
                    })
                    if len(comments) >= limit:
                        break
                if len(comments) >= limit:
                    break
            return comments
        except Exception:
            logger.exception("InstagramAdapter.fetch_recent_comments error")
            return []

    def delete_comment(self, comment_id: str) -> bool:
        try:
            resp = requests.delete(
                f'{GRAPH}/{comment_id}',
                params={'access_token': self.token},
                timeout=10,
            )
            return resp.json().get('success', False)
        except Exception:
            logger.exception("InstagramAdapter.delete_comment error")
            return False

    def reply_to_comment(self, comment_id: str, text: str) -> bool:
        try:
            resp = requests.post(
                f'{GRAPH}/{comment_id}/replies',
                params={'message': text, 'access_token': self.token},
                timeout=10,
            )
            return 'id' in resp.json()
        except Exception:
            logger.exception("InstagramAdapter.reply_to_comment error")
            return False

    def get_account_insights(self) -> dict:
        try:
            resp = requests.get(
                f'{GRAPH}/{self.account_id}',
                params={
                    'fields': 'followers_count,media_count,username',
                    'access_token': self.token,
                },
                timeout=10,
            )
            data = resp.json()
            return {
                'followers': data.get('followers_count', 0),
                'posts': data.get('media_count', 0),
                'name': data.get('username', ''),
                'engagement_rate': 0.0,
            }
        except Exception:
            return {}
