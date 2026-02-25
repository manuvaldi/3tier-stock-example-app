import redis
import time
import random
from flask import Flask, jsonify
from flask_cors import CORS
import threading

app = Flask(__name__)
CORS(app)
db = redis.Redis(host='database', port=6379, decode_responses=True)

def stock_worker():
    price = 150.0
    while True:
        price += random.uniform(-0.5, 0.5)
        timestamp = time.strftime('%H:%M:%S')
        db.lpush('stock_history', f"{timestamp}|{price:.2f}")
        db.ltrim('stock_history', 0, 99) # Mantiene los últimos 100
        time.sleep(2)

@app.route('/data')
def get_data():
    data = db.lrange('stock_history', 0, -1)
    return jsonify([d.split('|') for d in data][::-1])

if __name__ == '__main__':
    threading.Thread(target=stock_worker, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)