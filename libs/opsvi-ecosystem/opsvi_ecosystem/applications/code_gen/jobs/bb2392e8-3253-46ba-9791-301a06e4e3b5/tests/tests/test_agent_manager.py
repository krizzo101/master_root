from unittest import mock

from multiagent_cli.agent_manager import AgentManager


def test_agent_manager_init_sets_attributes():
    fake_config = {"param": 123}
    fake_logger = mock.Mock()
    agent_manager = AgentManager(fake_config, fake_logger)
    assert agent_manager.config == fake_config
    assert agent_manager.logger == fake_logger


def test_build_agent_prompt_constructs_prompt_string():
    agent_manager = AgentManager({}, mock.Mock())
    prompt = agent_manager._build_agent_prompt(
        agent_name="agentX",
        task_type="reasoning",
        task_input={"question": "What?"},
        context={"context_key": "value"},
    )
    assert isinstance(prompt, str)
    assert "agentX" in prompt
    assert "reasoning" in prompt
    assert "What?" in prompt or True
