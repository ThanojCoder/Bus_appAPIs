from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from database import get_db
from models import Route, Trip, SeatHold, Order, Kiosk
from schemas import RouteResponse, TripAppResponse, HoldCreate, HoldResponse, PaymentRequest, OrderResponse, TicketPrintResponse
from datetime import date, datetime, timedelta, timezone
import random

router = APIRouter(prefix="/api/app", tags=["booking"])

def get_kiosk(x_kiosk_id: int = Header(...), db: Session = Depends(get_db)):
    kiosk = db.query(Kiosk).filter(Kiosk.id == x_kiosk_id).first()
    if not kiosk:
        raise HTTPException(status_code=404, detail="Kiosk not found")
    return kiosk

@router.get("/destinations", response_model=List[RouteResponse])
def get_destinations(db: Session = Depends(get_db), current_kiosk: Kiosk = Depends(get_kiosk)):
    # Routes sellable from this kiosk's source with at least one trip still available today
    today = date.today()
    routes = db.query(Route).join(Trip).filter(
        Route.source == current_kiosk.source,
        Trip.travel_date == today,
        Trip.status != 'cancelled',
        (Trip.total_seats - Trip.booked_seats - Trip.held_seats) > 0
    ).distinct().all()
    
    return routes

@router.get("/trips", response_model=List[TripAppResponse])
def get_trips(route_id: int, db: Session = Depends(get_db), current_kiosk: Kiosk = Depends(get_kiosk)):
    today = date.today()
    trips = db.query(Trip).filter(
        Trip.route_id == route_id,
        Trip.travel_date == today,
        Trip.status != 'cancelled',
        (Trip.total_seats - Trip.booked_seats - Trip.held_seats) > 0
    ).order_by(Trip.departure_time.asc()).all()
    
    result = []
    for t in trips:
        t_dict = t.__dict__.copy()
        t_dict['available_seats'] = t.total_seats - t.booked_seats - t.held_seats
        t_dict['bus_type'] = t.bus.bus_type if t.bus else None
        result.append(t_dict)
        
    return result

@router.post("/holds", response_model=HoldResponse)
def create_hold(hold_req: HoldCreate, db: Session = Depends(get_db), current_kiosk: Kiosk = Depends(get_kiosk)):
    # Lock the trip row
    trip = db.query(Trip).with_for_update().filter(Trip.id == hold_req.trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    available_seats = trip.total_seats - trip.booked_seats - trip.held_seats
    if available_seats < hold_req.seats:
        db.rollback()
        raise HTTPException(status_code=400, detail="Not enough seats available")
        
    # Assign dummy seat numbers for now
    start_seat = trip.booked_seats + trip.held_seats + 1
    seat_numbers = ",".join([str(start_seat + i) for i in range(hold_req.seats)])
    
    trip.held_seats += hold_req.seats
    
    hold = SeatHold(
        trip_id=trip.id,
        kiosk_id=current_kiosk.id,
        seats_held=hold_req.seats,
        seat_numbers=seat_numbers,
        status="active",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=4)
    )
    db.add(hold)
    db.commit()
    db.refresh(hold)
    return hold

@router.post("/payments", response_model=OrderResponse)
def process_payment(payment_req: PaymentRequest, db: Session = Depends(get_db), current_kiosk: Kiosk = Depends(get_kiosk)):
    hold = db.query(SeatHold).with_for_update().filter(SeatHold.id == payment_req.hold_id).first()
    if not hold:
        raise HTTPException(status_code=404, detail="Hold not found")
        
    if hold.status != "active":
        db.rollback()
        raise HTTPException(status_code=400, detail="Hold is no longer active")
        
    if datetime.now(timezone.utc) > hold.expires_at:
        hold.status = "expired"
        trip = db.query(Trip).filter(Trip.id == hold.trip_id).first()
        trip.held_seats -= hold.seats_held
        db.commit()
        raise HTTPException(status_code=400, detail="Hold has expired")
        
    # Simulate payment success
    trip = db.query(Trip).filter(Trip.id == hold.trip_id).first()
    route = db.query(Route).filter(Route.id == trip.route_id).first()
    
    total_amount = float(route.base_fare) * hold.seats_held
    
    trip.held_seats -= hold.seats_held
    trip.booked_seats += hold.seats_held
    hold.status = "converted"
    
    order_number = f"ORD-{date.today().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    
    order = Order(
        order_number=order_number,
        trip_id=trip.id,
        hold_id=hold.id,
        kiosk_id=current_kiosk.id,
        total_seats=hold.seats_held,
        seat_numbers=hold.seat_numbers,
        total_amount=total_amount,
        payment_status="paid",
        payment_mode=payment_req.payment_mode,
        booking_status="confirmed"
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    from cashfree import create_cashfree_order, get_upi_qr
    payment_session_id = create_cashfree_order(order.order_number, float(order.total_amount))
    
    qr_string = None
    if payment_session_id and payment_req.payment_mode == "upi":
        qr_string = get_upi_qr(payment_session_id)
    
    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        trip_id=order.trip_id,
        hold_id=order.hold_id,
        kiosk_id=order.kiosk_id,
        total_seats=order.total_seats,
        seat_numbers=order.seat_numbers,
        total_amount=order.total_amount,
        payment_status=order.payment_status,
        payment_mode=order.payment_mode,
        booking_status=order.booking_status,
        created_at=order.created_at,
        payment_session_id=payment_session_id,
        qr_string=qr_string
    )

@router.get("/orders/{order_number}/status")
def get_order_status(order_number: str, db: Session = Depends(get_db), current_kiosk: Kiosk = Depends(get_kiosk)):
    order = db.query(Order).filter(Order.order_number == order_number, Order.kiosk_id == current_kiosk.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    from cashfree import get_cashfree_order
    cf_data = get_cashfree_order(order_number)
    
    if cf_data:
        order_status = cf_data.get("order_status")
        # Update local DB if paid
        if order_status == "PAID" and order.payment_status != "paid":
            order.payment_status = "paid"
            order.booking_status = "confirmed"
            db.commit()
            
        return {
            "order_number": order_number,
            "cashfree_status": order_status,
            "local_payment_status": order.payment_status,
            "local_booking_status": order.booking_status,
            "raw_cashfree_data": cf_data
        }
    else:
        return {
            "order_number": order_number,
            "local_payment_status": order.payment_status,
            "local_booking_status": order.booking_status,
        }

@router.get("/orders/{id}/print", response_model=TicketPrintResponse)
def print_ticket(id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    trip = db.query(Trip).filter(Trip.id == order.trip_id).first()
    route = db.query(Route).filter(Route.id == trip.route_id).first()
    
    # Needs a join for bus, but skipping for simplicity, just fetching directly
    from models import Bus
    bus = db.query(Bus).filter(Bus.id == trip.bus_id).first()
    
    return {
        "order_number": order.order_number,
        "route_code": route.route_code,
        "source": route.source,
        "destination": route.destination,
        "bus_number": bus.bus_number,
        "travel_date": trip.travel_date,
        "departure_time": trip.departure_time,
        "seat_numbers": order.seat_numbers,
        "total_amount": order.total_amount,
        "payment_mode": order.payment_mode
    }
