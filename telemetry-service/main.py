from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import sqlite3
import os
import sys
from typing import List, Optional
from datetime import datetime, timedelta
import json

# Add shared models to path
sys.path.append('../shared')
from models import TelemetryCreate, TelemetryResponse, TelemetryQuery, EnergyAnalytics, DeviceHealth

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
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"

security = HTTPBearer()

# Database setup
def init_db():
    conn = sqlite3.connect('telemetry.db')
    cursor = conn.cursor()
    
    # Create telemetry table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id VARCHAR(100) NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            energy_usage REAL NOT NULL,
            voltage REAL,
            current REAL,
            power_factor REAL,
            temperature REAL,
            humidity REAL,
            status VARCHAR(50) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for better query performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_device_id ON telemetry(device_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON telemetry(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_device_timestamp ON telemetry(device_id, timestamp)')
    
    conn.commit()
    conn.close()

init_db()

# Authentication dependency
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    return payload

# Utility functions
def calculate_energy_analytics(telemetry_data: List[tuple]) -> EnergyAnalytics:
    if not telemetry_data:
        return None
    
    energy_values = [row[3] for row in telemetry_data]  # energy_usage column
    total_energy = sum(energy_values)
    average_energy = total_energy / len(energy_values)
    peak_energy = max(energy_values)
    
    # Simple cost estimation (can be made more sophisticated)
    cost_estimate = total_energy * 0.12  # Assuming $0.12 per kWh
    carbon_footprint = total_energy * 0.92  # kg CO2 per kWh
    
    return EnergyAnalytics(
        device_id=telemetry_data[0][1],  # device_id
        period="custom",
        total_energy=total_energy,
        average_energy=average_energy,
        peak_energy=peak_energy,
        cost_estimate=cost_estimate,
        carbon_footprint=carbon_footprint,
        data_points=[]  # Would convert raw data to TelemetryResponse objects
    )

# API Routes
@app.post("/telemetry", response_model=TelemetryResponse, status_code=status.HTTP_201_CREATED)
async def create_telemetry(telemetry_data: TelemetryCreate, current_user: dict = Depends(get_current_user)):
    """Create new telemetry data point"""
    conn = sqlite3.connect('telemetry.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO telemetry (device_id, energy_usage, voltage, current, power_factor, temperature, humidity, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            telemetry_data.device_id,
            telemetry_data.energy_usage,
            telemetry_data.voltage,
            telemetry_data.current,
            telemetry_data.power_factor,
            telemetry_data.temperature,
            telemetry_data.humidity,
            telemetry_data.status
        ))
        
        telemetry_id = cursor.lastrowid
        conn.commit()
        
        # Get the created telemetry data
        cursor.execute("SELECT * FROM telemetry WHERE id = ?", (telemetry_id,))
        telemetry = cursor.fetchone()
        conn.close()
        
        return TelemetryResponse(
            id=telemetry[0],
            device_id=telemetry[1],
            timestamp=telemetry[2],
            energy_usage=telemetry[3],
            voltage=telemetry[4],
            current=telemetry[5],
            power_factor=telemetry[6],
            temperature=telemetry[7],
            humidity=telemetry[8],
            status=telemetry[9]
        )
        
    except Exception as e:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create telemetry: {str(e)}"
        )

@app.get("/telemetry", response_model=List[TelemetryResponse])
async def get_telemetry(
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    start_time: Optional[datetime] = Query(None, description="Start time for filtering"),
    end_time: Optional[datetime] = Query(None, description="End time for filtering"),
    limit: int = Query(100, description="Maximum number of records to return"),
    current_user: dict = Depends(get_current_user)
):
    """Get telemetry data with optional filtering"""
    conn = sqlite3.connect('telemetry.db')
    cursor = conn.cursor()
    
    query = "SELECT * FROM telemetry WHERE 1=1"
    params = []
    
    if device_id:
        query += " AND device_id = ?"
        params.append(device_id)
    
    if start_time:
        query += " AND timestamp >= ?"
        params.append(start_time.isoformat())
    
    if end_time:
        query += " AND timestamp <= ?"
        params.append(end_time.isoformat())
    
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    telemetry_data = cursor.fetchall()
    conn.close()
    
    return [
        TelemetryResponse(
            id=row[0],
            device_id=row[1],
            timestamp=row[2],
            energy_usage=row[3],
            voltage=row[4],
            current=row[5],
            power_factor=row[6],
            temperature=row[7],
            humidity=row[8],
            status=row[9]
        )
        for row in telemetry_data
    ]

@app.get("/telemetry/{device_id}/analytics")
async def get_device_analytics(
    device_id: str,
    period: str = Query("daily", description="Analytics period: daily, weekly, monthly, yearly"),
    current_user: dict = Depends(get_current_user)
):
    """Get energy analytics for a specific device"""
    conn = sqlite3.connect('telemetry.db')
    cursor = conn.cursor()
    
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid period. Use: daily, weekly, monthly, yearly"
        )
    
    cursor.execute("""
        SELECT * FROM telemetry 
        WHERE device_id = ? AND timestamp >= ?
        ORDER BY timestamp DESC
    """, (device_id, start_time.isoformat()))
    
    telemetry_data = cursor.fetchall()
    conn.close()
    
    if not telemetry_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No telemetry data found for device {device_id} in the specified period"
        )
    
    analytics = calculate_energy_analytics(telemetry_data)
    analytics.period = period
    
    return analytics

@app.get("/telemetry/{device_id}/health")
async def get_device_health(
    device_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get device health status and recommendations"""
    conn = sqlite3.connect('telemetry.db')
    cursor = conn.cursor()
    
    # Get latest telemetry
    cursor.execute("""
        SELECT * FROM telemetry 
        WHERE device_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 1
    """, (device_id,))
    
    latest = cursor.fetchone()
    
    if not latest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No telemetry data found for device {device_id}"
        )
    
    # Get data from last 24 hours for uptime calculation
    yesterday = datetime.now() - timedelta(days=1)
    cursor.execute("""
        SELECT COUNT(*) FROM telemetry 
        WHERE device_id = ? AND timestamp >= ?
    """, (device_id, yesterday.isoformat()))
    
    recent_count = cursor.fetchone()[0]
    
    # Get error count (status != 'active')
    cursor.execute("""
        SELECT COUNT(*) FROM telemetry 
        WHERE device_id = ? AND status != 'active'
    """, (device_id,))
    
    error_count = cursor.fetchone()[0]
    
    conn.close()
    
    # Calculate uptime percentage (assuming data points every hour)
    expected_points = 24
    uptime_percentage = (recent_count / expected_points) * 100 if expected_points > 0 else 0
    
    # Generate recommendations
    recommendations = []
    if uptime_percentage < 90:
        recommendations.append("Device may be experiencing connectivity issues")
    if error_count > 0:
        recommendations.append("Device has reported errors - check device status")
    if latest[7] and latest[7] > 80:  # temperature > 80
        recommendations.append("Device temperature is high - check ventilation")
    
    return DeviceHealth(
        device_id=device_id,
        status=latest[9],  # status
        last_seen=latest[2],  # timestamp
        uptime_percentage=uptime_percentage,
        error_count=error_count,
        maintenance_due=error_count > 5 or uptime_percentage < 80,
        recommendations=recommendations
    )

@app.get("/telemetry/devices/summary")
async def get_devices_summary(current_user: dict = Depends(get_current_user)):
    """Get summary of all devices and their latest status"""
    conn = sqlite3.connect('telemetry.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT device_id, 
               MAX(timestamp) as last_seen,
               MAX(energy_usage) as latest_energy,
               COUNT(*) as total_readings
        FROM telemetry 
        GROUP BY device_id
        ORDER BY last_seen DESC
    """)
    
    devices = cursor.fetchall()
    conn.close()
    
    return [
        {
            "device_id": device[0],
            "last_seen": device[1],
            "latest_energy": device[2],
            "total_readings": device[3]
        }
        for device in devices
    ]

@app.delete("/telemetry/{telemetry_id}")
async def delete_telemetry(
    telemetry_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete specific telemetry record (admin only)"""
    # Check if user is admin (you might want to implement proper role checking)
    conn = sqlite3.connect('telemetry.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM telemetry WHERE id = ?", (telemetry_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Telemetry record {telemetry_id} not found"
        )
    
    conn.commit()
    conn.close()
    
    return {"message": f"Telemetry record {telemetry_id} deleted successfully"}

@app.get("/health")
async def health_check():
    """Service health check"""
    return {
        "status": "healthy",
        "service": "telemetry-service",
        "timestamp": datetime.now().isoformat(),
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
