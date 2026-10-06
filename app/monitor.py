import httpx
from datetime import datetime
from .database import SessionLocal
from .models import MonitoredEndpoint, PingLog

async def check_endpoint_health(endpoint_id: int, url: str):
    db = SessionLocal()
    start_time = datetime.utcnow()
    is_up = False
    status_code = None
    response_time_ms = None

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        try:
            response = await client.get(url)
            end_time = datetime.utcnow()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            status_code = response.status_code
            # Consider 200-399 range as healthy "UP"
            if 200 <= status_code < 400:
                is_up = True
        except Exception:
            is_up = False
            status_code = None
            response_time_ms = None

    # Save the check results into the database
    db_log = PingLog(
        endpoint_id=endpoint_id,
        status_code=status_code,
        response_time_ms=response_time_ms,
        is_up=is_up
    )
    db.add(db_log)
    db.commit()
    db.close()