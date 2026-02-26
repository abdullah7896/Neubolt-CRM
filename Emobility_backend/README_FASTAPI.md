# Neubolt FastAPI - Quick Start Guide

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements_fastapi.txt
```

2. **Configure environment:**
```bash
# Copy .env.example to .env and update values
copy .env.example .env
```

3. **Update .env file:**
- Set your database credentials
- Change JWT_SECRET_KEY to a secure random string
- Configure MQTT and GPS settings

## Running the Application

### Development Mode (with auto-reload):
```bash
# Run on localhost (recommended for local testing)
uvicorn fastapi_app:app --reload --host 127.0.0.1 --port 8000

# Run on all interfaces (accessible from other devices)
uvicorn fastapi_app:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode:
```bash
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --workers 4
```

## Database Initialization

The database tables will be created automatically on first run. An initial admin user will be created:

- **Username:** admin
- **Password:** admin123
- **⚠️ Change this password after first login!**

## API Documentation

Once running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Default Endpoints

### Authentication
- `POST /neubolt/login` - User login
- `POST /neubolt/logout` - User logout
- `POST /neubolt/refresh` - Refresh access token
- `GET /neubolt/me` - Get current user info

### Users
- `POST /neubolt/users` - Create user (Admin only)
- `GET /neubolt/users` - List users
- `GET /neubolt/users/{cnic}` - Get user
- `PUT /neubolt/users/{cnic}` - Update user
- `DELETE /neubolt/users/{cnic}` - Delete user

### Drivers
- `POST /neubolt/drivers` - Register driver
- `GET /neubolt/drivers` - List drivers
- `GET /neubolt/drivers/{driver_id}` - Get driver
- `PUT /neubolt/drivers/{driver_id}` - Update driver
- `DELETE /neubolt/drivers/{driver_id}` - Delete driver

### Vehicles
- `POST /neubolt/vehicles` - Register vehicle
- `GET /neubolt/vehicles` - List vehicles
- `GET /neubolt/vehicles/{registration_number}` - Get vehicle
- `GET /neubolt/vehicles/{registration_number}/telemetry` - Get telemetry
- `GET /neubolt/vehicles/{registration_number}/location` - Get GPS location

### Other Endpoints
- Stations, Batteries, Swaps, Complaints, Analytics, Files

## Architecture

- **Single Unified Database:** All data in one PostgreSQL database
- **JWT Authentication:** Secure token-based auth with refresh tokens
- **Role-Based Access:** Admin, CRM, Maintenance, Operator roles
- **PII Masking:** Automatic data masking based on user role
- **Real-time Data:**
  - MQTT worker for telemetry (EV and stations)
  - GPS TCP server on port 8000 for location tracking
- **Background Workers:** MQTT and GPS run in separate threads

## Testing

Login example:
```bash
curl -X POST http://localhost:8000/neubolt/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

Use the returned `access_token` for authenticated requests:
```bash
curl http://localhost:8000/neubolt/users \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Troubleshooting

- **Database connection failed:** Check DB credentials in .env
- **MQTT not connecting:** Verify MQTT broker is running
- **GPS not working:** Check port 8000 is not in use

## Migration from Flask

The new FastAPI application (`fastapi_app.py`) coexists with the old Flask version (`api2.py`). Both can run simultaneously on different ports for gradual migration.

**Frontend changes needed:**
- Update API base URL if changed
- Authentication flow remains compatible
- Endpoint paths remain the same (`/neubolt/*`)
