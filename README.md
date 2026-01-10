CRM Background Tasks – Setup Guide

1. Install Redis and Python dependencies
Install Redis (Linux – Ubuntu/Debian)
sudo apt update
sudo apt install redis-server

Start Redis
sudo systemctl start redis
sudo systemctl enable redis

Verify Redis is running: redis-cli ping
Expected output: PONG

Install Python dependencies
Activate your virtual environment (if applicable): ". venv/bin/activate", 
Then run: pip3 install -r requirements.txt

2. Run database migrations

Apply Django migrations: python3 manage.py migrate

3. Start the Celery worker

From the Django project root directory: celery -A crm worker -l info

4. Start Celery Beat (task scheduler)

Open a new terminal and run: celery -A crm beat -l info

5. Verify CRM report generation

The scheduled task writes logs to: /tmp/crm_report_log.txt

Check the log file: cat /tmp/crm_report_log.txt
Or follow updates live: tail -f /tmp/crm_report_log.txt