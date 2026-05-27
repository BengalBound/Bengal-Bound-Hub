"""Facebook Graph API adapter for Serea."""
import logging
from typing import Optional

import requests

from .base import BasePlatformAdapter, PostResult

logger = logging.getLogger(__name__)

GRAPH = 'https://graph.facebook.com/v18.0'


class FacebookAdapter(BasePlatformAdapter):

    def post(self, caption: str, media_url: Optional[str] = None,
             hashtags: list = None) -> PostResult:
        hashtags = hashtags or []
        full_text = caption
        if hashtags:
            full_text += '\n\n' + ' '.join(f'#{h.lstrip("#")}' for h in hashtags)

        try:
            if media_url:
                resp = requests.post(
                    f'{GRAPH}/{self.account_id}/photos',
                    params={
                        'url': media_url,
                        'caption': full_text,
                        'access_token': self.token,
                    },
                    timeout=20,
                )
            else:
                resp = requests.post(
                    f'{GRAPH}/{self.account_id}/feed',
                    params={'message': full_text, 'access_token': self.token},
                    timeout=20,
                )
            data = resp.json()
            if 'id' in data:
                return PostResult(success=True, platform_post_id=data['id'])
            return PostResult(success=False, error=data.get('error', {}).get('message', 'Unknown error'))
        except Exception as exc:
            logger.exception("FacebookAdapter.post error")
            return PostResult(success=False, error=str(exc))

    def fetch_recent_comments(self, limit: int = 50) -> list:
        try:
            resp = requests.get(
                f'{GRAPH}/{self.account_id}/feed',
                params={
                    'fields': 'id,message,comments{id,message,from,created_time}',
                    'limit': 10,
                    'access_token': self.token,
                },
                timeout=15,
            )
            comments = []
            for post in resp.json().get('data', []):
                for c in post.get('comments', {}).get('data', []):
                    comments.append({
                        'id': c['id'],
                        'text': c.get('message', ''),
                        'author': c.get('from', {}).get('name', ''),
                        'timestamp': c.get('created_time', ''),
                        'post_id': post['id'],
                    })
                    if len(comments) >= limit:
                        break
                if len(comments) >= limit:
                    break
            return comments
        except Exception:
            logger.exception("FacebookAdapter.fetch_recent_comments error")
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
            logger.exception("FacebookAdapter.delete_comment error")
            return False

    def reply_to_comment(self, comment_id: str, text: str) -> bool:
        try:
            resp = requests.post(
                f'{GRAPH}/{comment_id}/comments',
                params={'message': text, 'access_token': self.token},
                timeout=10,
            )
            return 'id' in resp.json()
        except Exception:
            logger.exception("FacebookAdapter.reply_to_comment error")
            return False

    def get_account_insights(self) -> dict:
        try:
            resp = requests.get(
                f'{GRAPH}/{self.account_id}',
                params={
                    'fields': 'fan_count,name',
                    'access_token': self.token,
                },
                timeout=10,
            )
            data = resp.json()
            return {
                'followers': data.get('fan_count', 0),
                'name': data.get('name', ''),
                'posts': 0,
                'engagement_rate': 0.0,
            }
        except Exception:
            return {}
