from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from contextlib import asynccontextmanager

from .database import engine, Base, get_db
from .models import User, MonitoredEndpoint, PingLog
from .schemas import UserCreate, UserResponse, EndpointCreate, EndpointResponse, PingLogResponse, Token
from .monitor import check_endpoint_health
from .scheduler import start_scheduler, shutdown_scheduler
from .auth import get_password_hash, verify_password, create_access_token, get_current_user

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
        "message": "Welcome to the Uptime Monitor SaaS API with Background Worker & JWT Auth!",
        "docs": "/docs"
    }

@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash the password before storing it in the database
    hashed_pass = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_pass)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/endpoints/", response_model=EndpointResponse, status_code=status.HTTP_201_CREATED)
def create_endpoint(endpoint: EndpointCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Automatically tie the endpoint to the authenticated user via JWT token
    db_endpoint = MonitoredEndpoint(
        name=endpoint.name,
        url=endpoint.url,
        interval_seconds=endpoint.interval_seconds,
        user_id=current_user.id
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