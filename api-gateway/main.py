from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import httpx
import os
import sys
from typing import Optional

# Add shared models to path
sys.path.append('../shared')
from models import UserRole

app = FastAPI(
    title="Smart Home API Gateway",
    description="Central gateway for all smart home microservices",
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

# Service URLs
AUTH_SERVICE_URL = "http://localhost:8001"
USER_SERVICE_URL = "http://localhost:8002"
TELEMETRY_SERVICE_URL = "http://localhost:8003"
AI_SERVICE_URL = "http://localhost:8004"

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

# Role-based access control
def require_role(required_role: UserRole):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") != required_role.value and current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# Health check for all services
@app.get("/health")
async def health_check():
    """Check health of all microservices"""
    services = {}
    
    # Check auth service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{AUTH_SERVICE_URL}/health")
            services["auth-service"] = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        services["auth-service"] = "unreachable"
    
    # Check user service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{USER_SERVICE_URL}/health")
            services["user-service"] = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        services["user-service"] = "unreachable"
    
    # Check telemetry service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{TELEMETRY_SERVICE_URL}/health")
            services["telemetry-service"] = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        services["telemetry-service"] = "unreachable"
    
    # Check AI service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{AI_SERVICE_URL}/health")
            services["ai-service"] = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        services["ai-service"] = "unreachable"
    
    return {
        "status": "gateway-healthy",
        "timestamp": "2024-01-15T10:30:00Z",
        "services": services
    }

# ===== AUTH SERVICE ROUTES =====
@app.post("/auth/register")
async def register(user_data: dict):
    """User registration endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{AUTH_SERVICE_URL}/register", json=user_data)
        return response.json()

@app.post("/auth/login")
async def login(user_credentials: dict):
    """User authentication endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{AUTH_SERVICE_URL}/login", json=user_credentials)
        return response.json()

# ===== USER SERVICE ROUTES =====
@app.get("/users/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {current_user.get('token')}"}
        response = await client.get(f"{USER_SERVICE_URL}/me", headers=headers)
        return response.json()

@app.get("/users")
async def get_all_users(current_user: dict = Depends(require_role(UserRole.ADMIN))):
    """Get all users (admin only)"""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {current_user.get('token')}"}
        response = await client.get(f"{USER_SERVICE_URL}/users", headers=headers)
        return response.json()

@app.get("/users/profile/{user_id}")
async def get_user_profile(user_id: int, current_user: dict = Depends(get_current_user)):
    """Get user profile"""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {current_user.get('token')}"}
        response = await client.get(f"{USER_SERVICE_URL}/profile/{user_id}", headers=headers)
        return response.json()

@app.put("/users/profile/{user_id}")
async def update_user_profile(user_id: int, profile_data: dict, current_user: dict = Depends(get_current_user)):
    """Update user profile"""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {current_user.get('token')}"}
        response = await client.put(f"{USER_SERVICE_URL}/profile/{user_id}", json=profile_data, headers=headers)
        return response.json()

# ===== TELEMETRY SERVICE ROUTES =====
@app.post("/telemetry")
async def create_telemetry(telemetry_data: dict, current_user: dict = Depends(get_current_user)):
    """Create new telemetry data point"""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {current_user.get('token')}"}
        response = await client.post(f"{TELEMETRY_SERVICE_URL}/telemetry", json=telemetry_data, headers=headers)
        return response.json()

@app.get("/telemetry")
async def get_telemetry(
    device_id: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Get telemetry data with optional filtering"""
    params = {"limit": limit}
    if device_id:
        params["device_id"] = device_id
    if start_time:
        params["start_time"] = start_time
    if end_time:
        params["end_time"] = end_time
    
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {current_user.get('token')}"}
        response = await client.get(f"{TELEMETRY_SERVICE_URL}/telemetry", params=params, headers=headers)
        return response.json()

@app.get("/telemetry/{device_id}/analytics")
async def get_device_analytics(
    device_id: str,
    period: str = "daily",
    current_user: dict = Depends(get_current_user)
):
    """Get energy analytics for a specific device"""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {current_user.get('token')}"}
        response = await client.get(f"{TELEMETRY_SERVICE_URL}/telemetry/{device_id}/analytics", params={"period": period}, headers=headers)
        return response.json()

@app.get("/telemetry/{device_id}/health")
async def get_device_health(device_id: str, current_user: dict = Depends(get_current_user)):
    """Get device health status and recommendations"""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {current_user.get('token')}"}
        response = await client.get(f"{TELEMETRY_SERVICE_URL}/telemetry/{device_id}/health", headers=headers)
        return response.json()

@app.get("/telemetry/devices/summary")
async def get_devices_summary(current_user: dict = Depends(get_current_user)):
    """Get summary of all devices and their latest status"""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {current_user.get('token')}"}
        response = await client.get(f"{TELEMETRY_SERVICE_URL}/telemetry/devices/summary", headers=headers)
        return response.json()

# ===== AI SERVICE ROUTES =====
@app.post("/ai/ask")
async def ask_ai_question(question_data: dict, current_user: dict = Depends(get_current_user)):
    """Ask a question to the AI service"""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {current_user.get('token')}"}
        response = await client.post(f"{AI_SERVICE_URL}/ai/ask", json=question_data, headers=headers)
        return response.json()

@app.get("/ai/conversations")
async def get_ai_conversations(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Get AI conversation history"""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {current_user.get('token')}"}
        response = await client.get(f"{AI_SERVICE_URL}/ai/conversations", params={"limit": limit}, headers=headers)
        return response.json()

@app.get("/ai/intents")
async def get_ai_intent_statistics(current_user: dict = Depends(get_current_user)):
    """Get AI intent statistics"""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {current_user.get('token')}"}
        response = await client.get(f"{AI_SERVICE_URL}/ai/intents", headers=headers)
        return response.json()

@app.post("/ai/session/start")
async def start_ai_session(current_user: dict = Depends(get_current_user)):
    """Start a new AI conversation session"""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {current_user.get('token')}"}
        response = await client.post(f"{AI_SERVICE_URL}/ai/session/start", headers=headers)
        return response.json()

@app.get("/ai/insights")
async def get_ai_insights(current_user: dict = Depends(get_current_user)):
    """Get AI-generated insights about smart home usage"""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {current_user.get('token')}"}
        response = await client.get(f"{AI_SERVICE_URL}/ai/insights", headers=headers)
        return response.json()

# ===== ROOT ENDPOINT =====
@app.get("/")
async def root():
    """API Gateway root endpoint"""
    return {
        "message": "Smart Home API Gateway",
        "version": "1.0.0",
        "status": "running",
        "services": {
            "auth": AUTH_SERVICE_URL,
            "user": USER_SERVICE_URL,
            "telemetry": TELEMETRY_SERVICE_URL,
            "ai": AI_SERVICE_URL
        },
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
