import subprocess
import sys
import tempfile
from pathlib import Path
import csv
import os


def test_cli_text_report(tmp_path):
    # Assemble a small CSV
    csv_path = tmp_path / "people.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["age", "gender"])
        writer.writerow([25, "M"])
        writer.writerow([35, "M"])
        writer.writerow([30, "F"])
        writer.writerow(["", "F"])
    # Output file
    out_path = tmp_path / "report.txt"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "csv_reporter.cli",
            "--input",
            str(csv_path),
            "--report",
            "text",
            "--output",
            str(out_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert out_path.read_text().startswith("CSV Analysis Report")


def test_cli_json_stdout(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("num\n1\n2\n3\n", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "csv_reporter.cli",
            "--input",
            str(csv_path),
            "--report",
            "json",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "{" in result.stdout


def test_cli_wrong_file():
    # Should give a nonzero exit code for missing file
    result = subprocess.run(
        [sys.executable, "-m", "csv_reporter.cli", "--input", "no_such_file.csv"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "not found" in result.stderr.lower() or "Error:" in result.stderr


def test_cli_config_file(tmp_path):
    # Custom config (tab-separated)
    csv_path = tmp_path / "data.tsv"
    csv_path.write_text("foo\tbar\n1\ta\n2\tb\n", encoding="utf-8")
    config_path = tmp_path / "custom.yaml"
    config_path.write_text('csv:\n  delimiter: "\t"\n', encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "csv_reporter.cli",
            "--input",
            str(csv_path),
            "--config",
            str(config_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "CSV Analysis Report" in result.stdout or "{" in result.stdout
