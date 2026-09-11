FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Production WSGI server. Long timeout accommodates the heavy analytics
# aggregations until the caching layer is enabled.
CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "3", "--timeout", "120", "run:app"]
