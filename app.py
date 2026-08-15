from flask import Flask, render_template, request, redirect,session
import sqlite3

app = Flask(__name__)
app.secret_key = "restaurant_secret_key"
# ==========================
# DATABASE CONNECTION
# ==========================

def get_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# ==========================
# CREATE DATABASE
# ==========================

def create_database():

    conn = get_connection()

    # Menu Table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS menu(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        item_name TEXT NOT NULL,

        category TEXT NOT NULL,

        price REAL NOT NULL

    )
    """)

    # Orders Table
 # Orders Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        customer_name TEXT NOT NULL,

        phone TEXT NOT NULL,

        food_name TEXT NOT NULL,

        category TEXT NOT NULL,

        price REAL NOT NULL,

        quantity INTEGER NOT NULL,

        total REAL NOT NULL,

        order_date TEXT NOT NULL,

        order_time TEXT NOT NULL

)
""")    

# Bill History Table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bill_history(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        customer_name TEXT NOT NULL,

        phone TEXT NOT NULL,

        food_name TEXT NOT NULL,

        category TEXT NOT NULL,

        price REAL NOT NULL,

        quantity INTEGER NOT NULL,

       total REAL NOT NULL,

       order_date TEXT NOT NULL,

       order_time TEXT NOT NULL

)
""")


    conn.commit()
    conn.close()


create_database()

# ==========================
# HOME
# ==========================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================
# DASHBOARD
# ==========================

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# ==========================
# MENU PAGE
# ==========================

@app.route("/menu")
def menu():

    conn = get_connection()

    menu = conn.execute(
        "SELECT * FROM menu ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "menu.html",
        menu=menu
    )


# ==========================
# ADD MENU
# ==========================

@app.route("/add_menu", methods=["POST"])
def add_menu():

    item_name = request.form["item_name"]
    category = request.form["category"]
    price = request.form["price"]

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO menu
        (item_name, category, price)
        VALUES (?, ?, ?)
        """,
        (item_name, category, price)
    )

    conn.commit()
    conn.close()

    return redirect("/menu")


# ==========================
# DELETE MENU
# ==========================

@app.route("/delete_menu/<int:id>")
def delete_menu(id):

    conn = get_connection()

    conn.execute(
        "DELETE FROM menu WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/menu")
# ==========================
# ORDER PAGE
# ==========================

@app.route("/order")
def order():

    conn = get_connection()

    # Menu items for dropdown
    menu = conn.execute(
        "SELECT * FROM menu ORDER BY item_name"
    ).fetchall()

    # Order items
    orders = conn.execute(
        "SELECT * FROM orders ORDER BY id DESC"
    ).fetchall()

    # Grand Total
    total = conn.execute(
        "SELECT SUM(price * quantity) FROM orders"
    ).fetchone()[0]

    if total is None:
        total = 0

    conn.close()
    
    return render_template(
        "order.html",
        menu=menu,
        orders=orders,
        grand_total=total,
        customer_name=session.get("customer_name", ""),
        phone=session.get("phone", "")
    )

# ==========================
# ADD ORDER
# ==========================


from datetime import datetime

@app.route("/add_order", methods=["POST"])
def add_order():

    customer_name = request.form["customer_name"]
    phone = request.form["phone"]
    food_name = request.form["food_name"]
    category = request.form["category"]

    price = float(request.form["price"])
    quantity = int(request.form["quantity"])

    total = price * quantity

    now = datetime.now()

    order_date = now.strftime("%d-%m-%Y")
    order_time = now.strftime("%I:%M %p")

    session["customer_name"] = customer_name
    session["phone"] = phone

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO orders
        (
            customer_name,
            phone,
            food_name,
            category,
            price,
            quantity,
            total,
            order_date,
            order_time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            customer_name,
            phone,
            food_name,
            category,
            price,
            quantity,
            total,
            order_date,
            order_time
        )
    )

    conn.commit()
    conn.close()

    return redirect("/order")

# ==========================
# BILL PAGE
# ==========================
from datetime import datetime
@app.route("/bill")
def bill():

    conn = get_connection()

    orders = conn.execute(
        "SELECT * FROM orders"
    ).fetchall()

    total = conn.execute(
        "SELECT SUM(price * quantity) FROM orders"
    ).fetchone()[0]

    if total is None:
        total = 0

    # Current Date and Time
    now = datetime.now()

    current_date = now.strftime("%d-%m-%Y")
    current_time = now.strftime("%I:%M %p")

    conn.close()

    return render_template(
        "bill.html",
         orders=orders,
        grand_total=total,
        current_date=current_date,
        current_time=current_time,
        customer_name=session.get("customer_name", ""),
        phone=session.get("phone", "")
)
# ==========================
# CUSTOMERS
# ==========================

@app.route("/customers")
def customers():

    conn = get_connection()

    customers = conn.execute("""
        SELECT
            customer_name,
            phone,
            COUNT(*) AS total_orders,
            SUM(total) AS total_spent,
            MAX(order_date) AS last_visit
        FROM bill_history
        GROUP BY customer_name, phone
        ORDER BY customer_name ASC
    """).fetchall()

    conn.close()

    return render_template(
        "customers.html",
        customers=customers
    )


# ==========================
# REPORTS
# ==========================
@app.route("/reports")
def reports():

    conn = get_connection()

    # Total Sales
    
    total_sales = conn.execute("""
        SELECT IFNULL(SUM(total),0)
        FROM bill_history
    """).fetchone()[0]
    # Total Orders
    total_orders = conn.execute("""
       SELECT COUNT(*)
       FROM bill_history
    """).fetchone()[0]

    # Total Items Sold
    total_items = conn.execute("""
    SELECT IFNULL(SUM(quantity),0)
    FROM bill_history
    """).fetchone()[0]

    # Average Order Value
    average_order = 0

    if total_orders > 0:
        average_order = round(total_sales / total_orders, 2)

    # Top Selling Items
    top_items = conn.execute("""
        SELECT
            food_name,
            SUM(quantity) AS total_qty,
            SUM(total) AS total_sales
        FROM bill_history
        GROUP BY food_name
        ORDER BY total_qty DESC
        LIMIT 5
    """).fetchall()

    conn.close()

    return render_template(
        "reports.html",
        total_sales=total_sales,
        total_orders=total_orders,
        total_items=total_items,
        average_order=average_order,
        top_items=top_items
    )


# ==========================
# HISTORY
# ==========================

@app.route("/history")
def history():
    return render_template("history.html")


# ==========================
# LOGIN
# ==========================

@app.route("/login")
def login():
    return render_template("login.html")


# ==========================
# REGISTER
# ==========================

@app.route("/register")
def register():
    return render_template("register.html")


# ==========================
# RUN APP
# ==========================


@app.route("/finish_bill")
def finish_bill():

    conn = get_connection()

    # Copy all current orders to bill_history
    conn.execute("""
        INSERT INTO bill_history
        (
            customer_name,
            phone,
            food_name,
            category,
            price,
            quantity,
            total,
            order_date,
            order_time
        )
        SELECT
            customer_name,
            phone,
            food_name,
            category,
            price,
            quantity,
            total,
            order_date,
            order_time
        FROM orders
    """)

    # Clear current orders
    conn.execute("DELETE FROM orders")

    conn.commit()
    conn.close()

    session.pop("customer_name", None)
    session.pop("phone", None)

    return redirect("/order")
if __name__ == "__main__":
    app.run(debug=True)
