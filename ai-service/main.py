from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import os
import sys
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import re
import logging

# Import shared models and database
from shared.models import UserQuestion, AIResponse, ConversationSession, TelemetryResponse
from shared.database import execute_query, check_connection

app = FastAPI(
    title="Conversational AI Service",
    description="Handles user questions and provides intelligent responses with data insights",
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
    try:
        # Create conversations table
        execute_query('''
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(100) UNIQUE NOT NULL,
                user_id VARCHAR(100) NOT NULL,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                context TEXT DEFAULT '{}'
            )
        ''', fetch=False)
        
        # Create questions table
        execute_query('''
            CREATE TABLE IF NOT EXISTS questions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(100) NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                intent VARCHAR(100),
                confidence REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                context TEXT DEFAULT '{}'
            )
        ''', fetch=False)
        
        logging.info("AI database initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize AI database: {e}")
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

# AI Intent Recognition
def analyze_intent(question: str) -> tuple[str, float]:
    """Simple intent recognition using keyword matching"""
    question_lower = question.lower()
    
    # Energy usage patterns
    energy_patterns = {
        "energy": ["energy", "power", "electricity", "consumption", "usage", "kwh"],
        "cost": ["cost", "bill", "money", "expensive", "cheap", "savings"],
        "device": ["device", "appliance", "machine", "equipment", "sensor"],
        "status": ["status", "working", "broken", "online", "offline", "health"],
        "comparison": ["compare", "versus", "vs", "difference", "better", "worse"],
        "trend": ["trend", "pattern", "increase", "decrease", "over time", "history"],
        "recommendation": ["recommend", "suggestion", "advice", "tip", "optimize", "improve"]
    }
    
    max_confidence = 0
    detected_intent = "general"
    
    for intent, keywords in energy_patterns.items():
        matches = sum(1 for keyword in keywords if keyword in question_lower)
        if matches > 0:
            confidence = min(matches / len(keywords) * 2, 1.0)  # Scale confidence
            if confidence > max_confidence:
                max_confidence = confidence
                detected_intent = intent
    
    return detected_intent, max_confidence

# AI Response Generation
def generate_response(question: str, intent: str, confidence: float, user_id: int) -> AIResponse:
    """Generate intelligent response based on intent and context"""
    
    # Mock telemetry data (in real implementation, this would come from telemetry service)
    mock_telemetry = {
        "device_001": {"energy": 2.5, "status": "active", "temperature": 45},
        "device_002": {"energy": 1.8, "status": "active", "temperature": 38},
        "device_003": {"energy": 3.2, "status": "warning", "temperature": 75}
    }
    
    if intent == "energy":
        if "total" in question.lower() or "all" in question.lower():
            total_energy = sum(device["energy"] for device in mock_telemetry.values())
            answer = f"Total energy consumption across all devices is {total_energy:.1f} kWh."
            data_summary = {"total_energy": total_energy, "device_count": len(mock_telemetry)}
        else:
            device_energy = {k: v["energy"] for k, v in mock_telemetry.items()}
            answer = f"Current energy consumption: {', '.join([f'{k}: {v} kWh' for k, v in device_energy.items()])}"
            data_summary = {"device_energy": device_energy}
    
    elif intent == "cost":
        total_energy = sum(device["energy"] for device in mock_telemetry.values())
        estimated_cost = total_energy * 0.12  # $0.12 per kWh
        answer = f"Estimated daily cost: ${estimated_cost:.2f} based on current consumption of {total_energy:.1f} kWh."
        data_summary = {"estimated_cost": estimated_cost, "energy_consumption": total_energy}
    
    elif intent == "device":
        if "status" in question.lower() or "health" in question.lower():
            device_status = {k: v["status"] for k, v in mock_telemetry.items()}
            answer = f"Device status: {', '.join([f'{k}: {v}' for k, v in device_status.items()])}"
            data_summary = {"device_status": device_status}
        else:
            answer = f"You have {len(mock_telemetry)} devices connected. Ask me about their energy usage, status, or health!"
            data_summary = {"device_count": len(mock_telemetry)}
    
    elif intent == "status":
        warnings = [k for k, v in mock_telemetry.items() if v["status"] != "active"]
        if warnings:
            answer = f"Warning: Devices {', '.join(warnings)} need attention. Device 003 has high temperature (75°C)."
            data_summary = {"warnings": warnings, "high_temp_devices": ["device_003"]}
        else:
            answer = "All devices are operating normally with good status."
            data_summary = {"status": "all_normal"}
    
    elif intent == "trend":
        # Mock time series data
        time_series = [
            {"timestamp": "2024-01-15T10:00:00", "energy": 2.1},
            {"timestamp": "2024-01-15T11:00:00", "energy": 2.3},
            {"timestamp": "2024-01-15T12:00:00", "energy": 2.5},
            {"timestamp": "2024-01-15T13:00:00", "energy": 2.8}
        ]
        answer = "Energy consumption shows an upward trend over the last few hours. This might indicate increased device usage."
        data_summary = {"trend": "increasing", "change_percentage": 33}
        time_series_data = time_series
    
    elif intent == "recommendation":
        high_temp_devices = [k for k, v in mock_telemetry.items() if v["temperature"] > 70]
        if high_temp_devices:
            answer = f"Recommendation: Check ventilation for devices {', '.join(high_temp_devices)}. High temperatures can affect efficiency and lifespan."
            suggested_actions = ["Check device ventilation", "Monitor temperature trends", "Consider device maintenance"]
        else:
            answer = "Your devices are operating efficiently! Consider setting up energy usage alerts to optimize consumption."
            suggested_actions = ["Set up energy alerts", "Monitor usage patterns", "Schedule regular maintenance"]
        data_summary = {"recommendations_count": len(suggested_actions)}
    
    else:
        answer = "I can help you with energy monitoring, device status, cost analysis, and recommendations. Try asking about your energy usage, device health, or cost savings!"
        data_summary = {"capabilities": ["energy_monitoring", "device_status", "cost_analysis", "recommendations"]}
    
    return AIResponse(
        answer=answer,
        intent=intent,
        confidence=confidence,
        data_summary=data_summary,
        time_series_data=time_series_data if 'time_series_data' in locals() else None,
        suggested_actions=suggested_actions if 'suggested_actions' in locals() else None,
        timestamp=datetime.now()
    )

# API Routes
@app.post("/ai/ask", response_model=AIResponse)
async def ask_question(question_data: UserQuestion, current_user: dict = Depends(get_current_user)):
    """Ask a question and get AI-powered response"""
    
    # Create or get conversation session
    session_id = f"session_{current_user.get('sub')}_{int(datetime.now().timestamp())}"
    
    # Analyze intent
    intent, confidence = analyze_intent(question_data.question)
    
    # Generate response
    ai_response = generate_response(question_data.question, intent, confidence, question_data.user_id)
    
    # Store conversation in database
    try:
        # Store question and answer
        execute_query("""
            INSERT INTO questions (session_id, question, answer, intent, confidence, context)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            session_id,
            question_data.question,
            ai_response.answer,
            intent,
            confidence,
            json.dumps(question_data.context or {})
        ), fetch=False)
        
    except Exception as e:
        logging.error(f"Error storing conversation: {e}")
    
    return ai_response

@app.get("/ai/conversations", response_model=List[Dict[str, Any]])
async def get_conversation_history(
    limit: int = Query(10, description="Number of recent conversations to return"),
    current_user: dict = Depends(get_current_user)
):
    """Get conversation history for the current user"""
    conversations = execute_query("""
        SELECT q.question, q.answer, q.intent, q.confidence, q.timestamp
        FROM questions q
        WHERE q.session_id LIKE %s
        ORDER BY q.timestamp DESC
        LIMIT %s
    """, (f"session_{current_user.get('sub')}%", limit))
    
    return [
        {
            "question": conv[0],
            "answer": conv[1],
            "intent": conv[2],
            "confidence": conv[3],
            "timestamp": conv[4]
        }
        for conv in conversations
    ]

@app.get("/ai/intents")
async def get_intent_statistics(current_user: dict = Depends(get_current_user)):
    """Get statistics about user's question intents"""
    conn = sqlite3.connect('ai_conversations.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT intent, COUNT(*) as count, AVG(confidence) as avg_confidence
        FROM questions
        WHERE session_id LIKE ?
        GROUP BY intent
        ORDER BY count DESC
    """, (f"session_{current_user.get('sub')}%",))
    
    stats = cursor.fetchall()
    conn.close()
    
    return [
        {
            "intent": stat[0],
            "count": stat[1],
            "average_confidence": round(stat[2], 2) if stat[2] else 0
        }
        for stat in stats
    ]

@app.post("/ai/session/start")
async def start_conversation_session(current_user: dict = Depends(get_current_user)):
    """Start a new conversation session"""
    session_id = f"session_{current_user.get('sub')}_{int(datetime.now().timestamp())}"
    
    conn = sqlite3.connect('ai_conversations.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO conversations (session_id, user_id, context)
            VALUES (?, ?, ?)
        """, (session_id, current_user.get('sub'), json.dumps({})))
        
        conn.commit()
        
        return {
            "session_id": session_id,
            "message": "Conversation session started",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start session: {str(e)}"
        )
    finally:
        conn.close()

@app.get("/ai/insights")
async def get_ai_insights(current_user: dict = Depends(get_current_user)):
    """Get AI-generated insights about user's smart home usage"""
    
    # Mock insights (in real implementation, this would analyze actual data)
    insights = {
        "energy_optimization": {
            "title": "Energy Optimization Opportunity",
            "description": "Your devices show 15% higher energy usage during peak hours",
            "recommendation": "Consider scheduling non-essential devices to run during off-peak hours",
            "potential_savings": "$45/month"
        },
        "device_health": {
            "title": "Device Maintenance Alert",
            "description": "Device 003 has been running at high temperature for 3 days",
            "recommendation": "Check ventilation and consider maintenance",
            "priority": "high"
        },
        "usage_patterns": {
            "title": "Usage Pattern Analysis",
            "description": "Your energy consumption peaks between 6-9 PM daily",
            "recommendation": "This is normal for residential usage patterns",
            "confidence": "high"
        }
    }
    
    return {
        "user_id": current_user.get('sub'),
        "insights": insights,
        "generated_at": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Service health check"""
    return {
        "status": "healthy",
        "service": "ai-service",
        "timestamp": datetime.now().isoformat(),
        "capabilities": [
            "intent_recognition",
            "response_generation",
            "conversation_tracking",
            "insight_generation"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
