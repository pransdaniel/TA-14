web: python manage.py migrate && python manage.py collectstatic --noinput && gunicorn adaptive_engine.wsgi --bind 0.0.0.0:${PORT:-8000}
