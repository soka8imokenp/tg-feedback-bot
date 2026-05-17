FROM python:3.12.9-slim

WORKDIR /app

# Установите системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Скопируйте requirements и установите зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Скопируйте файлы проекта
COPY . .

# Собрать статические файлы Django
RUN python manage.py collectstatic --noinput || true

# Откройте порт
EXPOSE 8000

# Запустите Django приложение с Gunicorn
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
