from datetime import date, datetime, time
from typing import List, Optional
from pydantic import BaseModel, EmailStr, model_validator
from models import (
    AdminRole,
    BookingStatusEnum,
    BusTypeEnum,
    HoldStatus,
    KioskStatus,
    PaymentModeEnum,
    PaymentStatusEnum,
    TripStatus,
)


# --- Routes ---
class RouteBase(BaseModel):
    route_code: str
    source: str
    destination: str
    base_fare: float


class AssignedBusItem(BaseModel):
    assignment_id: int
    bus_id: int
    bus_number: str
    bus_type: str
    total_seats: int
    departure_time: str
    is_active: bool = True
    trip_id: Optional[int] = None


class AssignedKioskItem(BaseModel):
    kiosk_id: int
    kiosk_code: str
    terminal_name: str
    source: str
    location_name: str
    status: str


class RouteResponse(RouteBase):
    id: int
    is_active: bool
    created_at: datetime
    assigned_buses: Optional[List[AssignedBusItem]] = []
    assigned_kiosks: Optional[List[AssignedKioskItem]] = []

    class Config:
        from_attributes = True


# --- Trips ---
class TripResponse(BaseModel):
    id: int
    route_id: int
    bus_id: int
    travel_date: date
    departure_time: time
    trip_duration: Optional[str] = None
    bus_type: Optional[BusTypeEnum] = None
    total_seats: int
    booked_seats: int
    held_seats: int
    status: TripStatus

    class Config:
        from_attributes = True


class TripAppResponse(TripResponse):
    available_seats: int


# --- Holds ---
class HoldCreate(BaseModel):
    trip_id: int
    seats: int


class HoldResponse(BaseModel):
    id: int
    trip_id: int
    kiosk_id: int
    seats_held: int
    seat_numbers: str
    status: HoldStatus
    expires_at: datetime

    class Config:
        from_attributes = True


# --- Payments & Orders ---
class PaymentRequest(BaseModel):
    hold_id: int
    payment_mode: PaymentModeEnum


class OrderResponse(BaseModel):
    id: int
    order_number: str
    trip_id: int
    hold_id: int
    kiosk_id: int
    total_seats: int
    seat_numbers: str
    total_amount: float
    payment_status: PaymentStatusEnum
    payment_mode: PaymentModeEnum
    booking_status: BookingStatusEnum
    created_at: datetime
    payment_session_id: Optional[str] = None
    qr_string: Optional[str] = None
    route_code: Optional[str] = None
    route_name: Optional[str] = None
    bus_number: Optional[str] = None
    travel_date: Optional[date] = None

    class Config:
        from_attributes = True


class TicketPrintResponse(BaseModel):
    order_number: str
    route_code: str
    source: str
    destination: str
    bus_number: str
    travel_date: date
    departure_time: time
    seat_numbers: str
    total_amount: float
    payment_mode: PaymentModeEnum


# --- Heartbeat ---
class HeartbeatRequest(BaseModel):
    status: KioskStatus
