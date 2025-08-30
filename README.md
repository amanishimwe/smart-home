# Smart Home - Microservice Architecture

A modern smart home application built with microservices architecture using FastAPI, React, and Docker. The system provides comprehensive energy monitoring, device management, and conversational AI capabilities.

## 🚀 Core Services

### 1. **Auth Service** (Port 8001)
- **Purpose:** User registration, login, JWT issuance, and role management
- **Features:**
  - User authentication and authorization
  - JWT token management with expiration
  - Role-based access control (Admin, User, Guest)
  - Password hashing with bcrypt
  - Session management
- **Endpoints:**
  - `POST /register` - User registration
  - `POST /login` - User authentication
  - `GET /health` - Service health check

### 2. **Telemetry Service** (Port 8003)
- **Purpose:** Accepts and stores device telemetry data
- **Features:**
  - Real-time device data collection
  - Energy usage monitoring (kWh, voltage, current, power factor)
  - Environmental monitoring (temperature, humidity)
  - Device status tracking
  - Energy analytics and cost estimation
  - Device health monitoring and recommendations
- **Endpoints:**
  - `POST /telemetry` - Create telemetry data point
  - `GET /telemetry` - Get telemetry data with filtering
  - `GET /telemetry/{device_id}/analytics` - Energy analytics
  - `GET /telemetry/{device_id}/health` - Device health status
  - `GET /telemetry/devices/summary` - Devices overview

### 3. **Conversational AI Service** (Port 8004)
- **Purpose:** Receives user questions, interprets intent, and returns structured summaries
- **Features:**
  - Natural language processing for energy-related queries
  - Intent recognition (energy, cost, device, status, trends, recommendations)
  - Contextual responses with data insights
  - Time-series data visualization
  - Conversation history and session management
  - AI-generated insights and recommendations
- **Endpoints:**
  - `POST /ai/ask` - Ask AI question
  - `GET /ai/conversations` - Conversation history
  - `GET /ai/intents` - Intent statistics
  - `POST /ai/session/start` - Start conversation session
  - `GET /ai/insights` - AI-generated insights

### 4. **User Service** (Port 8002)
- **Purpose:** User profile and account management
- **Features:**
  - User profile CRUD operations
  - Account preferences and settings
  - Role-based permissions
- **Endpoints:**
  - `GET /users/me` - Current user info
  - `GET /users/profile/{user_id}` - User profile
  - `PUT /users/profile/{user_id}` - Update profile

### 5. **API Gateway** (Port 8000)
- **Purpose:** Central routing and orchestration
- **Features:**
  - Request routing to appropriate services
  - Authentication middleware
  - Service health monitoring
  - Load balancing preparation
  - Unified API documentation

## 🛠️ Technology Stack

- **Backend:** FastAPI, Python 3.8+
- **Frontend:** React, Vite, Tailwind CSS
- **Database:** SQLite (for now, will change to PostgreSQL later)
- **Authentication:** JWT tokens with bcrypt
- **Containerization:** Docker & Docker Compose
- **API Documentation:** OpenAPI/Swagger
- **AI:** Intent recognition and response generation

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.8+
- Node.js 16+

### Option 1: Docker (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd Smart-home

# Start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:5173
# API Gateway: http://localhost:8000
# Auth Service: http://localhost:8001
# User Service: http://localhost:8002
# Telemetry Service: http://localhost:8003
# AI Service: http://localhost:8004
```

### Option 2: Local Development
```bash
# Install shared dependencies
cd shared
pip install -r requirements.txt

# Start services in separate terminals
cd ../auth-service && python main.py
cd ../user-service && python main.py
cd ../telemetry-service && python main.py
cd ../ai-service && python main.py
cd ../api-gateway && python main.py
cd ../frontend && npm run dev
```


## 🔐 Authentication Flow

1. **Registration:** User creates account via `/auth/register`
2. **Login:** User authenticates via `/auth/login`
3. **Token:** JWT token issued and stored
4. **Authorization:** Token used for subsequent API calls
5. **Role-based Access:** Different permissions based on user role

### Ports
- Frontend: 5173
- API Gateway: 8000
- Auth Service: 8001
- User Service: 8002
- Telemetry Service: 8003
- AI Service: 8004

## 🚀 Deployment

### Production Considerations
1. **Database:** Use PostgreSQL instead of SQLite
2. **Secrets:** Use environment variables or secret management
3. **Monitoring:** Add logging, metrics, and health checks
4. **Scaling:** Use Kubernetes for container orchestration
5. **Security:** Enable HTTPS, rate limiting, and CORS

**Happy coding! 🎉**
