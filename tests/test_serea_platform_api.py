import pytest
import requests
from unittest.mock import patch, MagicMock
from serea.platform_api import FacebookAPI, InstagramAPI, LinkedInAPI, get_api_for_account, PlatformAPIError
from serea.models import SocialMediaAccount
from serea.platforms.facebook import FacebookAdapter
from serea.platforms.instagram import InstagramAdapter

pytestmark = pytest.mark.django_db

# Mock requests.get and requests.post
@patch('serea.platform_api.requests.get')
def test_facebook_api_get_recent_posts(mock_get):
    fb = FacebookAPI("123", "token")
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": [{"id": "p1", "message": "hello"}]}
    mock_get.return_value = mock_response
    
    posts = fb.get_recent_posts(limit=10)
    assert len(posts) == 1
    assert posts[0]['id'] == 'p1'

@patch('serea.platform_api.requests.post')
def test_facebook_api_post_text(mock_post):
    fb = FacebookAPI("123", "token")
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "post1"}
    mock_post.return_value = mock_response
    
    post_id = fb.post_text("hello")
    assert post_id == "post1"

@patch('serea.platform_api.requests.get')
def test_facebook_api_error(mock_get):
    fb = FacebookAPI("123", "token")
    mock_response = MagicMock()
    mock_response.json.return_value = {"error": {"message": "Bad token"}}
    mock_get.return_value = mock_response
    
    with pytest.raises(PlatformAPIError, match="Bad token"):
        fb.get_recent_posts()

@patch('serea.platform_api.requests.get')
def test_instagram_api_get_media(mock_get):
    ig = InstagramAPI("ig123", "token")
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": [{"id": "m1"}]}
    mock_get.return_value = mock_response
    
    media = ig.get_media()
    assert len(media) == 1

@patch('serea.platform_api.requests.post')
def test_instagram_api_post_photo(mock_post):
    ig = InstagramAPI("ig123", "token")
    
    # Needs two steps
    mock_response1 = MagicMock()
    mock_response1.json.return_value = {"id": "c1"}
    
    mock_response2 = MagicMock()
    mock_response2.json.return_value = {"id": "published1"}
    
    mock_post.side_effect = [mock_response1, mock_response2]
    
    post_id = ig.post_photo("url", "caption")
    assert post_id == "published1"

@patch('serea.platform_api.requests.post')
def test_linkedin_api_post_text(mock_post):
    li = LinkedInAPI("org1", "token")
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.headers = {'x-restli-id': 'urn1'}
    mock_post.return_value = mock_response
    
    res = li.post_text("hello")
    assert res == "urn1"

@patch('serea.platform_api.requests.post')
@patch('serea.platform_api.requests.get')
def test_linkedin_api_post_with_image(mock_get, mock_post):
    li = LinkedInAPI("org1", "token")
    
    # Step 1: register upload
    mock_reg = MagicMock()
    mock_reg.ok = True
    mock_reg.json.return_value = {
        "value": {
            "uploadMechanism": {
                "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest": {
                    "uploadUrl": "http://upload"
                }
            },
            "asset": "urn:asset1"
        }
    }
    
    # Step 2: Download image (mock_get)
    mock_img = MagicMock()
    mock_img.ok = True
    mock_img.content = b"image_data"
    mock_get.return_value = mock_img
    
    # Step 2.5: Upload image (mock_post)
    mock_up = MagicMock()
    mock_up.ok = True
    
    # Step 3: Publish (mock_post)
    mock_pub = MagicMock()
    mock_pub.ok = True
    mock_pub.headers = {'x-restli-id': 'urn:post1'}
    
    mock_post.side_effect = [mock_reg, mock_up, mock_pub]
    
    res = li.post_with_image("Text", "http://image")
    assert res == "urn:post1"

def test_get_api_for_account(user_factory):
    account = SocialMediaAccount(platform='facebook', account_id='123', access_token='token')
    api = get_api_for_account(account)
    assert isinstance(api, FacebookAPI)
    
    account2 = SocialMediaAccount(platform='instagram', account_id='123', access_token='token')
    api2 = get_api_for_account(account2)
    assert isinstance(api2, InstagramAPI)
    
    account3 = SocialMediaAccount(platform='linkedin', account_id='123', access_token='token')
    api3 = get_api_for_account(account3)
    assert isinstance(api3, LinkedInAPI)
    
    account4 = SocialMediaAccount(platform='tiktok', account_id='123', access_token='token')
    with pytest.raises(PlatformAPIError):
        get_api_for_account(account4)
        
    account.access_token = None
    with pytest.raises(PlatformAPIError):
        get_api_for_account(account)
