from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    endpoints = relationship("MonitoredEndpoint", back_populates="owner")

class MonitoredEndpoint(Base):
    __tablename__ = "endpoints"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    interval_seconds = Column(Integer, default=60)
    is_active = Column(Boolean, default=True)

    owner = relationship("User", back_populates="endpoints")
    logs = relationship("PingLog", back_populates="endpoint")

class PingLog(Base):
    __tablename__ = "ping_logs"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, ForeignKey("endpoints.id"))
    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    is_up = Column(Boolean, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    endpoint = relationship("MonitoredEndpoint", back_populates="logs")