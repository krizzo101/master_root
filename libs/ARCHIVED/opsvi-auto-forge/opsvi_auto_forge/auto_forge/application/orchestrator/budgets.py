"""Budget management for resource allocation and cost tracking."""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from opsvi_auto_forge.infrastructure.memory.graph.client import Neo4jClient
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)


class BudgetType(str, Enum):
    """Types of budgets."""

    TOKENS = "tokens"
    COST = "cost"
    TIME = "time"
    MEMORY = "memory"
    CPU = "cpu"


class BudgetPeriod(str, Enum):
    """Budget periods."""

    PER_TASK = "per_task"
    PER_RUN = "per_run"
    PER_PROJECT = "per_project"
    PER_HOUR = "per_hour"
    PER_DAY = "per_day"
    PER_MONTH = "per_month"


class BudgetLimit(BaseModel):
    """Budget limit configuration."""

    budget_type: BudgetType
    period: BudgetPeriod
    limit: float
    soft_limit: Optional[float] = None
    hard_limit: Optional[float] = None
    unit: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True)

    @field_validator("limit", "soft_limit", "hard_limit")
    @classmethod
    def validate_limits(cls, v: Optional[float]) -> Optional[float]:
        """Validate limit values are positive."""
        if v is not None and v < 0:
            raise ValueError("Budget limits must be positive")
        return v


class BudgetUsage(BaseModel):
    """Current budget usage."""

    budget_type: BudgetType
    period: BudgetPeriod
    used: float = 0.0
    limit: float
    remaining: float
    percentage: float = 0.0
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
        },
    )

    @field_validator("used", "limit", "remaining")
    @classmethod
    def validate_values(cls, v: float) -> float:
        """Validate usage values are non-negative."""
        if v < 0:
            raise ValueError("Budget values must be non-negative")
        return v

    @field_validator("percentage")
    @classmethod
    def validate_percentage(cls, v: float) -> float:
        """Validate percentage is between 0 and 100."""
        if not 0.0 <= v <= 100.0:
            raise ValueError("Percentage must be between 0 and 100")
        return v


class BudgetAlert(BaseModel):
    """Budget alert configuration."""

    budget_type: BudgetType
    threshold: float = Field(..., ge=0.0, le=100.0)
    alert_type: str = "warning"  # warning, critical, exceeded
    message: str
    enabled: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True)


class BudgetManager:
    """Manages budgets and resource allocation."""

    def __init__(self, neo4j_client: Optional[Neo4jClient] = None):
        """Initialize the budget manager."""
        self.neo4j_client = neo4j_client
        self.budgets: Dict[str, BudgetLimit] = {}
        self.usage: Dict[str, BudgetUsage] = {}
        self.alerts: Dict[str, BudgetAlert] = {}
        self._load_default_budgets()

    def _load_default_budgets(self) -> None:
        """Load default budget configurations."""
        default_budgets = [
            BudgetLimit(
                budget_type=BudgetType.TOKENS,
                period=BudgetPeriod.PER_TASK,
                limit=10000,
                soft_limit=8000,
                hard_limit=12000,
                unit="tokens",
            ),
            BudgetLimit(
                budget_type=BudgetType.COST,
                period=BudgetPeriod.PER_TASK,
                limit=1.0,
                soft_limit=0.8,
                hard_limit=1.5,
                unit="USD",
            ),
            BudgetLimit(
                budget_type=BudgetType.TIME,
                period=BudgetPeriod.PER_TASK,
                limit=300,
                soft_limit=240,
                hard_limit=600,
                unit="seconds",
            ),
            BudgetLimit(
                budget_type=BudgetType.TOKENS,
                period=BudgetPeriod.PER_RUN,
                limit=100000,
                soft_limit=80000,
                hard_limit=150000,
                unit="tokens",
            ),
            BudgetLimit(
                budget_type=BudgetType.COST,
                period=BudgetPeriod.PER_RUN,
                limit=10.0,
                soft_limit=8.0,
                hard_limit=15.0,
                unit="USD",
            ),
            BudgetLimit(
                budget_type=BudgetType.TIME,
                period=BudgetPeriod.PER_RUN,
                limit=3600,
                soft_limit=3000,
                hard_limit=7200,
                unit="seconds",
            ),
        ]

        for budget in default_budgets:
            key = f"{budget.budget_type}_{budget.period}"
            self.budgets[key] = budget

        # Set up default alerts
        default_alerts = [
            BudgetAlert(
                budget_type=BudgetType.TOKENS,
                threshold=80.0,
                alert_type="warning",
                message="Token usage approaching limit",
            ),
            BudgetAlert(
                budget_type=BudgetType.TOKENS,
                threshold=95.0,
                alert_type="critical",
                message="Token usage critical",
            ),
            BudgetAlert(
                budget_type=BudgetType.COST,
                threshold=80.0,
                alert_type="warning",
                message="Cost approaching limit",
            ),
            BudgetAlert(
                budget_type=BudgetType.COST,
                threshold=95.0,
                alert_type="critical",
                message="Cost critical",
            ),
        ]

        for alert in default_alerts:
            key = f"{alert.budget_type}_{alert.alert_type}_{alert.threshold}"
            self.alerts[key] = alert

        logger.info(
            f"Loaded {len(default_budgets)} default budgets and {len(default_alerts)} alerts"
        )

    async def get_budget(
        self, budget_type: BudgetType, period: BudgetPeriod
    ) -> Optional[BudgetLimit]:
        """Get budget limit for a specific type and period."""
        key = f"{budget_type}_{period}"
        return self.budgets.get(key)

    async def set_budget(self, budget: BudgetLimit) -> bool:
        """Set a budget limit."""
        try:
            key = f"{budget.budget_type}_{budget.period}"
            self.budgets[key] = budget

            # Persist to Neo4j if available
            if self.neo4j_client:
                await self._persist_budget(budget)

            logger.info(f"Set budget: {key} = {budget.limit} {budget.unit}")
            return True

        except Exception as e:
            logger.error(f"Failed to set budget: {e}")
            return False

    async def get_usage(
        self,
        budget_type: BudgetType,
        period: BudgetPeriod,
        context_id: Optional[str] = None,
    ) -> Optional[BudgetUsage]:
        """Get current usage for a budget."""
        key = f"{budget_type}_{period}"
        if context_id:
            key = f"{key}_{context_id}"

        return self.usage.get(key)

    async def update_usage(
        self,
        budget_type: BudgetType,
        period: BudgetPeriod,
        used: float,
        context_id: Optional[str] = None,
    ) -> bool:
        """Update usage for a budget."""
        try:
            key = f"{budget_type}_{period}"
            if context_id:
                key = f"{key}_{context_id}"

            budget = await self.get_budget(budget_type, period)
            if not budget:
                logger.warning(f"No budget found for {budget_type}_{period}")
                return False

            # Get current usage or create new
            usage = self.usage.get(key)
            if not usage:
                usage = BudgetUsage(
                    budget_type=budget_type,
                    period=period,
                    limit=budget.limit,
                    remaining=budget.limit,
                )

            # Update usage
            usage.used = used
            usage.remaining = max(0.0, budget.limit - used)
            usage.percentage = (
                (used / budget.limit) * 100.0 if budget.limit > 0 else 0.0
            )
            usage.last_updated = datetime.now(timezone.utc)

            self.usage[key] = usage

            # Check for alerts
            await self._check_alerts(usage, context_id)

            # Persist to Neo4j if available
            if self.neo4j_client:
                await self._persist_usage(usage, context_id)

            logger.info(
                f"Updated usage: {key} = {used}/{budget.limit} ({usage.percentage:.1f}%)"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to update usage: {e}")
            return False

    async def can_allocate(
        self,
        budget_type: BudgetType,
        period: BudgetPeriod,
        amount: float,
        context_id: Optional[str] = None,
    ) -> bool:
        """Check if we can allocate resources within budget."""
        try:
            budget = await self.get_budget(budget_type, period)
            if not budget:
                logger.warning(f"No budget found for {budget_type}_{period}")
                return True  # Allow if no budget set

            usage = await self.get_usage(budget_type, period, context_id)
            current_used = usage.used if usage else 0.0

            # Check against hard limit
            if budget.hard_limit and (current_used + amount) > budget.hard_limit:
                logger.warning(
                    f"Hard limit exceeded: {current_used + amount} > {budget.hard_limit}"
                )
                return False

            # Check against soft limit
            if budget.soft_limit and (current_used + amount) > budget.soft_limit:
                logger.warning(
                    f"Soft limit exceeded: {current_used + amount} > {budget.soft_limit}"
                )
                # Still allow but log warning

            return True

        except Exception as e:
            logger.error(f"Failed to check allocation: {e}")
            return False

    async def allocate(
        self,
        budget_type: BudgetType,
        period: BudgetPeriod,
        amount: float,
        context_id: Optional[str] = None,
    ) -> bool:
        """Allocate resources and update usage."""
        try:
            if not await self.can_allocate(budget_type, period, amount, context_id):
                return False

            usage = await self.get_usage(budget_type, period, context_id)
            current_used = usage.used if usage else 0.0

            await self.update_usage(
                budget_type, period, current_used + amount, context_id
            )
            return True

        except Exception as e:
            logger.error(f"Failed to allocate resources: {e}")
            return False

    async def get_budget_summary(
        self, context_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a summary of all budgets and usage."""
        summary = {"budgets": {}, "usage": {}, "alerts": [], "total_usage": {}}

        for budget in self.budgets.values():
            key = f"{budget.budget_type}_{budget.period}"
            summary["budgets"][key] = budget.model_dump()

            usage = await self.get_usage(budget.budget_type, budget.period, context_id)
            if usage:
                summary["usage"][key] = usage.model_dump()

        # Calculate total usage by type
        for budget_type in BudgetType:
            total_used = 0.0
            for usage in self.usage.values():
                if usage.budget_type == budget_type:
                    total_used += usage.used
            summary["total_usage"][budget_type] = total_used

        return summary

    async def add_alert(self, alert: BudgetAlert) -> bool:
        """Add a budget alert."""
        try:
            key = f"{alert.budget_type}_{alert.alert_type}_{alert.threshold}"
            self.alerts[key] = alert

            # Persist to Neo4j if available
            if self.neo4j_client:
                await self._persist_alert(alert)

            logger.info(f"Added alert: {key}")
            return True

        except Exception as e:
            logger.error(f"Failed to add alert: {e}")
            return False

    async def _check_alerts(
        self, usage: BudgetUsage, context_id: Optional[str] = None
    ) -> None:
        """Check if any alerts should be triggered."""
        for alert in self.alerts.values():
            if (
                alert.budget_type == usage.budget_type
                and alert.enabled
                and usage.percentage >= alert.threshold
            ):
                logger.warning(
                    f"Budget alert triggered: {alert.message} "
                    f"({usage.percentage:.1f}% used)"
                )

                # Persist alert to Neo4j if available
                if self.neo4j_client:
                    await self._persist_alert_trigger(alert, usage, context_id)

    async def _persist_budget(self, budget: BudgetLimit) -> None:
        """Persist budget to Neo4j."""
        if not self.neo4j_client:
            return

        query = """
        MERGE (b:BudgetLimit {type: $type, period: $period})
        SET b.limit = $limit,
            b.soft_limit = $soft_limit,
            b.hard_limit = $hard_limit,
            b.unit = $unit,
            b.metadata = $metadata,
            b.updated_at = datetime()
        """

        params = {
            "type": budget.budget_type,
            "period": budget.period,
            "limit": budget.limit,
            "soft_limit": budget.soft_limit,
            "hard_limit": budget.hard_limit,
            "unit": budget.unit,
            "metadata": budget.metadata,
        }

        await self.neo4j_client.execute_query(query, params)

    async def _persist_usage(
        self, usage: BudgetUsage, context_id: Optional[str] = None
    ) -> None:
        """Persist usage to Neo4j."""
        if not self.neo4j_client:
            return

        query = """
        MERGE (u:BudgetUsage {type: $type, period: $period, context_id: $context_id})
        SET u.used = $used,
            u.limit = $limit,
            u.remaining = $remaining,
            u.percentage = $percentage,
            u.metadata = $metadata,
            u.last_updated = datetime()
        """

        params = {
            "type": usage.budget_type,
            "period": usage.period,
            "context_id": context_id or "global",
            "used": usage.used,
            "limit": usage.limit,
            "remaining": usage.remaining,
            "percentage": usage.percentage,
            "metadata": usage.metadata,
        }

        await self.neo4j_client.execute_query(query, params)

    async def _persist_alert(self, alert: BudgetAlert) -> None:
        """Persist alert to Neo4j."""
        if not self.neo4j_client:
            return

        query = """
        MERGE (a:BudgetAlert {type: $type, alert_type: $alert_type, threshold: $threshold})
        SET a.message = $message,
            a.enabled = $enabled,
            a.metadata = $metadata,
            a.updated_at = datetime()
        """

        params = {
            "type": alert.budget_type,
            "alert_type": alert.alert_type,
            "threshold": alert.threshold,
            "message": alert.message,
            "enabled": alert.enabled,
            "metadata": alert.metadata,
        }

        await self.neo4j_client.execute_query(query, params)

    async def _persist_alert_trigger(
        self, alert: BudgetAlert, usage: BudgetUsage, context_id: Optional[str] = None
    ) -> None:
        """Persist alert trigger to Neo4j."""
        if not self.neo4j_client:
            return

        query = """
        CREATE (t:BudgetAlertTrigger {
            type: $type,
            alert_type: $alert_type,
            threshold: $threshold,
            current_percentage: $current_percentage,
            context_id: $context_id,
            triggered_at: datetime()
        })
        """

        params = {
            "type": alert.budget_type,
            "alert_type": alert.alert_type,
            "threshold": alert.threshold,
            "current_percentage": usage.percentage,
            "context_id": context_id or "global",
        }

        await self.neo4j_client.execute_query(query, params)
