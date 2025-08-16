import pytest
from simple_news_scraper.output import OutputHandler


def test_print_headlines_outputs_correctly(capsys):
    headlines = ["Headline 1", "Headline 2"]
    OutputHandler.print_headlines(headlines)
    captured = capsys.readouterr()
    for headline in headlines:
        assert headline in captured.out


def test_save_headlines_writes_file_and_handles_errors(tmp_path):
    headlines = ["Headline 1", "Headline 2"]
    file_path = tmp_path / "headlines.txt"
    OutputHandler.save_headlines(headlines, str(file_path))
    with open(file_path) as f:
        contents = f.read()
    for headline in headlines:
        assert headline in contents


def test_save_headlines_raises_for_invalid_path():
    headlines = ["Headline 1"]
    invalid_path = "/invalid_path/headlines.txt"
    with pytest.raises(Exception):
        OutputHandler.save_headlines(headlines, invalid_path)
