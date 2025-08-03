from orchestrator.orchestrator import Orchestrator
from orchestrator.subscription_engine import SubscriptionEngine
from orchestrator.task_market import TaskMarket


def test_orchestrator_init():
    orchestrator = Orchestrator()
    assert hasattr(orchestrator, "agents")


def test_task_market_init():
    market = TaskMarket()
    assert hasattr(market, "tasks")


def test_subscription_engine_init():
    engine = SubscriptionEngine()
    assert hasattr(engine, "subscriptions")
