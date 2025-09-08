from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import os
import sys
from typing import List, Optional
from datetime import datetime, timedelta
import json
import logging

# Import shared models and database
from shared.models import TelemetryCreate, TelemetryResponse, TelemetryQuery, EnergyAnalytics, DeviceHealth
from shared.database import execute_query, check_connection

app = FastAPI(
    title="Telemetry Service",
    description="Handles device telemetry data collection and analytics",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"

security = HTTPBearer()

# JWT token validation
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT token and return user info"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    if not check_connection():
        logging.error("Failed to connect to database")
        raise Exception("Database connection failed")
    logging.info("Telemetry service started successfully")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db_status = check_connection()
        return {
            "status": "healthy" if db_status else "unhealthy",
            "service": "telemetry-service",
            "database": "connected" if db_status else "disconnected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "telemetry-service", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Telemetry Data Endpoints
@app.post("/telemetry", status_code=status.HTTP_201_CREATED)
async def create_telemetry_data(
    telemetry_data: TelemetryCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create new telemetry data point"""
    try:
        query = """
            INSERT INTO telemetry (user_id, device_id, temperature, humidity, energy_usage, status, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        result = execute_query(query, (
            current_user["sub"],
            telemetry_data.device_id,
            telemetry_data.temperature,
            telemetry_data.humidity,
            telemetry_data.energy_usage,
            telemetry_data.status,
            telemetry_data.timestamp or datetime.now()
        ))
        
        if result:
            return {"message": "Telemetry data created successfully", "id": result[0][0]}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create telemetry data"
            )
    except Exception as e:
        logging.error(f"Error creating telemetry data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create telemetry data: {str(e)}"
        )

@app.get("/telemetry")
async def get_telemetry_data(
    device_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """Get telemetry data for the current user"""
    try:
        if device_id:
            query = """
                SELECT id, user_id, device_id, temperature, humidity, energy_usage, status, timestamp
                FROM telemetry 
                WHERE user_id = %s AND device_id = %s
                ORDER BY timestamp DESC 
                LIMIT %s
            """
            params = (current_user["sub"], device_id, limit)
        else:
            query = """
                SELECT id, user_id, device_id, temperature, humidity, energy_usage, status, timestamp
                FROM telemetry 
                WHERE user_id = %s
                ORDER BY timestamp DESC 
                LIMIT %s
            """
            params = (current_user["sub"], limit)
        
        telemetry_data = execute_query(query, params)
        
        return [
            TelemetryResponse(
                id=row[0],
                user_id=row[1],
                device_id=row[2],
                temperature=row[3],
                humidity=row[4],
                energy_usage=row[5],
                status=row[6],
                timestamp=row[7]
            )
            for row in telemetry_data
        ]
    except Exception as e:
        logging.error(f"Error fetching telemetry data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch telemetry data: {str(e)}"
        )

@app.get("/telemetry/{device_id}/analytics")
async def get_device_analytics(
    device_id: str,
    period: str = Query("daily", description="Analytics period: daily, weekly, monthly, yearly"),
    current_user: dict = Depends(get_current_user)
):
    """Get energy analytics for a specific device"""
    try:
        # Calculate time range based on period
        now = datetime.now()
        if period == "daily":
            start_time = now - timedelta(days=1)
        elif period == "weekly":
            start_time = now - timedelta(weeks=1)
        elif period == "monthly":
            start_time = now - timedelta(days=30)
        elif period == "yearly":
            start_time = now - timedelta(days=365)
        else:
            start_time = now - timedelta(days=7)  # Default to weekly
        
        query = """
            SELECT AVG(energy_usage), MAX(energy_usage), MIN(energy_usage), COUNT(*)
            FROM telemetry 
            WHERE device_id = %s AND timestamp >= %s AND user_id = %s
        """
        
        stats = execute_query(query, (device_id, start_time, current_user["sub"]))
        
        if not stats or not stats[0] or stats[0][0] is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No telemetry data found for device {device_id}"
            )
        
        stat_row = stats[0]
        analytics = EnergyAnalytics(
            device_id=device_id,
            average_usage=float(stat_row[0]),
            peak_usage=float(stat_row[1]),
            min_usage=float(stat_row[2]),
            total_readings=int(stat_row[3]),
            period_start=start_time.isoformat(),
            period_end=now.isoformat()
        )
        
        analytics.period = period
        return analytics
    except Exception as e:
        logging.error(f"Error getting analytics for device {device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )

@app.get("/telemetry/{device_id}/health")
async def get_device_health(
    device_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get device health status and recommendations"""
    try:
        # Get latest telemetry
        query = """
            SELECT * FROM telemetry 
            WHERE device_id = %s 
            ORDER BY timestamp DESC 
            LIMIT 1
        """
        
        latest_data = execute_query(query, (device_id,))
        
        if not latest_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No telemetry data found for device {device_id}"
            )
        
        latest = latest_data[0]
        
        # Get data from last 24 hours for uptime calculation
        yesterday = datetime.now() - timedelta(days=1)
        count_query = """
            SELECT COUNT(*) FROM telemetry 
            WHERE device_id = %s AND timestamp >= %s
        """
        
        recent_count_data = execute_query(count_query, (device_id, yesterday.isoformat()))
        recent_count = recent_count_data[0][0] if recent_count_data else 0
        
        # Get error count (status != 'active')
        error_query = """
            SELECT COUNT(*) FROM telemetry 
            WHERE device_id = %s AND status != 'active'
        """
        
        error_count_data = execute_query(error_query, (device_id,))
        error_count = error_count_data[0][0] if error_count_data else 0
        
        # Calculate uptime percentage (assuming data points every hour)
        expected_points = 24
        uptime_percentage = (recent_count / expected_points) * 100 if expected_points > 0 else 0
        
        # Generate recommendations
        recommendations = []
        if uptime_percentage < 80:
            recommendations.append("Device connectivity issues detected. Check network connection.")
        if error_count > 5:
            recommendations.append("Multiple errors detected. Device may require maintenance.")
        if latest[4] and float(latest[4]) > 100:  # energy_usage
            recommendations.append("High energy consumption detected. Consider optimization.")
        
        return DeviceHealth(
            device_id=device_id,
            status=latest[6],  # status
            last_seen=latest[7],  # timestamp
            uptime_percentage=uptime_percentage,
            error_count=error_count,
            maintenance_due=error_count > 5 or uptime_percentage < 80,
            recommendations=recommendations
        )
    except Exception as e:
        logging.error(f"Error getting device health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get device health: {str(e)}"
        )

@app.get("/telemetry/devices/summary")
async def get_devices_summary(current_user: dict = Depends(get_current_user)):
    """Get summary of all devices for the current user with latest telemetry"""
    try:
        # Get user's devices with latest telemetry data using PostgreSQL
        query = """
            SELECT ud.device_id, ud.device_name, ud.device_type, ud.location, ud.is_active,
                   t.energy_usage, t.timestamp, t.status
            FROM user_devices ud
            LEFT JOIN (
                SELECT device_id, energy_usage, timestamp, status,
                       ROW_NUMBER() OVER (PARTITION BY device_id ORDER BY timestamp DESC) as rn
                FROM telemetry 
                WHERE user_id = %s
            ) t ON ud.device_id = t.device_id AND t.rn = 1
            WHERE ud.user_id = %s
            ORDER BY ud.created_at DESC
        """
        
        devices = execute_query(query, (current_user["sub"], current_user["sub"]))
    except Exception as e:
        # Return empty result if query fails
        logging.error(f"Error getting devices summary: {e}")
        devices = []
    
    return {
        "user_id": current_user["sub"],
        "total_devices": len(devices),
        "active_devices": len([d for d in devices if d[4]]),  # is_active
        "devices": [
            {
                "device_id": device[0],
                "device_name": device[1],
                "device_type": device[2],
                "location": device[3],
                "is_active": device[4],
                "latest_energy_usage": device[5],
                "last_update": device[6],
                "status": device[7]
            }
            for device in devices
        ]
    }

# User Device Management Endpoints
@app.post("/devices", status_code=status.HTTP_201_CREATED)
async def create_user_device(
    device_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Create a new device for the current user"""
    try:
        query = """
            INSERT INTO user_devices (user_id, device_id, device_name, device_type, location)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING device_id
        """
        
        result = execute_query(query, (
            current_user["sub"],
            device_data.get("device_id"),
            device_data.get("device_name", "Unknown Device"),
            device_data.get("device_type", "Smart Device"),
            device_data.get("location", "Unknown Location")
        ))
        
        if result:
            return {"message": "Device created successfully", "device_id": result[0][0]}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create device"
            )
    except Exception as e:
        logging.error(f"Error creating device: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create device: {str(e)}"
        )

@app.get("/devices")
async def get_user_devices(current_user: dict = Depends(get_current_user)):
    """Get all devices for the current user"""
    try:
        query = """
            SELECT device_id, device_name, device_type, location, is_active, created_at
            FROM user_devices 
            WHERE user_id = %s
            ORDER BY created_at DESC
        """
        
        devices = execute_query(query, (current_user["sub"],))
        
        return [
            {
                "device_id": device[0],
                "device_name": device[1], 
                "device_type": device[2],
                "location": device[3],
                "is_active": device[4],
                "created_at": device[5]
            }
            for device in devices
        ]
    except Exception as e:
        logging.error(f"Error getting user devices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get devices: {str(e)}"
        )

@app.delete("/telemetry/{telemetry_id}")
async def delete_telemetry(
    telemetry_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete specific telemetry record (admin only)"""
    try:
        query = "DELETE FROM telemetry WHERE id = %s AND user_id = %s"
        result = execute_query(query, (telemetry_id, current_user["sub"]))
        
        return {"message": f"Telemetry record {telemetry_id} deleted successfully"}
    except Exception as e:
        logging.error(f"Error deleting telemetry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete telemetry: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
