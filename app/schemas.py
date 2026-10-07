from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional


# --- User Schemas ---
class UserCreate(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True


# --- Endpoint Schemas ---
class EndpointCreate(BaseModel):
    name: str
    url: str
    interval_seconds: Optional[int] = 60


class EndpointResponse(BaseModel):
    id: int
    name: str
    url: str
    interval_seconds: int
    is_active: bool
    user_id: int

    class Config:
        from_attributes = True


# --- Ping Log Schemas ---
class PingLogResponse(BaseModel):
    id: int
    endpoint_id: int
    status_code: Optional[int]
    response_time_ms: Optional[int]
    is_up: bool
    timestamp: datetime

    class Config:
        from_attributes = True

    # --- JWT Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
