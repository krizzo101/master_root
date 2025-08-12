"""Unit tests for pipeline sequential runner."""

from pathlib import Path

from applications.code_gen.pipeline import build_pipeline


def test_pipeline_runs(tmp_path: Path) -> None:
    pipeline = build_pipeline()
    state = {"request": "generate hello script", "output_dir": tmp_path}

    result = pipeline.invoke(state)

    assert (tmp_path / "DONE").exists()
    assert "requirements" in result
    assert "architecture" in result
    assert "code_bundle" in result
    assert "test_report" in result
    assert "doc_set" in result
