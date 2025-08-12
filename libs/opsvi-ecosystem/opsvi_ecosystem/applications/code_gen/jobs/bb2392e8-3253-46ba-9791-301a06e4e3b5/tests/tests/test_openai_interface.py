from unittest import mock

from multiagent_cli.openai_interface import OpenAIReasoningInterface


def test_openai_interface_init_sets_attributes():
    fake_config = {"api_key": "dummy"}
    fake_logger = mock.Mock()
    interface = OpenAIReasoningInterface(fake_config, fake_logger)
    assert interface.config == fake_config
    assert interface.logger == fake_logger


def test_validate_structured_response_accepts_valid_json():
    interface = OpenAIReasoningInterface({}, mock.Mock())
    good_result = {"result": {"answer": "42"}, "metadata": {}}
    assert interface._validate_structured_response(good_result) == True


def test_validate_structured_response_rejects_invalid_json():
    logger = mock.Mock()
    interface = OpenAIReasoningInterface({}, logger)
    bad_result = "not a dict"
    result = interface._validate_structured_response(bad_result)
    assert result is False
    logger.error.assert_called()
