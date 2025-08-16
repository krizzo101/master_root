import pytest
import pandas as pd
import csv_reporter.data_processor as dp
from unittest import mock


@pytest.fixture
def config_stub():
    class Config:
        pass

    return Config()


@pytest.fixture
def sample_df():
    return pd.DataFrame({"category": ["A", "B", "A", "B"], "value": [10, 20, 30, 40]})


def test_data_processor_init_stores_config(config_stub):
    processor = dp.DataProcessor(config_stub)
    assert processor.config == config_stub


def test_process_returns_summary_with_progress(sample_df, config_stub):
    processor = dp.DataProcessor(config_stub)
    progress_calls = []

    def progress_cb(n):
        progress_calls.append(n)

    result = processor.process(sample_df, progress_cb)
    assert isinstance(result, dict)
    assert "category_counts" in result
    # Confirm progress callback called multiple times
    assert len(progress_calls) > 0


def test_process_with_none_dataframe_raises_type_error(config_stub):
    processor = dp.DataProcessor(config_stub)
    with pytest.raises(TypeError):
        processor.process(None, lambda n: None)
