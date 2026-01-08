STEPS

1. activate virtual environment
. venv/bin/activate

2. Install redis and install dependencies
pip3 install -r requirements.txt

3. Run migrations
python3 manage.py migrate

4. Start celery worker
celery -A crm worker -l info

5. Start celery beat
celery -A crm beat -f info

6. Verify logs in /tmp/crm_report_log.txt