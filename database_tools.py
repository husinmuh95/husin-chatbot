import sqlite3
import pandas as pd
from faker import Faker
import random

DB_FILE = "sales_data.db"
fake = Faker()

def init_database():
    """Create and populate the database with a more complex schema and more data."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # DROP TABLES
    c.execute("DROP TABLE IF EXISTS order_details;")
    c.execute("DROP TABLE IF EXISTS sales;")
    c.execute("DROP TABLE IF EXISTS customers;")
    c.execute("DROP TABLE IF EXISTS products;")
    c.execute("DROP TABLE IF EXISTS suppliers;")
    c.execute("DROP TABLE IF EXISTS employees;")

    # CREATE TABLES
    c.execute("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            city TEXT
        );
    """)

    c.execute("""
        CREATE TABLE suppliers (
            supplier_id INTEGER PRIMARY KEY,
            supplier_name TEXT,
            contact_email TEXT
        );
    """)

    c.execute("""
        CREATE TABLE employees (
            employee_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            department TEXT
        );
    """)

    c.execute("""
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT,
            category TEXT,
            price REAL,
            stock_quantity INTEGER,
            supplier_id INTEGER,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
        );
    """)

    c.execute("""
        CREATE TABLE sales (
            sale_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            employee_id INTEGER,
            sale_date TEXT,
            total_amount REAL,
            payment_method TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );
    """)

    c.execute("""
        CREATE TABLE order_details (
            order_detail_id INTEGER PRIMARY KEY,
            sale_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            FOREIGN KEY (sale_id) REFERENCES sales(sale_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );
    """)

    # GENERATE DATA
    print("Generating data...")

    # CUSTOMERS
    customers_data = [(i, fake.first_name(), fake.last_name(), fake.email(), fake.city()) for i in range(1, 501)]
    c.executemany("INSERT INTO customers VALUES (?,?,?,?,?)", customers_data)

    # SUPPLIERS
    suppliers_data = [(i, fake.company(), fake.email()) for i in range(1, 51)]
    c.executemany("INSERT INTO suppliers VALUES (?,?,?)", suppliers_data)

    # EMPLOYEES
    employees_data = [(i, fake.first_name(), fake.last_name(), "Sales") for i in range(1, 21)]
    c.executemany("INSERT INTO employees VALUES (?,?,?,?)", employees_data)

    # PRODUCTS
    categories = ["Electronics", "Apparel", "Books", "Home Goods"]
    products_data = [
        (i, fake.word().capitalize() + " " + fake.word().capitalize(), random.choice(categories), round(random.uniform(10.0, 1000.0), 2), random.randint(0, 500), random.randint(1, 50))
        for i in range(1, 201)
    ]
    c.executemany("INSERT INTO products VALUES (?,?,?,?,?,?)", products_data)

    # SALES ORDER
    sales_data = []
    order_details_data = []
    order_detail_id = 1
    
    for sale_id in range(1, 1001):
        customer_id = random.randint(1, 500)
        employee_id = random.randint(1, 20)
        sale_date = fake.date_between(start_date="-1y", end_date="today")
        payment_method = random.choice(["Credit Card", "Cash", "Bank Transfer"])
        
        num_items = random.randint(1, 5)
        total_amount = 0
        
        for _ in range(num_items):
            product_id = random.randint(1, 200)
            quantity = random.randint(1, 10)
            
            product_price_df = pd.read_sql_query(f"SELECT price FROM products WHERE product_id = {product_id}", conn)
            product_price = product_price_df['price'][0]
            total_amount += product_price * quantity
            
            order_details_data.append((order_detail_id, sale_id, product_id, quantity))
            order_detail_id += 1
            
        sales_data.append((sale_id, customer_id, employee_id, sale_date, round(total_amount, 2), payment_method))

    c.executemany("INSERT INTO sales VALUES (?,?,?,?,?,?)", sales_data)
    c.executemany("INSERT INTO order_details VALUES (?,?,?,?)", order_details_data)

    conn.commit()
    conn.close()
    return "Database initialized with a new, complex schema and more data!"

def text_to_sql(sql_query, st_session_state):
    """Execute a given SQL query and return the results as a string."""
    conn = sqlite3.connect(DB_FILE)
    try:
        df = pd.read_sql_query(sql_query, conn)
        st_session_state.last_sql_result_df = df
        result_string = df.to_string(index=False)
    except Exception as e:
        st_session_state.last_sql_result_df = pd.DataFrame() 
        result_string = f"SQL Execution Error: {e}"
    finally:
        conn.close()
    return result_string

def get_database_info():
    """Get the schema and sample data for all tables."""
    conn = sqlite3.connect(DB_FILE)
    info = []
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for table_name in tables:
        table_name = table_name[0]
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        schema = f"Table: {table_name}\n"
        for col in columns:
            schema += f"- {col[1]} ({col[2]})\n"
        info.append(schema)

        sample_df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 3;", conn)
        info.append(f"Sample data for {table_name}:\n{sample_df.to_string(index=False)}\n")

    conn.close()
    return "\n".join(info)