# Railway Environment Variables for Redis Auth System

# Redis Configuration (Railway will provide these)
REDIS_HOST=${REDIS_HOST}
REDIS_PORT=${REDIS_PORT}
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_DB=0

# Application Configuration
NODE_ENV=production
LOG_LEVEL=INFO
DEBUG=false

# FastAPI Configuration
HOST=0.0.0.0
PORT=${PORT}

# CORS Configuration (Next.js frontend)
ALLOWED_ORIGINS=${NEXT_PUBLIC_SITE_URL}
CORS_CREDENTIALS=true

# OpenAI Configuration
OPENAI_API_KEY=${OPENAI_API_KEY}

# Session Configuration
SESSION_EXPIRY_MINUTES=30
MAX_SESSIONS=1000