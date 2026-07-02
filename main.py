# app.py
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import json
import os

# We set template_folder to '.' so Flask looks for index.html in the same directory as app.py
app = Flask(__name__, template_folder='.')
CORS(app)  

DB_FILE = "orders.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite database on startup."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL,
            items TEXT NOT NULL,  -- JSON string array representing dishes
            total REAL NOT NULL,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Run database setup
init_db()

# ==================== WEB CONTENT ROUTE ====================
@app.route('/')
def home():
    """Serves the front-end user interface to prevent root 404 errors."""
    return render_template('templates/index.html')


# ==================== DATA API ROUTES ====================

# 1. CREATE: Save a brand new order
@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    if not data or 'customer' not in data or 'items' not in data or 'total' not in data:
        return jsonify({"error": "Invalid payload data"}), 400
    
    customer = data['customer']
    items_str = json.dumps(data['items'])
    total = data['total']
    status = data.get('status', 'Pending')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO orders (customer, items, total, status) VALUES (?, ?, ?, ?)",
        (customer, items_str, total, status)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({"id": new_id, "customer": customer, "status": status}), 201


# 2. READ: Get all tracking records
@app.route('/api/orders', methods=['GET'])
def get_orders():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders")
    rows = cursor.fetchall()
    conn.close()

    orders_list = []
    for row in rows:
        orders_list.append({
            "id": row['id'],
            "customer": row['customer'],
            "items": json.loads(row['items']),
            "total": row['total'],
            "status": row['status'],
            "createdAt": row['created_at']
        })
    return jsonify(orders_list)


# 3. UPDATE: Adjust order items, names, or clear state
@app.route('/api/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No payload data supplied"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    if 'customer' in data:
        cursor.execute("UPDATE orders SET customer = ? WHERE id = ?", (data['customer'], order_id))
    if 'items' in data:
        cursor.execute("UPDATE orders SET items = ? WHERE id = ?", (json.dumps(data['items']), order_id))
    if 'total' in data:
        cursor.execute("UPDATE orders SET total = ? WHERE id = ?", (data['total'], order_id))
    if 'status' in data:
        cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (data['status'], order_id))
        
    conn.commit()
    conn.close()
    return jsonify({"message": f"Order {order_id} updated successfully"})


# 4. DELETE: Drop row entirely out of SQLite database file
@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": f"Order {order_id} deleted permanently"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
