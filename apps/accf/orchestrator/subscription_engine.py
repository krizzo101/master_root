"""
ACCF Subscription Engine

Purpose:
    Provides topic-based subscription and notification for orchestrator events.

References:
    - docs/applications/ACCF/standards/orchestration_requirements.md
    - docs/applications/ACCF/architecture/adr/orchestration_adrs.md
    - .cursor/templates/implementation/orchestration_output_template.yml

Usage:
    from orchestrator.subscription_engine import SubscriptionEngine
    engine = SubscriptionEngine(...)
"""

from typing import Callable, Dict, List


class SubscriptionEngine:
    def __init__(self):
        self.subscriptions: Dict[str, List[Callable]] = {}

    def subscribe(self, topic: str, callback: Callable):
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        self.subscriptions[topic].append(callback)

    def notify(self, topic: str, data):
        if topic in self.subscriptions:
            for callback in self.subscriptions[topic]:
                callback(data)
