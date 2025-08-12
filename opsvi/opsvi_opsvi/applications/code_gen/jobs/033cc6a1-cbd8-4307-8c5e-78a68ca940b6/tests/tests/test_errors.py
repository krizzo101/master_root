from app.errors import internal_error, not_found_error, unhandled_exception


def test_not_found_error_returns_404_response():
    class DummyError:
        pass

    response = not_found_error(DummyError())
    assert response.status_code == 404
    # Response data should include 'Not Found'
    assert b"Not Found" in response.data or b"404" in response.data


def test_internal_error_returns_500_response():
    class DummyError:
        pass

    response = internal_error(DummyError())
    assert response.status_code == 500
    assert b"Internal Server Error" in response.data or b"500" in response.data


def test_unhandled_exception_logs_and_returns_500_response(caplog):
    caplog.set_level("ERROR")

    class DummyException(Exception):
        pass

    e = DummyException("fail")
    response = unhandled_exception(e)

    # Check response status
    assert response.status_code == 500
    # Check error message in response data
    assert b"Internal Server Error" in response.data or b"500" in response.data
    # Check error is logged
    assert any("ERROR" in record.levelname for record in caplog.records)
    assert any("fail" in record.message for record in caplog.records)
