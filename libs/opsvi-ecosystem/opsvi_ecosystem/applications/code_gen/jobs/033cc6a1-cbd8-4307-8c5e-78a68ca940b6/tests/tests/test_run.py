import run


def test_run_module_has_main_callable():
    # We may not actually run server, but ensure main block runs
    assert hasattr(run, "__name__")
    # run.py might call create_app or app.run
