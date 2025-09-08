from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from typing import Optional
import sys
import logging

# Import shared models and database
from shared.models import UserCreate, UserLogin, UserResponse, Token, UserRole
from shared.database import execute_query, check_connection

app = FastAPI(
    title="Auth Service", 
    description="User authentication and authorization microservice",
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
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Database setup
def init_db():
    try:
        execute_query('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''', fetch=False)
        logging.info("Auth database initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize auth database: {e}")
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

# Utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_user_by_username(username: str):
    try:
        result = execute_query("SELECT * FROM users WHERE username = %s", (username,))
        return dict(result[0]) if result else None
    except Exception as e:
        logging.error(f"Error getting user by username: {e}")
        return None

def get_user_by_email(email: str):
    try:
        result = execute_query("SELECT * FROM users WHERE email = %s", (email,))
        return dict(result[0]) if result else None
    except Exception as e:
        logging.error(f"Error getting user by email: {e}")
        return None

def create_user(user_data: UserCreate):
    hashed_password = get_password_hash(user_data.password)
    
    try:
        # Insert user and return the created user
        execute_query("""
            INSERT INTO users (username, email, password_hash, role)
            VALUES (%s, %s, %s, %s)
        """, (user_data.username, user_data.email, hashed_password, user_data.role.value), fetch=False)
        
        # Get the created user
        result = execute_query("SELECT * FROM users WHERE username = %s", (user_data.username,))
        if result:
            user = result[0]
            return {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "role": user[4],
                "created_at": user[5],
                "is_active": user[6]
            }
        return None
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        return None

# API Routes
@app.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user"""
    if get_user_by_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    if get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = create_user(user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create user"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": UserResponse(**user)
    }

@app.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Authenticate user and return JWT token"""
    user = get_user_by_username(user_credentials.username)
    
    if not user or not verify_password(user_credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Set token expiration based on remember_me
    if user_credentials.remember_me:
        access_token_expires = timedelta(days=30)
        expires_in = 30 * 24 * 60 * 60
    else:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        expires_in = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            role=user["role"],
            created_at=user["created_at"],
            is_active=user["is_active"]
        )
    }

@app.get("/health")
async def health_check():
    """Service health check"""
    return {
        "status": "healthy",
        "service": "auth-service",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
