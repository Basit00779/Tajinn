from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import json
import os

app = Flask(__name__)
CORS(app)

DB_FILE = "orders.db"


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer TEXT NOT NULL,
        items TEXT NOT NULL,
        total REAL NOT NULL,
        status TEXT DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


init_db()


@app.route("/")
def home():
    return render_template("templates/index.html")


@app.route("/api/orders", methods=["POST"])
def create_order():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid Data"}), 400

    customer = data.get("customer")
    items = data.get("items")
    total = data.get("total")
    status = data.get("status", "Pending")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO orders(customer,items,total,status)
        VALUES(?,?,?,?)
        """,
        (
            customer,
            json.dumps(items),
            total,
            status,
        ),
    )

    conn.commit()

    new_id = cur.lastrowid

    conn.close()

    return jsonify({
        "id": new_id,
        "message": "Order Created"
    }), 201


@app.route("/api/orders", methods=["GET"])
def get_orders():

    conn = get_db_connection()
    cur = conn.cursor()

    rows = cur.execute(
        "SELECT * FROM orders ORDER BY id DESC"
    ).fetchall()

    conn.close()

    orders = []

    for row in rows:
        orders.append({
            "id": row["id"],
            "customer": row["customer"],
            "items": json.loads(row["items"]),
            "total": row["total"],
            "status": row["status"],
            "createdAt": row["created_at"]
        })

    return jsonify(orders)


@app.route("/api/orders/<int:id>", methods=["PUT"])
def update_order(id):

    data = request.get_json()

    conn = get_db_connection()
    cur = conn.cursor()

    if "customer" in data:
        cur.execute(
            "UPDATE orders SET customer=? WHERE id=?",
            (data["customer"], id),
        )

    if "items" in data:
        cur.execute(
            "UPDATE orders SET items=? WHERE id=?",
            (
                json.dumps(data["items"]),
                id,
            ),
        )

    if "total" in data:
        cur.execute(
            "UPDATE orders SET total=? WHERE id=?",
            (
                data["total"],
                id,
            ),
        )

    if "status" in data:
        cur.execute(
            "UPDATE orders SET status=? WHERE id=?",
            (
                data["status"],
                id,
            ),
        )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Order Updated"
    })


@app.route("/api/orders/<int:id>", methods=["DELETE"])
def delete_order(id):

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM orders WHERE id=?",
        (id,),
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Order Deleted"
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(
        host="0.0.0.0",
        port=port
    )
