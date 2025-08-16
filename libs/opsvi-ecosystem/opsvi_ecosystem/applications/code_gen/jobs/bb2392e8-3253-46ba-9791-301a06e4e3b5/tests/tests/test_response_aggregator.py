from multiagent_cli.response_aggregator import AgentResultModel, aggregate_responses


def test_aggregate_responses_returns_aggregated_structure():
    agent_outputs = [
        AgentResultModel(agent_name="agent1", output={"value": 123}),
        AgentResultModel(agent_name="agent2", output={"value": 456}),
    ]
    aggregated = aggregate_responses(agent_outputs)
    assert isinstance(aggregated, dict)
    assert "agent1" in aggregated and "agent2" in aggregated
