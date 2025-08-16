from unittest import mock

import csv_reporter.cli as cli
import pytest


@pytest.fixture
def sample_csv_path(tmp_path):
    file = tmp_path / "sample.csv"
    file.write_text("name,age\nAlice,30\nBob,25")
    return str(file)


@pytest.fixture
def corrupted_csv_path(tmp_path):
    file = tmp_path / "corrupted.csv"
    file.write_text("name,age\nAlice,30\nBob,twentyfive")  # invalid age
    return str(file)


def test_build_arg_parser_returns_parser():
    parser = cli.build_arg_parser()
    assert parser is not None
    parser_str = str(parser)
    # Check that known arguments exist
    for arg in ["csv_file", "--format", "--verbose"]:
        assert arg in parser_str


def test_main_successful_run_with_valid_csv_and_default_format(sample_csv_path):
    test_argv = ["program", sample_csv_path]
    exit_code = cli.main(test_argv)
    assert exit_code == 0


def test_main_with_invalid_csv_file_argument():
    test_argv = ["program", "non_existent.csv"]
    exit_code = cli.main(test_argv)
    assert exit_code != 0


def test_main_help_text_contains_expected_options(capsys):
    parser = cli.build_arg_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--help"])
    captured = capsys.readouterr()
    assert "usage" in captured.out
    assert "--format" in captured.out
    assert "csv_file" in captured.out


@mock.patch("csv_reporter.cli.configure_logging")
def test_main_verbose_flag_enables_logging(mock_config_logging, sample_csv_path):
    test_argv = ["program", sample_csv_path, "--verbose"]
    cli.main(test_argv)
    mock_config_logging.assert_called_once()
    args, kwargs = mock_config_logging.call_args
    assert "level" in kwargs or len(args) > 0
