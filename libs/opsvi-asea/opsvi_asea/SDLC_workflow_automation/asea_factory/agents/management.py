from typing import List, Dict, Any
from asea_factory.config.config_loader import ConfigLoader
from asea_factory.agents.base_agent import BaseAgent


class ManagementAgent(BaseAgent):
    def __init__(self, config: ConfigLoader):
        super().__init__("Management", config, debug=True)

    def orchestrate(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        self.logger.info("Orchestrating all agent workflows.")
        # In production, this would manage parallel execution, error handling, etc.
        results = []
        for task in tasks:
            agent = task["agent"]
            args = task.get("args", {})
            results.append(agent.run(**args))
        return {"tasks": tasks, "results": results}

    def run(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self.orchestrate(tasks)
