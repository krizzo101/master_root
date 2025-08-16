from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class MetricType(str, Enum):
    cpu = "cpu"
    memory = "memory"
    disk = "disk"
    network = "network"


class MetricSample(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    metric_type: MetricType
    value: float
    ts: datetime = Field(index=True)


class Threshold(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    cpu: float = 90.0  # %
    memory: float = 90.0  # %
    disk: float = 90.0  # %
    network: float = 50000000.0  # Bytes/s (threshold for alerts, can be changed)


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str


class AlertEvent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    metric_type: MetricType
    value: float
    triggered_at: datetime
    resolved_at: datetime | None = None
    resolved_value: float | None = None
