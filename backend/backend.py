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
    global db
    redis_host = os.getenv('REDIS_HOST', 'database')
    redis_port = int(os.getenv('REDIS_PORT', 6379))

    while True:
        try:
            # 1. Intentamos resolver la IP para descartar problemas de DNS
            target_ip = socket.gethostbyname(redis_host)
            print(f"DEBUG: DNS Resolved {redis_host} -> {target_ip}", flush=True)

            # 2. Intentamos conectar
            r = redis.Redis(host=target_ip, port=redis_port, socket_connect_timeout=1, decode_responses=True)
            r.ping()
            
            print(f"DEBUG: Connection SUCCESS to {target_ip}", flush=True)
            return r
        except socket.gaierror:
            print(f"DEBUG: DNS ERROR - Cannot resolve {redis_host}", flush=True)
        except redis.ConnectionError as e:
            print(f"DEBUG: REDIS ERROR - Connection refused at {redis_host}: {e}", flush=True)
        except Exception as e:
            print(f"DEBUG: UNKNOWN ERROR: {type(e).__name__}: {e}", flush=True)
        
        time.sleep(2)

def stock_worker():
    """
    Background worker to generate stock data, recovering state from Redis
    """
    global db
    # Default starting price if Redis is empty
    current_price = 150.0 
    
    while True:
        try:
            if db is None:
                db = get_redis_connection()
            
            # 1. RECOVERY LOGIC: Try to get the last known price from Redis
            last_entry = db.lindex('stock_history', 0) # Get the most recent item
            if last_entry:
                # last_entry is "HH:MM:SS|PRICE", we split and take the price
                current_price = float(last_entry.split('|')[1])
            
            # 2. GENERATE NEW DATA
            current_price += random.uniform(-0.5, 0.5)
            timestamp = time.strftime('%H:%M:%S')
            
            # 3. SAVE
            db.lpush('stock_history', f"{timestamp}|{current_price:.2f}")
            db.ltrim('stock_history', 0, 99)
            
            time.sleep(2)
            
        except Exception as e:
            print(f"Worker encountered an error: {e}. Reconnecting...", flush=True)
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