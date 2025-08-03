from typing import Any, Callable, Dict


class AgentAPI:
    def __init__(self, intent_bus, event_router, task_market, knowledge_graph):
        self.intent_bus = intent_bus
        self.event_router = event_router
        self.task_market = task_market
        self.knowledge_graph = knowledge_graph

    async def publish_intent(self, intent_type: str, payload: Dict[str, Any]):
        await self.intent_bus.publish(intent_type, payload)

    def subscribe_to_intent(self, intent_type: str, callback: Callable):
        self.intent_bus.subscribe(intent_type, callback)

    async def claim_task(self, agent_id: str):
        return await self.task_market.claim_task(agent_id)

    def update_knowledge(self, fact: Dict[str, Any], provenance: Dict[str, Any] = None):
        self.knowledge_graph.update(fact, provenance)
