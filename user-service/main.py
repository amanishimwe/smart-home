from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
import os
import sys
from typing import List
import logging

# Import shared models and database
from shared.models import UserResponse, UserRole
from shared.database import execute_query, check_connection

app = FastAPI(title="User Service", version="1.0.0")

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
    try:
        execute_query('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100) UNIQUE NOT NULL,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                phone VARCHAR(20),
                address TEXT,
                preferences TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''', fetch=False)
        logging.info("User service database initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize user service database: {e}")
        raise

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    # Wait for database to be ready
    import time
    max_retries = 30
    for i in range(max_retries):
        if check_connection():
            init_db()
            break
        else:
            logging.info(f"Waiting for database... ({i+1}/{max_retries})")
            time.sleep(2)
    else:
        raise Exception("Could not connect to database after maximum retries")

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

# API Routes
@app.get("/me", response_model=dict)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    # This would typically fetch from a user database
    # For now, return the JWT payload
    return {
        "username": current_user.get("sub"),
        "role": current_user.get("role"),
        "exp": current_user.get("exp")
    }

@app.get("/users", response_model=List[dict])
async def get_all_users(current_user: dict = Depends(require_role(UserRole.ADMIN))):
    # This would fetch from a user database
    # For now, return mock data
    return [
        {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "role": "admin",
            "is_active": True
        }
    ]

@app.get("/profile/{user_id}")
async def get_user_profile(user_id: int, current_user: dict = Depends(get_current_user)):
    # Check if user is requesting their own profile or is admin
    if current_user.get("sub") != str(user_id) and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only access own profile"
        )
    
    # Fetch profile from database
    result = execute_query("SELECT * FROM user_profiles WHERE user_id = %s", (str(user_id),))
    profile = result[0] if result else None
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return {
        "user_id": profile[1],
        "first_name": profile[2],
        "last_name": profile[3],
        "phone": profile[4],
        "address": profile[5],
        "preferences": profile[6],
        "created_at": profile[7],
        "updated_at": profile[8]
    }

@app.put("/profile/{user_id}")
async def update_user_profile(user_id: int, profile_data: dict, current_user: dict = Depends(get_current_user)):
    if current_user.get("sub") != str(user_id) and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only update own profile"
        )
    
    # Check if profile exists
    existing = execute_query("SELECT * FROM user_profiles WHERE user_id = %s", (str(user_id),))
    
    if not existing:
        # Create new profile
        execute_query("""
            INSERT INTO user_profiles (user_id, first_name, last_name, phone, address, preferences)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            str(user_id),
            profile_data.get("first_name"),
            profile_data.get("last_name"),
            profile_data.get("phone"),
            profile_data.get("address"),
            profile_data.get("preferences")
        ), fetch=False)
    else:
        # Update existing profile
        execute_query("""
            UPDATE user_profiles 
            SET first_name = %s, last_name = %s, phone = %s, address = %s, preferences = %s, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %s
        """, (
            profile_data.get("first_name"),
            profile_data.get("last_name"),
            profile_data.get("phone"),
            profile_data.get("address"),
            profile_data.get("preferences"),
            str(user_id)
        ), fetch=False)
    
    return {"message": "Profile updated successfully"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "user-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
