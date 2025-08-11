import pytest
import json
import io
from json_data_processor import converter

@pytest.fixture
 def sample_json():
     return {
         "name": "John Doe",
         "age": 30,
         "children": [
             {"name": "Jane", "age": 10},
             {"name": "Doe", "age": 5}
         ],
         "is_employee": true
     }

@pytest.fixture
 def malformed_json_str():
     return '{"name": "John Doe", "age": 30, "children": ["name": "Jane"]'  # missing brackets and commas

@pytest.fixture
 def empty_json():
     return {}


def test_validate_json_data_with_valid_json(sample_json):
    # Should not raise any exception
    assert converter.validate_json_data(sample_json) is None

def test_validate_json_data_with_invalid_json_raises_value_error():
    invalid_data = "not a dict or list"
    with pytest.raises(ValueError):
        converter.validate_json_data(invalid_data)

def test_validate_json_data_with_malformed_json_string_raises_error(malformed_json_str):
    with pytest.raises(ValueError):
        converter.validate_json_data(malformed_json_str)

def test_normalize_json_returns_expected_structure(sample_json):
    normalized = converter._normalize_json(sample_json)
    # Should be a dictionary or list
    assert isinstance(normalized, (dict, list))
    # Check some keys appear in normalized data
    assert 'name' in normalized

def test_json_to_xml_output_contains_expected_tags(sample_json):
    xml_str = converter.json_to_xml(sample_json)
    assert isinstance(xml_str, str)
    # Check root XML tags exist
    assert xml_str.strip().startswith('<root>')
    assert xml_str.strip().endswith('</root>')
    assert '<name>John Doe</name>' in xml_str
    assert '<age>30</age>' in xml_str

def test_json_to_xml_with_empty_json_returns_root_only(empty_json):
    xml_str = converter.json_to_xml(empty_json)
    assert xml_str.strip() == '<root />' or xml_str.strip() == '<root></root>'

def test_json_to_csv_returns_csv_string_with_expected_columns_and_rows(sample_json):
    csv_str = converter.json_to_csv(sample_json)
    assert isinstance(csv_str, str)
    lines = csv_str.split('\n')
    # Should have at least one header line + data lines
    assert len(lines) >= 2
    # CSV header should contain keys from JSON
    headers = lines[0].split(',')
    assert 'name' in headers or 'age' in headers or 'is_employee' in headers
    # Check that each line has the same number of columns
    for line in lines:
        assert len(line.split(',')) == len(headers)

def test_json_to_csv_with_empty_json_returns_empty_string_or_header(empty_json):
    csv_str = converter.json_to_csv(empty_json)
    assert isinstance(csv_str, str)
    # It might return an empty string or CSV with no rows
    assert csv_str == '' or '\n' not in csv_str

def test_json_to_yaml_returns_valid_yaml_string(sample_json):
    yaml_str = converter.json_to_yaml(sample_json)
    assert isinstance(yaml_str, str)
    # Simple check: YAML should contain keys
    assert 'name:' in yaml_str
    assert 'age:' in yaml_str

def test_json_to_yaml_with_empty_json_returns_empty_document(empty_json):
    yaml_str = converter.json_to_yaml(empty_json)
    assert isinstance(yaml_str, str)
    assert yaml_str.strip() in ['', '{}', '---']

@pytest.mark.parametrize('format', ['xml', 'csv', 'yaml'])
def test_convert_json_returns_correct_format_output(sample_json, format):
    output = converter.convert_json(sample_json, format)
    assert isinstance(output, str)
    if format == 'xml':
        assert output.strip().startswith('<root>') or output.strip().startswith('<?xml')
    elif format == 'csv':
        assert '\n' in output
    elif format == 'yaml':
        assert 'name:' in output or 'age:' in output

def test_convert_json_with_unsupported_format_raises_value_error(sample_json):
    with pytest.raises(ValueError):
        converter.convert_json(sample_json, 'unsupported_format')

def test_performance_of_json_to_csv_with_large_dataset():
    large_data = [{"id": i, "value": f"value_{i}"} for i in range(10000)]
    import time
    start = time.time()
    csv_output = converter.json_to_csv(large_data)
    end = time.time()
    elapsed = end - start
    # Should complete within reasonable time (e.g., 1 second)
    assert elapsed < 1.0
    assert csv_output.count('\n') >= 10000

