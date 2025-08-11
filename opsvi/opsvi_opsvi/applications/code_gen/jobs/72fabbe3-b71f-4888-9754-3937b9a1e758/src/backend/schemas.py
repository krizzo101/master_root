from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from backend.models import MetricType


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    id: int
    username: str


class MetricSampleRead(BaseModel):
    metric_type: MetricType
    value: float
    ts: datetime


class ThresholdRead(BaseModel):
    cpu: float
    memory: float
    disk: float
    network: float


class ThresholdUpdate(BaseModel):
    cpu: Optional[float]
    memory: Optional[float]
    disk: Optional[float]
    network: Optional[float]


class AlertRead(BaseModel):
    metric_type: MetricType
    value: float
    triggered_at: datetime


class MetricsHistoryQuery(BaseModel):
    metric_type: MetricType
    start_ts: datetime
    end_ts: datetime
