from .facebook import FacebookAdapter
from .instagram import InstagramAdapter
from .tiktok import TikTokAdapter

ADAPTERS = {
    'facebook': FacebookAdapter,
    'instagram': InstagramAdapter,
    'tiktok': TikTokAdapter,
}


def get_adapter(platform: str, account):
    """Return an initialised platform adapter for the given SocialMediaAccount."""
    cls = ADAPTERS.get(platform)
    if cls is None:
        raise ValueError(f"No adapter for platform '{platform}'")
    return cls(account)
