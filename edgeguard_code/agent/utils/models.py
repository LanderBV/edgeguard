from typing import Optional

from pydantic import BaseModel, Field, validator


class Containers(BaseModel):
    name: str
    cpu: float # = Field(..., ge=0.0, le=100.0)
    memory: float # = Field(..., ge=0.0, le=100.0)

    @validator('cpu','memory')
    def check_value_range(cls, v):
        if v < 0:
            v = 0.0
        elif v > 100:
            v= 100.0
        return v

class Data(BaseModel):
    cpu: float # = Field(..., ge=0.0, le=100.0)
    memory: float  # = Field(..., ge=0.0, le=100.0)
    battery_percent: float  # = Field(..., ge=0.0, le=100.0)
    disk_usage:float  # = Field(..., ge=0.0, le=100.0)
    temperature:float
    containers: Optional[list[Containers]]

    @validator('cpu','memory', 'battery_percent', 'disk_usage')
    def check_value_range(cls, v):
        if v < 0:
            v = 0.0
        elif v > 100:
            v= 100.0
        return v

class Metrics(BaseModel):
    timestamp: float
    data: Data

class Drift(BaseModel):
    cpu: bool
    memory: bool
    battery: bool
    disk_usage: bool

class Message(BaseModel):
    current: Data
    future: Data
    drift: Drift
