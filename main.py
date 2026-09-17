import sys
from pathlib import Path

# Add project root to sys.path so imports work both standalone and when run from root
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import booking, heartbeat

# Create all tables in the engine (optional if already created via SQL)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bus Booking Kiosk App API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(booking.router)
app.include_router(heartbeat.router)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "kiosk-app-api"}
