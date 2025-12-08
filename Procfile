web: bash start.sh
worker: celery -A eko worker --loglevel=info --concurrency=2
beat: celery -A eko beat --loglevel=info
