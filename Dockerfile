FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install Flask-Cors
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "120", "app:app"]