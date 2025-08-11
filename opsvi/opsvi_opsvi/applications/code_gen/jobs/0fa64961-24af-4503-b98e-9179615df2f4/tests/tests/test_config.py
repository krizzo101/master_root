import pytest
import yaml
import csv_reporter.config as config
import os
import tempfile


def test_config_init_default_values():
    conf = config.Config()
    assert hasattr(conf, "settings")


def test_load_from_file_reads_yaml_and_merges(tmp_path):
    file_path = tmp_path / "config.yaml"
    yaml_content = """
    output:
      format: json
      path: ./reports
    csv:
      delimiter: ","
    """
    file_path.write_text(yaml_content)
    conf = config.Config()
    conf.load_from_file(str(file_path))
    assert conf.settings["output"]["format"] == "json"
    assert isinstance(conf.settings["csv"], dict)


def test_pandas_csv_args_returns_dict_keys():
    conf = config.Config()
    res = conf.pandas_csv_args()
    assert isinstance(res, dict)
    # Common keys that pandas read_csv accepts
    for key in ["delimiter", "quotechar", "header"]:
        assert key in res or len(res) == 0


def test_recursive_update_merges_dicts_correctly():
    base = {"a": 1, "b": {"c": 2}}
    updates = {"b": {"d": 3}, "e": 4}
    merged = config.Config._recursive_update(base, updates)
    assert merged["a"] == 1
    assert merged["b"]["c"] == 2
    assert merged["b"]["d"] == 3
    assert merged["e"] == 4


def test_repr_contains_settings():
    conf = config.Config()
    rep = repr(conf)
    assert isinstance(rep, str)
    assert "Config" in rep
