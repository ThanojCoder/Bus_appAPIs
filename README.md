# 🚌 Bus Booking Kiosk App APIs

A high-performance, standalone backend service built with **FastAPI** powering physical bus ticketing kiosks and self-service passenger terminals.

---

## 🚀 Features

- **🗺️ Destination Discovery**: Fetches active routes available from the terminal's specific origin city/station with scheduled trips for the day.
- **🕒 Real-Time Trip & Seat Availability**: Live schedule lookup displaying departure times, bus types, seat counts, and real-time open seats.
- **🔒 Seat Hold Engine**: Locks chosen seats for a temporary window (e.g., 10 minutes) during customer checkout to prevent double-booking.
- **💳 Cashfree Payment Gateway Integration**:
  - Dynamically creates PG payment sessions.
  - Generates instant on-screen **UPI QR codes** for contactless kiosk payments.
  - Queries real-time transaction status directly from Cashfree with automatic database settlement.
- **🖨️ Thermal Ticket Print Payload**: Formats completed reservations into printable ticket data (order number, route, departure time, assigned seats, payment mode).
- **💓 Terminal Heartbeat & Health Monitoring**: Periodic telemetry from kiosk terminals reporting operational status (`active`, `inactive`, `maintenance`) and timestamp.

---

## 🛠️ Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Server**: [Uvicorn](https://www.uvicorn.org/) (ASGI)
- **Database ORM**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
- **Database**: PostgreSQL
- **Payments**: [Cashfree Payment Gateway](https://www.cashfree.com/) (REST APIs & UPI QR)
- **Data Validation**: [Pydantic v2](https://docs.pydantic.dev/)

---

## 📁 Project Structure

```
appAPIs/
├── .env.example          # Template for environment configuration
├── .gitignore            # Git ignore file for Python, secrets, and caches
├── requirements.txt      # Python dependencies
├── README.md             # Documentation and setup guide
├── main.py               # FastAPI application entrypoint
├── database.py           # Database connection, engine, and session dependency
├── models.py             # SQLAlchemy ORM models (Routes, Buses, Trips, Orders, etc.)
├── schemas.py            # Pydantic request/response validation schemas
├── cashfree.py           # Cashfree payment gateway integration service
└── routers/              # API endpoints organized by domain
    ├── __init__.py
    ├── booking.py        # Destinations, trips, seat holds, payments, ticket print
    └── heartbeat.py      # Kiosk terminal status heartbeat
```

---

## ⚙️ Getting Started

### Prerequisites

- **Python**: 3.10+
- **PostgreSQL**: Running instance with the shared bus booking database
- **Cashfree Account**: Sandbox or Production client credentials

### 1. Clone & Navigate to Project

```bash
cd appAPIs
```

### 2. Set Up Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create your `.env` configuration file from the template:

```bash
# Windows PowerShell
cp .env.example .env

# Linux / macOS
cp .env.example .env
```

Edit `.env`:

```ini
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=busBooking_db
DB_USER=postgres
DB_PASSWORD=your_password_here

# Cashfree Payments
CASHFREE_URL=https://sandbox.cashfree.com/pg
CASHFREE_CLIENT_ID=your_cashfree_client_id_here
CASHFREE_CLIENT_SECRET=your_cashfree_client_secret_here
CASHFREE_API_VERSION=2023-08-01
```

### 5. Run the Server

```bash
# Running on port 8001 (recommended when running alongside adminAPIs on 8000):
uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Or on default port 8000:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The service will be accessible at `http://127.0.0.1:8001` (or `http://127.0.0.1:8000`).

---

## 📖 Interactive API Documentation

Once the server is running, explore and test the endpoints interactively:

- **Swagger UI**: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
- **ReDoc UI**: [http://127.0.0.1:8001/redoc](http://127.0.0.1:8001/redoc)

---

## 📡 API Endpoints Overview

All kiosk requests require the `X-Kiosk-Id` HTTP header to identify the calling terminal device.

| Method | Endpoint | Description | Required Header |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/app/destinations` | Available routes originating from this kiosk's station | `X-Kiosk-Id: <int>` |
| `GET` | `/api/app/routes/{route_id}/trips` | Scheduled trips with available seats for selected route | `X-Kiosk-Id: <int>` |
| `POST` | `/api/app/trips/{trip_id}/hold` | Reserve/hold specified number of seats | `X-Kiosk-Id: <int>` |
| `POST` | `/api/app/payments/order` | Initialize Cashfree order & return UPI QR string | `X-Kiosk-Id: <int>` |
| `GET` | `/api/app/orders/{order_number}/status` | Verify payment status from Cashfree and confirm booking | `X-Kiosk-Id: <int>` |
| `GET` | `/api/app/orders/{id}/print` | Retrieve printable thermal ticket receipt payload | ❌ |
| `POST` | `/api/app/heartbeat?kiosk_id={id}` | Post periodic heartbeat status (`active`/`maintenance`) | ❌ |
| `GET` | `/health` | Service health check | ❌ |

---

## 📤 Pushing to GitHub

To push this service to its own GitHub repository:

```bash
cd appAPIs
git init
git add .
git commit -m "feat: Initial commit for Bus Booking Kiosk App APIs"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git push -u origin main
```
