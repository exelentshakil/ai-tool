#!/bin/bash
cd /var/www/calculator-system
source venv/bin/activate
exec gunicorn \
    --bind 127.0.0.1:5000 \
    --workers 4 \
    --worker-class sync \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --timeout 30 \
    --keep-alive 2 \
    --log-level info \
    --access-logfile /var/www/calculator-system/logs/access.log \
    --error-logfile /var/www/calculator-system/logs/error.log \
    app:app
