from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from contextlib import asynccontextmanager

from .database import engine, Base, get_db
from .models import User, MonitoredEndpoint, PingLog
from .schemas import UserCreate, UserResponse, EndpointCreate, EndpointResponse, PingLogResponse
from .monitor import check_endpoint_health
from .scheduler import start_scheduler, shutdown_scheduler

# Manage startup and shutdown events cleanly in FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables and launch background scheduler
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    # Shutdown: Stop the background worker
    shutdown_scheduler()

app = FastAPI(title="Uptime Monitor SaaS API", version="1.0.0", lifespan=lifespan)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Welcome to the Uptime Monitor SaaS API with Background Worker!",
        "docs": "/docs"
    }

@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(email=user.email, hashed_password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/endpoints/", response_model=EndpointResponse, status_code=status.HTTP_201_CREATED)
def create_endpoint(endpoint: EndpointCreate, user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_endpoint = MonitoredEndpoint(
        name=endpoint.name,
        url=endpoint.url,
        interval_seconds=endpoint.interval_seconds,
        user_id=user_id
    )
    db.add(db_endpoint)
    db.commit()
    db.refresh(db_endpoint)
    return db_endpoint

@app.post("/endpoints/{endpoint_id}/ping", response_model=PingLogResponse)
async def manual_ping(endpoint_id: int, db: Session = Depends(get_db)):
    endpoint = db.query(MonitoredEndpoint).filter(MonitoredEndpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    await check_endpoint_health(endpoint.id, endpoint.url)
    latest_log = db.query(PingLog).filter(PingLog.endpoint_id == endpoint_id).order_by(PingLog.timestamp.desc()).first()
    return latest_log

@app.get("/endpoints/{endpoint_id}/logs", response_model=List[PingLogResponse])
def get_endpoint_logs(endpoint_id: int, db: Session = Depends(get_db)):
    logs = db.query(PingLog).filter(PingLog.endpoint_id == endpoint_id).order_by(PingLog.timestamp.desc()).all()
    return logs