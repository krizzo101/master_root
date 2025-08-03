import os
import sys

# Add 'src/' to sys.path for absolute imports
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
)

from capabilities.collaboration_agent import CollaborationAgent
from capabilities.execution_agent import ExecutionAgent
from capabilities.feedback_agent import FeedbackAgent
from capabilities.knowledge_agent import KnowledgeAgent
from capabilities.memory_agent import MemoryAgent
from capabilities.research_agent import ResearchAgent
from capabilities.security_agent import SecurityAgent
from orchestrator.orchestrator import Orchestrator
from registry.registry import AgentRegistry


def test_end_to_end():
    # Initialize orchestrator and registry
    orchestrator = Orchestrator()
    registry = AgentRegistry()

    # Create agents
    exec_agent = ExecutionAgent()
    collab_agent = CollaborationAgent()
    mem_agent = MemoryAgent()
    research_agent = ResearchAgent()
    knowledge_agent = KnowledgeAgent()
    security_agent = SecurityAgent()
    feedback_agent = FeedbackAgent()

    # Register agents
    registry.register("exec_agent", ["execute"], {"role": "executor"})
    registry.register("collab_agent", ["collaborate"], {"role": "collaborator"})
    registry.register("mem_agent", ["memory"], {"role": "memory"})
    registry.register("research_agent", ["research"], {"role": "researcher"})
    registry.register("knowledge_agent", ["knowledge"], {"role": "knowledge"})
    registry.register("security_agent", ["security"], {"role": "security"})
    registry.register("feedback_agent", ["feedback"], {"role": "feedback"})

    orchestrator.register_agent("exec_agent", exec_agent)
    orchestrator.register_agent("collab_agent", collab_agent)
    orchestrator.register_agent("mem_agent", mem_agent)
    orchestrator.register_agent("research_agent", research_agent)
    orchestrator.register_agent("knowledge_agent", knowledge_agent)
    orchestrator.register_agent("security_agent", security_agent)
    orchestrator.register_agent("feedback_agent", feedback_agent)

    # Test task routing and execution
    task = {"action": "process_data", "data": "sample"}
    result = orchestrator.route_task(task, "exec_agent")
    print("Task Execution Result:", result)
    assert result["status"] == "completed"

    # Test memory agent
    mem_agent.store("foo", "bar")
    assert mem_agent.retrieve("foo") == "bar"
    mem_answer = mem_agent.answer("What is foo?")
    print("Memory Agent Answer:", mem_answer)
    assert "answer" in mem_answer

    # Test research agent
    research_result = research_agent.answer_question("What is the capital of France?")
    print("Research Agent Result:", research_result)
    assert "answer" in research_result

    # Test knowledge agent
    knowledge_result = knowledge_agent.answer("List all facts.")
    print("Knowledge Agent Result:", knowledge_result)
    assert "answer" in knowledge_result

    # Test collaboration agent
    collab_result = collab_agent.collaborate({"content": "Let's work together!"})
    print("Collaboration Result:", collab_result)
    assert collab_result["status"] == "received"

    # Test security agent
    security_agent.log_action("exec_agent", "execute", {"task": task})
    assert security_agent.check_permission("exec_agent", "execute") is True

    # Test feedback agent
    feedback_agent.log_action("exec_agent", "execute", "success")
    feedback_analysis = feedback_agent.analyze()
    print("Feedback Analysis:", feedback_analysis)
    assert isinstance(feedback_analysis, list)

    # Test registry lookup and listing
    agent_info = registry.lookup("exec_agent")
    print("Registry Lookup:", agent_info)
    assert agent_info["capabilities"] == ["execute"]
    all_agents = registry.list_agents()
    print("All Registered Agents:", all_agents)
    assert "exec_agent" in all_agents
