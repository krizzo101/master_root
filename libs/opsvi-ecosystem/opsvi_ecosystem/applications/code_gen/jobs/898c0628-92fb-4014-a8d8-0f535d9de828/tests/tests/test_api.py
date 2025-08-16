import pytest
import io
import json
from json_data_processor import api
from unittest.mock import MagicMock, patch

@pytest.fixture
def valid_json_dict():
    return {"name": "Tester", "value": 123}

@pytest.fixture
def valid_json_str():
    return json.dumps({"name": "Tester", "value": 123})

@pytest.fixture
def sample_file(valid_json_str):
    return io.BytesIO(valid_json_str.encode('utf-8'))

@pytest.fixture
def invalid_json_str():
    return "{name: no_quotes}"  # invalid JSON

class DummyRequest:
    def __init__(self, json_data=None):
        self.json_data = json_data
    
    def get_json(self):
        if self.json_data is None:
            raise ValueError("No JSON")
        return self.json_data

@pytest.fixture
 def dummy_request(valid_json_dict):
     return DummyRequest(json_data=valid_json_dict)

@pytest.fixture
 def dummy_request_invalid():
     return DummyRequest(json_data=None)



def test_convert_json_endpoint_success_returns_expected_output(dummy_request):
    # Patch the convert_json method to isolate endpoint logic
    with patch('json_data_processor.api.convert_json', return_value='converted_data') as mock_convert:
        dummy_request.json_data = {"foo":"bar"}
        response = api.convert_json_endpoint(dummy_request)
        # Should call convert_json once
        mock_convert.assert_called_once()
        # Response should be string data
        assert isinstance(response, str)
        assert response == 'converted_data'

def test_convert_json_endpoint_handles_invalid_json_gracefully():
    # Using dummy request that raises error on get_json
    bad_request = DummyRequest(json_data=None)
    bad_request.get_json = MagicMock(side_effect=ValueError("Invalid JSON"))
    with pytest.raises(ValueError):
        api.convert_json_endpoint(bad_request)

@pytest.mark.parametrize('output_format', ['xml', 'csv', 'yaml'])
def test_upload_and_convert_returns_expected_format(sample_file, output_format):
    # Patch the convert_json to isolate
    with patch('json_data_processor.api.convert_json', return_value=f'{output_format}_content') as mock_convert:
        result = api.upload_and_convert(sample_file, output_format)
        mock_convert.assert_called_once()
        assert isinstance(result, str)
        assert result == f'{output_format}_content'

def test_upload_and_convert_raises_error_on_non_json_file():
    fake_file = io.BytesIO(b"This is not JSON data")
    with pytest.raises(ValueError):
        api.upload_and_convert(fake_file, 'json')  # specify json as output format for simplicity


def test_health_check_returns_expected_string():
    result = api.health_check()
    assert isinstance(result, str)
    assert 'healthy' in result.lower() or 'ok' in result.lower()

def test_convert_request_creation_with_valid_data(valid_json_dict):
    # Create ConvertRequest instance
    req = api.ConvertRequest(json_data=valid_json_dict, output_format='xml')
    assert req.json_data == valid_json_dict
    assert req.output_format == 'xml'

