FROM python:3.9-slim

# Evita que Python genere archivos .pyc y permite ver logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalamos librerías necesarias
RUN pip install --no-cache-dir redis flask flask-cors

# Copiamos el script del backend
COPY backend.py .

# Exponemos el puerto de Flask
EXPOSE 5000

CMD ["python", "backend.py"]