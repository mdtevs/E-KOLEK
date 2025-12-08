#!/bin/bash
# Railway Startup Script - Runs Web + Celery Worker
# This script starts both Django web server and Celery worker in the same container

echo "════════════════════════════════════════════════════════════"
echo "🚀 E-KOLEK Railway Startup"
echo "════════════════════════════════════════════════════════════"

# Exit on error
set -e

# Run database migrations
echo "📦 Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "📂 Collecting static files..."
python manage.py collectstatic --noinput

# Check if Redis is available
echo "🔍 Checking Redis connection..."
if python -c "import redis; r = redis.from_url('$REDIS_URL'); r.ping(); print('✅ Redis connected')" 2>/dev/null; then
    echo "✅ Redis is available - Starting Celery worker..."
    
    # Start Celery worker in background
    celery -A eko worker \
        --loglevel=info \
        --concurrency=2 \
        --max-tasks-per-child=50 \
        --detach \
        --logfile=/tmp/celery-worker.log \
        --pidfile=/tmp/celery-worker.pid
    
    echo "✅ Celery worker started (PID file: /tmp/celery-worker.pid)"
    echo "📋 Worker logs: /tmp/celery-worker.log"
else
    echo "⚠️  Redis not available - Celery worker disabled"
    echo "📧 Email OTP will use direct SMTP fallback"
fi

# Start Gunicorn web server
echo "🌐 Starting Gunicorn web server..."
echo "════════════════════════════════════════════════════════════"

exec gunicorn eko.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    --capture-output
