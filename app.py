from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

DATABASE = "marketplace.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_name TEXT NOT NULL,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            description TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            buyer_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    conn = get_db()
    products = conn.execute(
        "SELECT * FROM products ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template("index.html", products=products)


@app.route("/add-product", methods=["GET", "POST"])
def add_product():

    if request.method == "POST":
        farmer_name = request.form["farmer_name"]
        name = request.form["name"]
        quantity = int(request.form["quantity"])
        price = float(request.form["price"])
        description = request.form["description"]

        conn = get_db()

        conn.execute("""
            INSERT INTO products
            (farmer_name, name, quantity, price, description)
            VALUES (?, ?, ?, ?, ?)
        """, (
            farmer_name,
            name,
            quantity,
            price,
            description
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("home"))

    return render_template("add_product.html")


@app.route("/products")
def products():
    conn = get_db()

    products = conn.execute(
        "SELECT * FROM products ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template("products.html", products=products)


@app.route("/order/<int:product_id>", methods=["POST"])
def place_order(product_id):

    buyer_name = request.form["buyer_name"]
    quantity = int(request.form["quantity"])

    conn = get_db()

    product = conn.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    if product is None:
        conn.close()
        return "Product not found"

    if quantity <= 0:
        conn.close()
        return "Invalid quantity"

    if quantity > product["quantity"]:
        conn.close()
        return "Not enough quantity available"

    total_price = quantity * product["price"]

    conn.execute("""
        INSERT INTO orders
        (product_id, buyer_name, quantity, total_price)
        VALUES (?, ?, ?, ?)
    """, (
        product_id,
        buyer_name,
        quantity,
        total_price
    ))

    new_quantity = product["quantity"] - quantity

    conn.execute("""
        UPDATE products
        SET quantity = ?
        WHERE id = ?
    """, (
        new_quantity,
        product_id
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("view_orders"))


@app.route("/orders")
def view_orders():

    conn = get_db()

    orders = conn.execute("""
        SELECT
            orders.id,
            orders.buyer_name,
            orders.quantity,
            orders.total_price,
            orders.status,
            products.name AS product_name,
            products.farmer_name
        FROM orders
        JOIN products
        ON orders.product_id = products.id
        ORDER BY orders.id DESC
    """).fetchall()

    conn.close()

    return render_template("orders.html", orders=orders)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)