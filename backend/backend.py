import redis
import time
import random
from flask import Flask, jsonify
from flask_cors import CORS
import threading
import sys

app = Flask(__name__)
CORS(app)

# Use 'database' as hostname (service name in OpenShift/Compose)
REDIS_HOST = 'database'
REDIS_PORT = 6379

def get_redis_connection():
    """
    Attempt to connect to Redis with retries
    """
    db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    while True:
        try:
            db.ping()
            print("Successfully connected to Redis")
            return db
        except redis.ConnectionError:
            print("Redis not available, retrying in 2 seconds...")
            time.sleep(2)

# Initial connection
db = get_redis_connection()

def stock_worker():
    """
    Background worker to generate stock data
    """
    price = 150.0
    while True:
        try:
            price += random.uniform(-0.5, 0.5)
            timestamp = time.strftime('%H:%M:%S')
            
            # Atomic operations with Redis
            db.lpush('stock_history', f"{timestamp}|{price:.2f}")
            db.ltrim('stock_history', 0, 99)
            time.sleep(2)
        except redis.ConnectionError:
            print("Lost connection to Redis in worker. Reconnecting...")
            # Re-establish connection without killing the thread
            global db
            db = get_redis_connection()

@app.route('/data')
def get_data():
    try:
        data = db.lrange('stock_history', 0, -1)
        # Return formatted data for the chart
        return jsonify([d.split('|') for d in data][::-1])
    except redis.ConnectionError:
        return jsonify([]), 503  # Service Unavailable while reconnecting

if __name__ == '__main__':
    # Start the generator thread
    worker_thread = threading.Thread(target=stock_worker, daemon=True)
    worker_thread.start()
    
    # Run Flask API
    app.run(host='0.0.0.0', port=5000)