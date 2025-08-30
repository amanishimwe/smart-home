from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# User Management Models
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole = UserRole.USER

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    is_active: bool = True

class UserLogin(BaseModel):
    username: str
    password: str
    remember_me: bool = False

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse

# Telemetry Models
class TelemetryData(BaseModel):
    device_id: str
    timestamp: datetime
    energy_usage: float
    voltage: Optional[float] = None
    current: Optional[float] = None
    power_factor: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    status: str = "active"

class TelemetryCreate(BaseModel):
    device_id: str
    energy_usage: float
    voltage: Optional[float] = None
    current: Optional[float] = None
    power_factor: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    status: str = "active"

class TelemetryResponse(BaseModel):
    id: int
    device_id: str
    timestamp: datetime
    energy_usage: float
    voltage: Optional[float] = None
    current: Optional[float] = None
    power_factor: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    status: str

class TelemetryQuery(BaseModel):
    device_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: Optional[int] = 100

# Conversational AI Models
class UserQuestion(BaseModel):
    question: str
    user_id: int
    context: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

class AIResponse(BaseModel):
    answer: str
    intent: str
    confidence: float
    data_summary: Optional[Dict[str, Any]] = None
    time_series_data: Optional[List[Dict[str, Any]]] = None
    suggested_actions: Optional[List[str]] = None
    timestamp: datetime

class ConversationSession(BaseModel):
    session_id: str
    user_id: int
    start_time: datetime
    last_activity: datetime
    context: Dict[str, Any] = {}

# Device Models
class DeviceBase(BaseModel):
    name: str
    device_type: str
    location: str
    is_active: bool = True
    manufacturer: Optional[str] = None
    model: Optional[str] = None

class DeviceCreate(DeviceBase):
    user_id: int
    device_id: str  # Unique identifier for telemetry

class DeviceResponse(DeviceBase):
    id: int
    user_id: int
    device_id: str
    created_at: datetime
    last_seen: Optional[datetime] = None
    last_telemetry: Optional[TelemetryResponse] = None

# Notification Models
class NotificationBase(BaseModel):
    title: str
    message: str
    notification_type: str
    user_id: int
    priority: str = "normal"

class NotificationCreate(NotificationBase):
    pass

class NotificationResponse(NotificationBase):
    id: int
    created_at: datetime
    is_read: bool = False
    read_at: Optional[datetime] = None

# Analytics Models
class EnergyAnalytics(BaseModel):
    device_id: str
    period: str  # daily, weekly, monthly, yearly
    total_energy: float
    average_energy: float
    peak_energy: float
    cost_estimate: float
    carbon_footprint: float
    data_points: List[TelemetryResponse]

class DeviceHealth(BaseModel):
    device_id: str
    status: str
    last_seen: datetime
    uptime_percentage: float
    error_count: int
    maintenance_due: bool
    recommendations: List[str]
