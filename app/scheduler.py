from apscheduler.schedulers.asyncio import AsyncIOScheduler
from .database import SessionLocal
from .models import MonitoredEndpoint
from .monitor import check_endpoint_health

scheduler = AsyncIOScheduler()

async def scheduled_health_checks():
    db = SessionLocal()
    try:
        # Fetch all active endpoints from the database
        active_endpoints = db.query(MonitoredEndpoint).filter(MonitoredEndpoint.is_active == True).all()
        for endpoint in active_endpoints:
            # Run the health check asynchronously for each target
            await check_endpoint_health(endpoint.id, endpoint.url)
    finally:
        db.close()

def start_scheduler():
    # Schedule the health checks to run every 60 seconds
    scheduler.add_job(scheduled_health_checks, "interval", seconds=60, id="health_check_job", replace_existing=True)
    scheduler.start()

def shutdown_scheduler():
    scheduler.shutdown()