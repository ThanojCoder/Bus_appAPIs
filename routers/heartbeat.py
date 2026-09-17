from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Kiosk
from schemas import HeartbeatRequest
from datetime import datetime

router = APIRouter(prefix="/api/app/heartbeat", tags=["kiosk-heartbeat"])

@router.post("")
def send_heartbeat(kiosk_id: int, heartbeat: HeartbeatRequest, db: Session = Depends(get_db)):
    # Note: Kiosk app authenticate as a device. We could use simple auth like sending kiosk_id in headers, 
    # but for simplicity, we pass it as a query param or in headers. Let's assume it's in a header or query.
    kiosk = db.query(Kiosk).filter(Kiosk.id == kiosk_id).first()
    if not kiosk:
        raise HTTPException(status_code=404, detail="Kiosk not found")
        
    kiosk.status = heartbeat.status
    kiosk.last_heartbeat_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Heartbeat received"}
