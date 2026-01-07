activate virtual environment
. venv/bin/activate

install dependencies
pip3 install -r requirements.txt

run migrations
python3 manage.py migrate

start celery worker
celery -A crm worker -l info

start celery beat
celery -A crm beat -f info

verify logs in /tmp/crm_report_log.txt