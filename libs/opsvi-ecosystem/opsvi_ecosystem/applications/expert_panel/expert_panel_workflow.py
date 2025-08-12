from applications.expert_panel.agents import (
    EthicsExpert,
    ExpertAssignerAgent,
    MLExpert,
    ResearcherAgent,
    StatsExpert,
    SystemMessageGeneratorAgent,
)

from src.shared.logging.shared_logger import SharedLogger
from src.shared.mcp.mcp_server_template import BaseTool, MCPServerTemplate

logger = SharedLogger()


class MLExpertTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="ml_expert",
            description="Machine Learning domain expert agent.",
            input_schema={
                "type": "object",
                "properties": {"question": {"type": "string"}},
            },
        )

    async def execute(self, arguments):
        return [
            {"type": "text", "text": MLExpert().propose_answer(arguments["question"])}
        ]


class StatsExpertTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="stats_expert",
            description="Statistics domain expert agent.",
            input_schema={
                "type": "object",
                "properties": {"question": {"type": "string"}},
            },
        )

    async def execute(self, arguments):
        return [
            {
                "type": "text",
                "text": StatsExpert().propose_answer(arguments["question"]),
            }
        ]


class EthicsExpertTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="ethics_expert",
            description="Ethics domain expert agent.",
            input_schema={
                "type": "object",
                "properties": {"question": {"type": "string"}},
            },
        )

    async def execute(self, arguments):
        return [
            {
                "type": "text",
                "text": EthicsExpert().propose_answer(arguments["question"]),
            }
        ]


class ResearcherTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="researcher",
            description="Researcher agent for fact-checking, accuracy, and dispute resolution.",
            input_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
            },
        )

    async def execute(self, arguments):
        return [
            {
                "type": "text",
                "text": ResearcherAgent().perform_research(arguments["query"]),
            }
        ]


class ExpertPanelMCPServer(MCPServerTemplate):
    def __init__(self):
        super().__init__(name="ExpertPanelMCPServer")
        self.logger = logger
        self.expert_assigner = ExpertAssignerAgent()
        self.profile_gen = SystemMessageGeneratorAgent()
        self.register_tool(MLExpertTool())
        self.register_tool(StatsExpertTool())
        self.register_tool(EthicsExpertTool())
        self.register_tool(ResearcherTool())

    # Optionally, add a run_panel method for local CLI testing
    async def run_panel(
        self,
        question: str,
        num_experts: int = 3,
        roles: list = None,
        num_rounds: int = 5,
    ):
        expert_roster = self.expert_assigner.assign_experts(question)
        experts = []
        for e in expert_roster:
            if e["expert_type"] == "MLExpert":
                experts.append(MLExpert(e["system_message"]))
            elif e["expert_type"] == "StatsExpert":
                experts.append(StatsExpert(e["system_message"]))
            elif e["expert_type"] == "EthicsExpert":
                experts.append(EthicsExpert(e["system_message"]))
            elif e["expert_type"] == "Researcher":
                experts.append(ResearcherAgent(e["system_message"]))
        transcript = []
        answers = {e.name: e.propose_answer(question) for e in experts}
        transcript.append({"round": 1, "answers": answers.copy()})
        round_num = 2
        while round_num <= num_rounds:
            critiques = {e.name: e.critique_answers(answers) for e in experts}
            transcript.append({"round": round_num, "critiques": critiques.copy()})
            for e in experts:
                answers[e.name] = e.revise_answer(
                    answers[e.name], critiques.get(e.name, {})
                )
            transcript.append({"round": round_num, "answers": answers.copy()})
            if len(set(answers.values())) != 1:
                researcher = next((e for e in experts if e.name == "Researcher"), None)
                if researcher:
                    research_query = f"Fact-check and resolve dispute for: {question} and current answers: {answers}"
                    research_summary = await researcher.perform_research(research_query)
                    transcript.append(
                        {"round": round_num, "research": research_summary}
                    )
            else:
                break
            round_num += 1
        consensus = (
            answers[list(answers.keys())[0]]
            if len(set(answers.values())) == 1
            else "[No consensus reached]"
        )
        return {
            "consensus": consensus,
            "answers": answers,
            "transcript": transcript,
        }


if __name__ == "__main__":
    import asyncio
    import sys

    question = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "What are the open problems in AGI safety?"
    )
    server = ExpertPanelMCPServer()
    # For MCP server mode:
    # asyncio.run(server.run())
    # For CLI test mode (demo):
    result = asyncio.run(server.run_panel(question))
    print("\n=== Expert Panel Demo Result ===\n")
    print(result)
