import redis
import time
import random
import socket
from flask import Flask, jsonify, request
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

def get_db():
    """
    Returns an active Redis connection. 
    If connection is dead, it refreshes it before returning.
    """
    global db
    if db is None:
        db = get_redis_connection()
    return db
    
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
            r = redis.Redis(
                host=target_ip, 
                port=redis_port, 
                socket_connect_timeout=1,
                socket_timeout=1, 
                decode_responses=True
            )
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
    Background worker with aggressive reconnection
    """
    global db
    current_price = 150.0
    print("Worker thread started", flush=True)
    
    while True:
        try:
            # Always get a fresh or validated connection
            active_db = get_db()
            
            # Recovery logic
            last_entry = active_db.lindex('stock_history', 0)
            if last_entry:
                current_price = float(last_entry.split('|')[1])

            current_price += random.uniform(-0.5, 0.5)
            timestamp = time.strftime('%H:%M:%S')
            
            # En stock_worker:
            active_db.lpush('stock_history', f"{timestamp}|{current_price:.2f}")
            active_db.ltrim('stock_history', 0, 5000) # Guardamos hasta 5000 puntos en Redis            

            
            # Log to verify the worker is alive
            print(f"Worker heartbeat: generated {current_price:.2f}", flush=True)
            
            time.sleep(2)
        except Exception as e:
            print(f"Worker loop error: {e}. Resetting connection...", flush=True)
            db = None # Force a new DNS lookup and connection in the next iteration
            time.sleep(2)

@app.route('/data')
def get_data():
    global db
    # Get the 'limit' from URL params, default to 100
    limit_param = request.args.get('limit', 100)
    
    try:
        active_db = get_db()
        
        # If limit is -1, we get all points (up to our 1000 cap in worker)
        # Otherwise, we calculate the range for Redis
        if int(limit_param) == -1:
            end_index = -1
        else:
            end_index = int(limit_param) - 1
            
        data = active_db.lrange('stock_history', 0, end_index)
        # We return the list reversed to show oldest to newest in the chart
        return jsonify([d.split('|') for d in data][::-1])
    
    except (redis.ConnectionError, socket.gaierror):
        print("Connection lost during request. Resetting connection object.", flush=True)
        db = None 
        return jsonify([]), 503
    except Exception as e:
        print(f"[DEBUG] API Error: {e}", flush=True)
        return jsonify([]), 500

if __name__ == '__main__':
    # Initial connection attempt
    db = get_redis_connection()
    
    # Start the generator thread
    threading.Thread(target=stock_worker, daemon=True).start()
    
    # Run Flask on port 5000
    app.run(host='0.0.0.0', port=5000)