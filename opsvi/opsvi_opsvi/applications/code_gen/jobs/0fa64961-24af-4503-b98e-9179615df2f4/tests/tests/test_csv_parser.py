import pytest
import pandas as pd
import csv_reporter.csv_parser as parser
from unittest import mock


@pytest.fixture
def config_stub():
    class Config:
        def pandas_csv_args(self):
            return {}

    return Config()


@mock.patch("pandas.read_csv")
def test_parse_csv_success(mock_read_csv, config_stub):
    mock_df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    mock_read_csv.return_value = mock_df
    csv_parser = parser.CSVParser(config_stub)
    df = csv_parser.parse_csv("fake_path.csv")
    assert isinstance(df, pd.DataFrame)
    assert df.equals(mock_df)


def test_csv_parser_init_stores_config(config_stub):
    csv_parser = parser.CSVParser(config_stub)
    assert csv_parser.config == config_stub


def test_parse_csv_with_invalid_file_raises_exception(config_stub):
    csv_parser = parser.CSVParser(config_stub)
    with pytest.raises(Exception):
        csv_parser.parse_csv("non_existent.csv")


def test_parse_csv_with_malformed_csv(tmp_path, config_stub):
    file_path = tmp_path / "malformed.csv"
    file_path.write_text("a,b\n1,2\n3")  # uneven columns
    csv_parser = parser.CSVParser(config_stub)
    with pytest.raises(Exception):
        csv_parser.parse_csv(str(file_path))
