from pathlib import Path

from test_gpt5.agent.patching.apply_patch_adapter import apply_patch_text


def test_apply_patch_roundtrip(tmp_path: Path) -> None:
    repo = tmp_path
    (repo / "a.txt").write_text("hello\nworld\n")

    patch = """*** Begin Patch
*** Update File: a.txt
  hello
-world
+universe
*** End of File
*** End Patch
"""
    res = apply_patch_text(str(repo), patch)
    assert "Done!" in res
    assert (repo / "a.txt").read_text() == "hello\nuniverse\n"
