# Extends the official Airflow image with this project's Python dependencies
# (boto3, SQLAlchemy, psycopg2-binary, ...) so DAG tasks can talk to MinIO and
# Postgres without relying on the _PIP_ADDITIONAL_REQUIREMENTS dev shortcut.
FROM apache/airflow:2.9.3-python3.11

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
