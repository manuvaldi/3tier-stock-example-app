import redis
import time
import random
from flask import Flask, jsonify
from flask_cors import CORS
import threading
import os # Necessary to read environment variables

app = Flask(__name__)
# Enable CORS for cross-origin requests from the frontend
CORS(app)

# Read Redis host from environment variable or use 'database' as fallback
REDIS_HOST = os.getenv('REDIS_HOST', 'database')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

# Initialize db as None
db = None

def get_redis_connection():
    """
    Establish connection with Redis, retrying until successful
    """
    while True:
        try:
            # Using the host and port from environment variables
            r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
            r.ping()
            print(f"Successfully connected to Redis at {REDIS_HOST}")
            return r
        except redis.ConnectionError:
            print(f"Redis at {REDIS_HOST} not available, retrying in 2 seconds...")
            time.sleep(2)

def stock_worker():
    """
    Background worker to generate stock data even if Redis blips
    """
    global db
    price = 150.0
    while True:
        try:
            if db is None:
                db = get_redis_connection()
            
            price += random.uniform(-0.5, 0.5)
            timestamp = time.strftime('%H:%M:%S')
            
            db.lpush('stock_history', f"{timestamp}|{price:.2f}")
            db.ltrim('stock_history', 0, 99)
            time.sleep(2)
        except Exception as e:
            print(f"Worker encountered an error: {e}. Reconnecting...")
            db = None
            time.sleep(2)

@app.route('/data')
def get_data():
    global db
    try:
        if db is None:
            return jsonify([]), 503
        
        data = db.lrange('stock_history', 0, -1)
        return jsonify([d.split('|') for d in data][::-1])
    except Exception:
        return jsonify([]), 503

if __name__ == '__main__':
    # Initial connection attempt
    db = get_redis_connection()
    
    # Start the generator thread
    threading.Thread(target=stock_worker, daemon=True).start()
    
    # Run Flask on port 5000
    app.run(host='0.0.0.0', port=5000)