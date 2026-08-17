# Deployment Guide

## Production Docker Compose Setup
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## Monitoring Health
- `/health`: Health status endpoint
- `/readiness`: Readiness check
- `/liveness`: Liveness check
