# Smart Home Docker Setup Guide

This guide explains how to run the entire Smart Home microservices system using Docker and Docker Compose with PostgreSQL database.

## Prerequisites

- Docker Engine 20.10+ 
- Docker Compose v2.0+
- At least 4GB of available RAM
- Ports 3000, 5432, 8000-8004 available on your machine

## Quick Start

1. **Clone and navigate to the project:**
   ```bash
   cd smart-home/
   ```

2. **Build and start all services:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - API Gateway: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Architecture Overview

The system consists of the following containerized services:

- **PostgreSQL Database** (port 5432) - Centralized data storage
- **Auth Service** (port 8001) - User authentication and JWT management
- **User Service** (port 8002) - User profile management
- **Telemetry Service** (port 8003) - Device data collection and analytics
- **AI Service** (port 8004) - Conversational AI and insights
- **API Gateway** (port 8000) - Central request routing and orchestration
- **Frontend** (port 3000) - React-based user interface

## Environment Variables

Key environment variables (defined in docker-compose.yml):

```bash
SECRET_KEY=your-secret-key-here-change-in-production-2024
DB_HOST=postgres
DB_PORT=5432
DB_NAME=smarthome
DB_USER=postgres
DB_PASSWORD=postgres
```

**⚠️ IMPORTANT**: Change the `SECRET_KEY` and database credentials before production deployment!

## Individual Service Commands

### Start specific services:
```bash
# Database only
docker-compose up postgres

# Backend services only
docker-compose up postgres auth-service user-service telemetry-service ai-service

# Full stack
docker-compose up --build
```

### Stop services:
```bash
docker-compose down
```

### View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f auth-service
```

### Rebuild specific service:
```bash
docker-compose up --build auth-service
```

## Database Management

### Access PostgreSQL directly:
```bash
docker-compose exec postgres psql -U postgres -d smarthome
```

### Reset database:
```bash
docker-compose down -v  # Remove volumes
docker-compose up postgres --build  # Recreate database
```

### Backup database:
```bash
docker-compose exec postgres pg_dump -U postgres smarthome > backup.sql
```

## Health Checks

All services include health checks. Monitor service status:

```bash
docker-compose ps
```

Individual health endpoints:
- Auth Service: http://localhost:8001/health
- User Service: http://localhost:8002/health  
- Telemetry Service: http://localhost:8003/health
- AI Service: http://localhost:8004/health
- API Gateway: http://localhost:8000/health

## Development Workflow

### Make code changes:
1. Edit source code
2. Rebuild affected services: `docker-compose up --build <service-name>`
3. Test changes

### Add new dependencies:
1. Update `requirements.txt` in the service directory
2. Rebuild: `docker-compose up --build <service-name>`

### Database schema changes:
- Services automatically create/update tables on startup
- For major changes, consider migrations

## Troubleshooting

### Services fail to start:
- Check port availability: `netstat -tlnp | grep :8000`
- View logs: `docker-compose logs <service-name>`
- Ensure Docker has sufficient resources

### Database connection issues:
- Verify PostgreSQL is healthy: `docker-compose ps postgres`
- Check database logs: `docker-compose logs postgres`
- Ensure all services wait for database health check

### Frontend issues:
- Verify API Gateway is running: `curl http://localhost:8000/health`
- Check CORS settings in backend services
- Clear browser cache

### Performance issues:
- Monitor resource usage: `docker stats`
- Scale services: `docker-compose up --scale auth-service=2`
- Add resource limits in docker-compose.yml

## Production Deployment


### Environment-specific configs:
```bash
# Production
export SECRET_KEY="your-super-secure-key-here"
export DB_PASSWORD="secure-db-password"
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
```

## Scaling

Scale individual services:
```bash
# Scale auth service to 3 instances
docker-compose up --scale auth-service=3

# Scale with load balancer
docker-compose up --scale auth-service=3 --scale user-service=2
```

## Monitoring

### View real-time metrics:
```bash
docker stats
```

### Export logs:
```bash
docker-compose logs --since 1h > logs.txt
```

### Database metrics:
```bash
docker-compose exec postgres psql -U postgres -d smarthome -c "SELECT * FROM pg_stat_activity;"
```

## API Documentation

Once running, interactive API documentation is available at:
- API Gateway: http://localhost:8000/docs
- Auth Service: http://localhost:8001/docs
- User Service: http://localhost:8002/docs
- Telemetry Service: http://localhost:8003/docs
- AI Service: http://localhost:8004/docs

## Support

For issues and questions:
1. Check service logs: `docker-compose logs <service>`
2. Verify health endpoints
3. Review this documentation
4. Check Docker and system resources
