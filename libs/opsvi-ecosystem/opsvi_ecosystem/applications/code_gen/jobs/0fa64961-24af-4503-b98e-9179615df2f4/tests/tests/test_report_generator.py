import csv_reporter.report_generator as rg
import pytest


@pytest.fixture
def config_stub():
    class Config:
        pass

    return Config()


@pytest.fixture
def sample_summary():
    return {"category_counts": {"A": 2, "B": 2}, "value_sum": 100}


def test_report_generator_init_stores_config(config_stub):
    generator = rg.ReportGenerator(config_stub)
    assert generator.config == config_stub


@pytest.mark.parametrize("format", ["text", "json", "invalid"])
def test_generate_report_formats(format, sample_summary, config_stub):
    generator = rg.ReportGenerator(config_stub)
    if format == "invalid":
        with pytest.raises(ValueError):
            generator.generate_report(sample_summary, format)
    else:
        output = generator.generate_report(sample_summary, format)
        assert output is not None
        assert isinstance(output, str)
        if format == "json":
            import json

            json.loads(output)  # validate JSON format
