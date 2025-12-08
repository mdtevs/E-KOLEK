web: python manage.py migrate && python manage.py collectstatic --noinput && gunicorn eko.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --log-level debug --access-logfile - --error-logfile -
worker: celery -A eko worker --loglevel=info --concurrency=2
beat: celery -A eko beat --loglevel=info
