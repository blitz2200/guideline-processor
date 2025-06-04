#!/bin/bash

# Wait for database to be ready
echo "Waiting for database..."

# PostgreSQL 연결 확인을 위한 함수
wait_for_db() {
    until python -c "
import os
import psycopg2
try:
    conn = psycopg2.connect(
        host='db',
        database='guideline_processor', 
        user='postgres',
        password='postgres',
        port=5432
    )
    conn.close()
    print('Database is ready!')
    exit(0)
except psycopg2.OperationalError:
    exit(1)
"; do
        echo "Database is unavailable - sleeping"
        sleep 2
    done
}

# 또는 더 간단한 방법 - Django의 dbshell을 이용
wait_for_db_simple() {
    until python manage.py dbshell --command="SELECT 1;" > /dev/null 2>&1; do
        echo "Database is unavailable - sleeping"
        sleep 2
    done
    echo "Database is ready!"
}

# 가장 간단한 방법 - migrate 명령어 직접 시도
wait_for_db_migrate() {
    echo "Trying to connect to database..."
    until python manage.py migrate --check > /dev/null 2>&1; do
        echo "Database is unavailable - sleeping"
        sleep 2
    done
    echo "Database is ready!"
}

# 위 함수 중 하나를 선택해서 사용
wait_for_db

# Run migrations
echo "Running migrations..."
python manage.py makemigrations --noinput || true
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || true

# Start the server
echo "Starting server..."
exec "$@"