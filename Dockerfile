# Basic Python container for Junior Apogee App
FROM python:3.11-slim

WORKDIR /app
COPY . /app
RUN pip install --upgrade pip && \
    pip install -e .

EXPOSE 5000
CMD ["python", "app.py"]
