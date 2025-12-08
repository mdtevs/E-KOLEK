web: gunicorn eko.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120 --log-level info
worker: celery -A eko worker --loglevel=info --concurrency=2
beat: celery -A eko beat --loglevel=info
