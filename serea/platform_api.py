"""
serea/platform_api.py
─────────────────────
Thin wrappers around the Meta Graph API (Facebook + Instagram)
and the LinkedIn v2 UGC Posts API.

Usage:
    from serea.platform_api import FacebookAPI, InstagramAPI, LinkedInAPI, PlatformAPIError

    fb = FacebookAPI(page_id=account.account_id, access_token=account.access_token)
    fb.post_text("Hello world!")

All methods raise PlatformAPIError on failure.
Tokens passed in are already decrypted by EncryptedTextField — no manual
decryption needed here.
"""

import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.facebook.com/v18.0"
LINKEDIN_BASE = "https://api.linkedin.com/v2"


class PlatformAPIError(Exception):
    """Raised when a platform API call returns an error or unexpected status."""


# ─────────────────────────────────────────────────────────────────────────────
# Facebook  (Meta Graph API v18.0)
# ─────────────────────────────────────────────────────────────────────────────

class FacebookAPI:
    """
    Manages a single Facebook Page via the Meta Graph API.

    page_id      — Facebook Page ID
    access_token — Page Access Token (already decrypted)
    """

    def __init__(self, page_id: str, access_token: str):
        self.page_id = page_id
        self.token = access_token

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        params = params or {}
        params['access_token'] = self.token
        r = requests.get(f"{GRAPH_BASE}/{path}", params=params, timeout=15)
        data = r.json()
        if 'error' in data:
            msg = data['error'].get('message', str(data['error']))
            raise PlatformAPIError(f"Facebook API error: {msg}")
        return data

    def _post_form(self, path: str, payload: dict) -> dict:
        payload = dict(payload)
        payload['access_token'] = self.token
        r = requests.post(f"{GRAPH_BASE}/{path}", data=payload, timeout=15)
        data = r.json()
        if 'error' in data:
            msg = data['error'].get('message', str(data['error']))
            raise PlatformAPIError(f"Facebook API error: {msg}")
        return data

    def _delete(self, path: str) -> bool:
        params = {'access_token': self.token}
        r = requests.delete(f"{GRAPH_BASE}/{path}", params=params, timeout=15)
        data = r.json()
        if 'error' in data:
            msg = data['error'].get('message', str(data['error']))
            raise PlatformAPIError(f"Facebook delete error: {msg}")
        return data.get('success', False)

    # ── Reading ───────────────────────────────────────────────────────────────

    def get_recent_posts(self, limit: int = 10) -> list:
        """Return up to `limit` recent Page posts."""
        data = self._get(
            f"{self.page_id}/posts",
            {'fields': 'id,message,created_time', 'limit': limit},
        )
        return data.get('data', [])

    def get_comments(self, object_id: str, after: Optional[str] = None) -> list:
        """Fetch top-level comments on a post or page object."""
        params = {
            'fields': 'id,message,from,created_time',
            'limit': 50,
        }
        if after:
            params['after'] = after
        data = self._get(f"{object_id}/comments", params)
        return data.get('data', [])

    # ── Writing ───────────────────────────────────────────────────────────────

    def post_text(self, message: str) -> str:
        """Publish a text update to the Page. Returns the new post ID."""
        data = self._post_form(f"{self.page_id}/feed", {'message': message})
        return data.get('id', '')

    def post_photo(self, message: str, photo_url: str) -> str:
        """Publish a photo with caption. Returns the post ID."""
        data = self._post_form(
            f"{self.page_id}/photos",
            {'message': message, 'url': photo_url},
        )
        return data.get('post_id') or data.get('id', '')

    def reply_to_comment(self, comment_id: str, message: str) -> str:
        """Reply to a comment. Returns the reply comment ID."""
        data = self._post_form(f"{comment_id}/comments", {'message': message})
        return data.get('id', '')

    def delete_comment(self, comment_id: str) -> bool:
        """Delete a comment. Returns True on success."""
        return self._delete(comment_id)


# ─────────────────────────────────────────────────────────────────────────────
# Instagram  (via Meta Graph API — requires Instagram Business Account)
# ─────────────────────────────────────────────────────────────────────────────

class InstagramAPI:
    """
    Instagram Business API via Meta Graph API.

    ig_account_id — Instagram Business Account ID
    access_token  — Page Access Token from the linked Facebook Page
    """

    def __init__(self, ig_account_id: str, access_token: str):
        self.ig_id = ig_account_id
        self.token = access_token

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        params = params or {}
        params['access_token'] = self.token
        r = requests.get(f"{GRAPH_BASE}/{path}", params=params, timeout=15)
        data = r.json()
        if 'error' in data:
            msg = data['error'].get('message', str(data['error']))
            raise PlatformAPIError(f"Instagram API error: {msg}")
        return data

    def _post_form(self, path: str, payload: dict) -> dict:
        payload = dict(payload)
        payload['access_token'] = self.token
        r = requests.post(f"{GRAPH_BASE}/{path}", data=payload, timeout=15)
        data = r.json()
        if 'error' in data:
            msg = data['error'].get('message', str(data['error']))
            raise PlatformAPIError(f"Instagram API error: {msg}")
        return data

    # ── Reading ───────────────────────────────────────────────────────────────

    def get_media(self, limit: int = 10) -> list:
        """Return recent media objects."""
        data = self._get(
            f"{self.ig_id}/media",
            {'fields': 'id,caption,timestamp,like_count,comments_count', 'limit': limit},
        )
        return data.get('data', [])

    def get_comments(self, media_id: str, after: Optional[str] = None) -> list:
        """Fetch comments on a media object."""
        params = {'fields': 'id,text,username,timestamp', 'limit': 50}
        if after:
            params['after'] = after
        data = self._get(f"{media_id}/comments", params)
        return data.get('data', [])

    # ── Writing ───────────────────────────────────────────────────────────────

    def reply_to_comment(self, media_id: str, message: str) -> str:
        """Reply to a comment thread on a media object. Returns reply ID."""
        data = self._post_form(f"{media_id}/replies", {'message': message})
        return data.get('id', '')

    def hide_comment(self, comment_id: str, hide: bool = True) -> bool:
        """Hide (or unhide) a comment. Instagram doesn't expose a delete endpoint to most apps."""
        payload = {'access_token': self.token, 'hide': str(hide).lower()}
        r = requests.post(f"{GRAPH_BASE}/{comment_id}", data=payload, timeout=15)
        data = r.json()
        if 'error' in data:
            msg = data['error'].get('message', str(data['error']))
            raise PlatformAPIError(f"Instagram hide error: {msg}")
        return data.get('success', False)

    def post_photo(self, image_url: str, caption: str) -> str:
        """
        Publish a photo post using the two-step container API.
        Returns the published media ID.
        """
        container = self._post_form(
            f"{self.ig_id}/media",
            {'image_url': image_url, 'caption': caption},
        )
        creation_id = container.get('id')
        if not creation_id:
            raise PlatformAPIError("Instagram: failed to create media container.")
        published = self._post_form(
            f"{self.ig_id}/media_publish",
            {'creation_id': creation_id},
        )
        return published.get('id', '')

    def send_dm(self, recipient_id: str, message: str) -> str:
        """Send a DM via the Messenger API (requires linked Facebook Page token)."""
        payload = {
            'recipient': {'id': recipient_id},
            'message': {'text': message},
            'access_token': self.token,
        }
        r = requests.post(f"{GRAPH_BASE}/me/messages", json=payload, timeout=15)
        data = r.json()
        if 'error' in data:
            msg = data['error'].get('message', str(data['error']))
            raise PlatformAPIError(f"Instagram DM error: {msg}")
        return data.get('message_id', '')


# ─────────────────────────────────────────────────────────────────────────────
# LinkedIn  (v2 UGC Posts API — organization pages)
# ─────────────────────────────────────────────────────────────────────────────

class LinkedInAPI:
    """
    LinkedIn v2 UGC Posts API for organization page posting and comment management.

    org_id       — numeric organization ID (from linkedin.com/company/<org_id>/)
    access_token — OAuth 2.0 token with w_organization_social scope
    """

    def __init__(self, org_id: str, access_token: str):
        self.org_id = org_id
        self.token = access_token
        self._headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0',
        }

    def post_text(self, text: str) -> str:
        """Publish a text update to the organization page. Returns the post URN."""
        payload = {
            'author': f'urn:li:organization:{self.org_id}',
            'lifecycleState': 'PUBLISHED',
            'specificContent': {
                'com.linkedin.ugc.ShareContent': {
                    'shareCommentary': {'text': text},
                    'shareMediaCategory': 'NONE',
                }
            },
            'visibility': {
                'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC',
            },
        }
        r = requests.post(
            f"{LINKEDIN_BASE}/ugcPosts",
            json=payload,
            headers=self._headers,
            timeout=15,
        )
        if not r.ok:
            raise PlatformAPIError(f"LinkedIn post error {r.status_code}: {r.text[:200]}")
        return r.headers.get('x-restli-id', '')

    def post_with_image(self, text: str, image_url: str, title: str = '') -> str:
        """
        Publish an image post to the organization page.
        Uses the two-step register-upload → post flow.
        Returns the post URN.
        """
        # Step 1: Register upload
        reg_payload = {
            'registerUploadRequest': {
                'recipes': ['urn:li:digitalmediaRecipe:feedshare-image'],
                'owner': f'urn:li:organization:{self.org_id}',
                'serviceRelationships': [{
                    'relationshipType': 'OWNER',
                    'identifier': 'urn:li:userGeneratedContent',
                }],
            }
        }
        r = requests.post(
            f"{LINKEDIN_BASE}/assets?action=registerUpload",
            json=reg_payload,
            headers=self._headers,
            timeout=15,
        )
        if not r.ok:
            raise PlatformAPIError(f"LinkedIn register upload error {r.status_code}: {r.text[:200]}")

        result = r.json().get('value', {})
        upload_url = (
            result.get('uploadMechanism', {})
            .get('com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest', {})
            .get('uploadUrl', '')
        )
        asset_urn = result.get('asset', '')

        if not upload_url or not asset_urn:
            raise PlatformAPIError("LinkedIn: failed to obtain upload URL from register response.")

        # Step 2: Download and upload the image
        img_r = requests.get(image_url, timeout=15)
        if not img_r.ok:
            raise PlatformAPIError(f"Could not download image from {image_url}")

        up_r = requests.post(
            upload_url,
            data=img_r.content,
            headers={'Authorization': f'Bearer {self.token}'},
            timeout=30,
        )
        if not up_r.ok:
            raise PlatformAPIError(f"LinkedIn image upload failed {up_r.status_code}")

        # Step 3: Publish post with the uploaded asset
        payload = {
            'author': f'urn:li:organization:{self.org_id}',
            'lifecycleState': 'PUBLISHED',
            'specificContent': {
                'com.linkedin.ugc.ShareContent': {
                    'shareCommentary': {'text': text},
                    'shareMediaCategory': 'IMAGE',
                    'media': [{
                        'status': 'READY',
                        'description': {'text': text[:200]},
                        'media': asset_urn,
                        'title': {'text': title or text[:60]},
                    }],
                }
            },
            'visibility': {'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'},
        }
        post_r = requests.post(
            f"{LINKEDIN_BASE}/ugcPosts",
            json=payload,
            headers=self._headers,
            timeout=15,
        )
        if not post_r.ok:
            raise PlatformAPIError(f"LinkedIn post error {post_r.status_code}: {post_r.text[:200]}")
        return post_r.headers.get('x-restli-id', '')

    def get_organization_comments(self, post_urn: str) -> list:
        """Fetch comments on an organization post."""
        encoded = requests.utils.quote(post_urn, safe='')
        r = requests.get(
            f"{LINKEDIN_BASE}/socialActions/{encoded}/comments",
            headers=self._headers,
            timeout=15,
        )
        if not r.ok:
            raise PlatformAPIError(
                f"LinkedIn get comments error {r.status_code}: {r.text[:200]}"
            )
        return r.json().get('elements', [])

    def delete_comment(self, comment_urn: str) -> bool:
        """Delete a comment by URN."""
        encoded = requests.utils.quote(comment_urn, safe='')
        r = requests.delete(
            f"{LINKEDIN_BASE}/socialActions/{encoded}",
            headers=self._headers,
            timeout=15,
        )
        if not r.ok:
            raise PlatformAPIError(
                f"LinkedIn delete comment error {r.status_code}: {r.text[:200]}"
            )
        return True


# ─────────────────────────────────────────────────────────────────────────────
# Factory helper
# ─────────────────────────────────────────────────────────────────────────────

def get_api_for_account(account):
    """
    Return the appropriate API wrapper for a SocialMediaAccount instance.
    Raises PlatformAPIError if the platform is unsupported or credentials missing.
    """
    token = account.access_token
    if not token:
        raise PlatformAPIError(
            f"No access token stored for {account.get_platform_display()} account '{account.account_name}'."
        )

    platform = account.platform
    extra = account.extra_credentials or {}

    if platform == 'facebook':
        return FacebookAPI(page_id=account.account_id, access_token=token)

    if platform == 'instagram':
        ig_id = extra.get('instagram_business_account_id') or account.account_id
        return InstagramAPI(ig_account_id=ig_id, access_token=token)

    if platform == 'linkedin':
        return LinkedInAPI(org_id=account.account_id, access_token=token)

    raise PlatformAPIError(f"Unsupported platform for automated posting: {platform}")
