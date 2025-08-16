import pytest
from unittest.mock import MagicMock, patch
from opsvi_data.providers.redis_provider import RedisProvider, RedisConfig

@pytest.fixture
def mock_redis_client():
    with patch('redis.Redis') as mock_redis:
        yield mock_redis.return_value

@pytest.fixture
def redis_provider(mock_redis_client):
    config = RedisConfig()
    provider = RedisProvider(config)
    provider.client = mock_redis_client
    return provider

def test_xadd(redis_provider, mock_redis_client):
    stream = "test_stream"
    fields = {"key": "value"}
    mock_redis_client.xadd.return_value = "12345-0"
    
    message_id = redis_provider.xadd(stream, fields)
    
    mock_redis_client.xadd.assert_called_once_with(stream, fields, maxlen=None, approximate=True)
    assert message_id == "12345-0"

def test_xgroup_create(redis_provider, mock_redis_client):
    stream = "test_stream"
    group_name = "test_group"
    
    result = redis_provider.xgroup_create(stream, group_name)
    
    mock_redis_client.xgroup_create.assert_called_once_with(stream, group_name, mkstream=True)
    assert result is True

def test_xreadgroup(redis_provider, mock_redis_client):
    group_name = "test_group"
    consumer_name = "test_consumer"
    streams = {"test_stream": ">"}
    
    mock_redis_client.xreadgroup.return_value = [("test_stream", [("12345-0", {"key": "value"})])]
    
    result = redis_provider.xreadgroup(group_name, consumer_name, streams)
    
    mock_redis_client.xreadgroup.assert_called_once_with(group_name, consumer_name, streams, count=1, block=0)
    assert result is not None
    assert len(result) > 0

def test_xack(redis_provider, mock_redis_client):
    stream = "test_stream"
    group_name = "test_group"
    message_id = "12345-0"
    
    mock_redis_client.xack.return_value = 1
    
    result = redis_provider.xack(stream, group_name, message_id)
    
    mock_redis_client.xack.assert_called_once_with(stream, group_name, message_id)
    assert result == 1
