import sys

import csv_reporter.utils as utils


def test_print_progress_bar_context_manager_behavior():
    pbar = utils.print_progress_bar(
        total=5, desc="Testing", width=10, stream=sys.stdout
    )
    with pbar as pb:
        for i in range(5):
            pb.print_bar(i)
    # No exception raised means success


def test_print_bar_outputs_progress_to_stream(capsys):
    pbar = utils.print_progress_bar(total=3, desc="Progress", width=20, stream=None)
    pbar.print_bar(1)
    captured = capsys.readouterr()
    assert "Progress" in captured.out


def test_updater_closure_reports_progress_correctly(capsys):
    pbar = utils.print_progress_bar(total=3, desc="Prog", width=10, stream=None)
    callback = pbar.updater()
    with pbar:
        for i in range(3):
            callback(i)
    captured = capsys.readouterr()
    assert "Prog" in captured.out
