FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 8000

# ТАК КАК ПАПКА НАЗЫВАЕТСЯ config: Запускаем wsgi-модуль из твоей корневой директории
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

