from app.exceptions import NotFoundException, ValidationException


def test_not_found_exception_initializes_with_detail():
    detail_msg = "Item not found"
    exc = NotFoundException(detail=detail_msg)
    assert str(exc) == detail_msg


def test_validation_exception_initializes_with_detail():
    detail_msg = "Validation failed"
    exc = ValidationException(detail=detail_msg)
    assert str(exc) == detail_msg
