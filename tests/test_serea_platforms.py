import pytest
from unittest.mock import patch, MagicMock
from serea.platforms.facebook import FacebookAdapter
from serea.platforms.instagram import InstagramAdapter
from serea.platforms.tiktok import TikTokAdapter
from serea.models import SocialMediaAccount

pytestmark = pytest.mark.django_db

@pytest.fixture
def facebook_account(agent_setup):
    user, agent = agent_setup
    return SocialMediaAccount.objects.create(agent=agent, platform='facebook', account_id='fb1', access_token='token1')

@pytest.fixture
def instagram_account(agent_setup):
    user, agent = agent_setup
    return SocialMediaAccount.objects.create(agent=agent, platform='instagram', account_id='ig1', access_token='token1', extra_credentials={'instagram_business_account_id': 'ig_biz1'})

@pytest.fixture
def tiktok_account(agent_setup):
    user, agent = agent_setup
    return SocialMediaAccount.objects.create(agent=agent, platform='tiktok', account_id='tk1', access_token='token1')

@patch('serea.platforms.facebook.requests')
def test_facebook_adapter(mock_requests, facebook_account):
    adapter = FacebookAdapter(facebook_account)
    
    # fetch_recent_comments
    mock_get = MagicMock()
    mock_get.json.return_value = {
        'data': [{
            'id': 'p1',
            'comments': {'data': [{'id': 'c1', 'message': 'hello', 'from': {'name': 'user'}}]}
        }]
    }
    mock_requests.get.return_value = mock_get
    
    comments = adapter.fetch_recent_comments()
    assert len(comments) == 1
    assert comments[0]['text'] == 'hello'
    assert comments[0]['id'] == 'c1'
    
    # delete_comment
    mock_del = MagicMock()
    mock_del.json.return_value = {'success': True}
    mock_requests.delete.return_value = mock_del
    adapter.delete_comment('c1')
    mock_requests.delete.assert_called()
    
    # reply_to_comment
    mock_post = MagicMock()
    mock_post.json.return_value = {'id': 'r1'}
    mock_requests.post.return_value = mock_post
    adapter.reply_to_comment('c1', 'hi')
    mock_requests.post.assert_called()
    
    # post text
    mock_post.json.return_value = {'id': 'post1'}
    mock_requests.post.return_value = mock_post
    res = adapter.post("hello")
    assert res.success is True
    assert res.platform_post_id == "post1"

@patch('serea.platforms.instagram.requests')
def test_instagram_adapter(mock_requests, instagram_account):
    adapter = InstagramAdapter(instagram_account)
    
    # fetch_recent_comments
    mock_get_media = MagicMock()
    mock_get_media.json.return_value = {
        'data': [{'id': 'm1'}]
    }
    mock_get_comments = MagicMock()
    mock_get_comments.json.return_value = {
        'data': [{'id': 'c1', 'text': 'nice pic', 'username': 'user'}]
    }
    mock_requests.get.side_effect = [mock_get_media, mock_get_comments]
    comments = adapter.fetch_recent_comments()
    assert len(comments) == 1
    assert comments[0]['text'] == 'nice pic'
    assert comments[0]['id'] == 'c1'
    
    # delete_comment (uses delete, not post!)
    mock_del = MagicMock()
    mock_del.json.return_value = {'success': True}
    mock_requests.delete.return_value = mock_del
    adapter.delete_comment('c1')
    
    # reply_to_comment
    mock_post.json.return_value = {'id': 'r1'}
    mock_requests.post.return_value = mock_post
    adapter.reply_to_comment('c1', 'thanks')
    
    # post photo
    mock_post1 = MagicMock()
    mock_post1.json.return_value = {'id': 'c1'}
    mock_post2 = MagicMock()
    mock_post2.json.return_value = {'id': 'published1'}
    mock_requests.post.side_effect = [mock_post1, mock_post2]
    
    res = adapter.post("caption", media_url="http://img")
    assert res.success is True
    assert res.platform_post_id == "published1"
    
    # post text without image (not supported)
    res = adapter.post("text only")
    assert res.success is False
    assert "media_url is required" in res.error

def test_tiktok_adapter(tiktok_account):
    adapter = TikTokAdapter(tiktok_account)
    
    # Currently tiktok adapter is a stub
    comments = adapter.fetch_recent_comments()
    assert isinstance(comments, list)
    
    res = adapter.post("hello")
    assert res.success is False
    assert "not yet available" in res.error
