from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import time

from .database import engine, Base, get_db
from .models import User, MonitoredEndpoint, PingLog
from .schemas import UserCreate, UserResponse, EndpointCreate, EndpointResponse, PingLogResponse
from .monitor import check_endpoint_health

# Automatically create database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Uptime Monitor SaaS API", version="1.0.0")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Welcome to the Uptime Monitor SaaS API!",
        "docs": "/docs"
    }

# --- 1. User Registration Route ---
@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # In a real production app, hash this password using passlib!
    new_user = User(email=user.email, hashed_password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# --- 2. Create Endpoint to Monitor ---
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

# --- 3. Manually Trigger a Health Check for an Endpoint ---
@app.post("/endpoints/{endpoint_id}/ping", response_model=PingLogResponse)
async def manual_ping(endpoint_id: int, db: Session = Depends(get_db)):
    endpoint = db.query(MonitoredEndpoint).filter(MonitoredEndpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    # Run our async monitoring check immediately
    await check_endpoint_health(endpoint.id, endpoint.url)
    
    # Fetch and return the latest log entry
    latest_log = db.query(PingLog).filter(PingLog.endpoint_id == endpoint_id).order_by(PingLog.timestamp.desc()).first()
    return latest_log

# --- 4. Get Logs for an Endpoint ---
@app.get("/endpoints/{endpoint_id}/logs", response_model=List[PingLogResponse])
def get_endpoint_logs(endpoint_id: int, db: Session = Depends(get_db)):
    logs = db.query(PingLog).filter(PingLog.endpoint_id == endpoint_id).order_by(PingLog.timestamp.desc()).all()
    return logs