"""
AgentManager manages agent instances and agent task execution using Langgraph and OpenAI API.
"""
from multiagent_cli.config import AppConfig
from multiagent_cli.openai_interface import OpenAIReasoningInterface


class AgentManager:
    """
    Manages multiple agent types and executes their tasks by invoking the OpenAI reasoning interface.
    """

    def __init__(self, config: AppConfig, logger_inst):
        self.config = config
        self.logger = logger_inst
        self.openai_interface = OpenAIReasoningInterface(config, logger_inst)

    async def run_agent_task(
        self, agent_name: str, task_type: str, task_input: dict, context: dict = None
    ) -> dict:
        """
        Run the agent logic for a task.
        For demo: invoke the OpenAI model with a system prompt describing the agent/task behavior.
        """
        self.logger.info(
            f"[AgentManager] Running agent '{agent_name}' task type '{task_type}'"
        )
        prompt = self._build_agent_prompt(
            agent_name, task_type, task_input, context or {}
        )
        result = await self.openai_interface.reason(prompt, task_input)
        return result

    def _build_agent_prompt(
        self, agent_name: str, task_type: str, task_input: dict, context: dict
    ) -> str:
        """
        Constructs a system prompt for the OpenAI agent.
        """
        system_instr = f"""
You are an autonomous agent named '{agent_name}' in a multi-agent orchestration system.
Your current task type is '{task_type}'.
Work strictly with structured response in JSON format, echo only your output as JSON.
You are provided with the following task input: {task_input}. {f'Context: {context}' if context else ''}
"""
        return system_instr
