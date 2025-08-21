import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, TypedDict
from rich import print as rprint
from rich.panel import Panel
from rich.console import Console
import os
import json
import csv
import dateparser

class OrderItem(TypedDict):
    product_id: int
    quantity: int
    price_per_item: float

class DataManager:
    def __init__(self, db_path: str = "shop_data.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON;")
        self._create_tables()
        rprint(Panel(f"✅ [green]DataManager connected successfully to:[/green] [bold]{self.db_path}[/bold]"))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()
            rprint(Panel("🔌 [yellow]DataManager connection closed.[/yellow]"))

    def _create_tables(self):
        sql_commands = [
            """
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                price REAL NOT NULL,
                stock_quantity INTEGER NOT NULL DEFAULT 0,
                date_added TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact_info TEXT UNIQUE,
                date_added TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                order_date TEXT NOT NULL,
                total_amount REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS order_items (
                order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price_per_item REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (order_id),
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS shipments (
                shipment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL UNIQUE,
                shipping_address TEXT NOT NULL,
                tracking_number TEXT,
                shipment_date TEXT,
                status TEXT NOT NULL DEFAULT 'Awaiting Shipment',
                FOREIGN KEY (order_id) REFERENCES orders (order_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS daily_sales (
                sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                sale_date TEXT NOT NULL,
                quantity_sold INTEGER NOT NULL,
                total_revenue REAL NOT NULL,
                UNIQUE(product_id, sale_date),
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            );
            """
        ]
        with self.conn:
            for command in sql_commands:
                self.cursor.execute(command)

    def add_product(self, name: str, description: str, price: float, stock_quantity: int) -> int:
        with self.conn:
            self.cursor.execute(
                "INSERT INTO products (name, description, price, stock_quantity, date_added) VALUES (?, ?, ?, ?, ?)",
                (name, description, price, stock_quantity, datetime.utcnow().isoformat())
            )
            return self.cursor.lastrowid

    def add_customer(self, name: str, contact_info: str) -> int:
        with self.conn:
            self.cursor.execute("SELECT customer_id FROM customers WHERE contact_info = ?", (contact_info,))
            existing = self.cursor.fetchone()
            if existing:
                return existing['customer_id']
            self.cursor.execute(
                "INSERT INTO customers (name, contact_info, date_added) VALUES (?, ?, ?)",
                (name, contact_info, datetime.utcnow().isoformat())
            )
            return self.cursor.lastrowid

    def create_order_and_shipment(
        self,
        customer_id: int,
        items: List[OrderItem],
        shipping_address: str,
        tracking_number: str = None,
        order_date: datetime = None
    ) -> int:
        with self.conn:
            total_amount = sum(item['quantity'] * item['price_per_item'] for item in items)
            final_order_date = (order_date or datetime.utcnow()).isoformat()
            self.cursor.execute(
                "INSERT INTO orders (customer_id, order_date, total_amount) VALUES (?, ?, ?)",
                (customer_id, final_order_date, total_amount)
            )
            order_id = self.cursor.lastrowid
            self.cursor.executemany(
                "INSERT INTO order_items (order_id, product_id, quantity, price_per_item) VALUES (?, ?, ?, ?)",
                [(order_id, item['product_id'], item['quantity'], item['price_per_item']) for item in items]
            )
            for item in items:
                self.cursor.execute(
                    "UPDATE products SET stock_quantity = stock_quantity - ? WHERE product_id = ?",
                    (item['quantity'], item['product_id'])
                )
            self.cursor.execute(
                "INSERT INTO shipments (order_id, shipping_address, tracking_number, shipment_date) VALUES (?, ?, ?, ?)",
                (order_id, shipping_address, tracking_number, final_order_date)
            )
        return order_id

    def get_all_products(self) -> List[Dict[str, Any]]:
        self.cursor.execute("SELECT * FROM products ORDER BY name")
        return [dict(row) for row in self.cursor.fetchall()]

    def get_all_customers(self) -> List[Dict[str, Any]]:
        self.cursor.execute("SELECT * FROM customers ORDER BY name")
        return [dict(row) for row in self.cursor.fetchall()]

    def get_customer_orders(self, customer_id: int) -> List[Dict[str, Any]]:
        self.cursor.execute(
            "SELECT o.*, s.shipping_address, s.tracking_number, s.status AS shipment_status FROM orders o JOIN shipments s ON o.order_id = s.order_id WHERE o.customer_id = ? ORDER BY o.order_date DESC",
            (customer_id,)
        )
        orders = [dict(row) for row in self.cursor.fetchall()]
        for order in orders:
            self.cursor.execute(
                "SELECT p.name, oi.quantity, oi.price_per_item FROM order_items oi JOIN products p ON oi.product_id = p.product_id WHERE oi.order_id = ?",
                (order['order_id'],)
            )
            order['items'] = [dict(row) for row in self.cursor.fetchall()]
        return orders

    def update_daily_sales(self, for_date: datetime = None):
        target_date = (for_date or datetime.utcnow()).strftime('%Y-%m-%d')
        rprint(f"📈 [cyan]Updating daily sales summary for date:[/cyan] {target_date}")
        with self.conn:
            self.cursor.execute("""
                SELECT oi.product_id, date(o.order_date) as sale_date, SUM(oi.quantity) as total_quantity, SUM(oi.quantity * oi.price_per_item) as total_revenue
                FROM order_items oi JOIN orders o ON oi.order_id = o.order_id
                WHERE sale_date = ? GROUP BY oi.product_id, sale_date
            """, (target_date,))
            sales_for_day = self.cursor.fetchall()
            if not sales_for_day:
                rprint(f"[yellow]No sales recorded for {target_date}.[/yellow]")
                return
            for sale in sales_for_day:
                self.cursor.execute("""
                    INSERT INTO daily_sales (product_id, sale_date, quantity_sold, total_revenue) VALUES (?, ?, ?, ?)
                    ON CONFLICT(product_id, sale_date) DO UPDATE SET quantity_sold = excluded.quantity_sold, total_revenue = excluded.total_revenue;
                """, (sale['product_id'], sale['sale_date'], sale['total_quantity'], sale['total_revenue']))
            rprint(f"[green]✅ Daily sales updated for {len(sales_for_day)} product(s).[/green]")

    def export_sales_to_csv(self, file_path: str) -> str:
        self.cursor.execute("""
            SELECT ds.sale_date, p.name as product_name, ds.quantity_sold, ds.total_revenue
            FROM daily_sales ds JOIN products p ON ds.product_id = p.product_id
            ORDER BY ds.sale_date, p.name
        """)
        sales_data = self.cursor.fetchall()
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['date', 'product_name', 'quantity_sold', 'daily_revenue'])
            for row in sales_data:
                writer.writerow([row['sale_date'], row['product_name'], row['quantity_sold'], row['total_revenue']])
        return f"Successfully exported detailed sales data to {file_path}"

    def get_sales_on_date(self, date_str: str) -> List[Dict[str, Any]]:
        target_date = dateparser.parse(date_str, settings={'PREFER_DATES_FROM': 'past'})
        if not target_date:
            raise ValueError(f"Could not parse the date: '{date_str}'")
        target_date_iso = target_date.strftime('%Y-%m-%d')
        self.cursor.execute("""
            SELECT p.name as product_name, ds.quantity_sold, ds.total_revenue
            FROM daily_sales ds JOIN products p ON ds.product_id = p.product_id
            WHERE ds.sale_date = ?
        """, (target_date_iso,))
        return [dict(row) for row in self.cursor.fetchall()]

    def get_product_sales_on_date(self, product_name: str, date_str: str) -> Dict[str, Any]:
        target_date = dateparser.parse(date_str, settings={'PREFER_DATES_FROM': 'past'})
        if not target_date:
            raise ValueError(f"Could not parse the date: '{date_str}'")
        target_date_iso = target_date.strftime('%Y-%m-%d')
        self.cursor.execute("""
            SELECT p.name as product_name, ds.quantity_sold, ds.total_revenue
            FROM daily_sales ds JOIN products p ON ds.product_id = p.product_id
            WHERE ds.sale_date = ? AND LOWER(p.name) = LOWER(?)
        """, (target_date_iso, product_name))
        result = self.cursor.fetchone()
        return dict(result) if result else None

    def get_sales_for_date_range(self, start_date_str: str, end_date_str: str) -> List[Dict[str, Any]]:
        start_date = dateparser.parse(start_date_str, settings={'PREFER_DATES_FROM': 'past'})
        end_date = dateparser.parse(end_date_str, settings={'PREFER_DATES_FROM': 'future'})
        if not start_date or not end_date:
            raise ValueError("Could not parse date strings.")
        self.cursor.execute(
            "SELECT sale_date, product_id, quantity_sold, total_revenue FROM daily_sales WHERE sale_date BETWEEN ? AND ? ORDER BY sale_date",
            (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        )
        return [dict(row) for row in self.cursor.fetchall()]

if __name__ == '__main__':
    db_file = "test_shop_data.db"
    if os.path.exists(db_file):
        os.remove(db_file)

    console = Console()
    console.print(Panel("🚀 [bold green]Starting DataManager Full Test Suite[/bold green] 🚀"))
    with DataManager(db_file) as db:
        console.rule("[bold]Step 1: Setup Products & Customers[/bold]")
        p1_id = db.add_product("Leather Wallet", "Hand-stitched", 49.99, 100)
        p2_id = db.add_product("Ceramic Mug", "Hand-thrown", 24.99, 100)
        c1_id = db.add_customer("Alice", "alice@example.com")
        console.print("✅ Products and customers created.")
        
        console.rule("[bold]Step 2: Simulate Sales for 'Yesterday' & 'Today'[/bold]")
        yesterday = datetime.utcnow() - timedelta(days=1)
        db.create_order_and_shipment(c1_id, [{"product_id": p1_id, "quantity": 2, "price_per_item": 49.99}], "Addr 1", order_date=yesterday)
        db.create_order_and_shipment(c1_id, [{"product_id": p2_id, "quantity": 5, "price_per_item": 24.99}], "Addr 2", order_date=yesterday)
        db.update_daily_sales(for_date=yesterday)
        
        today = datetime.utcnow()
        db.create_order_and_shipment(c1_id, [{"product_id": p1_id, "quantity": 3, "price_per_item": 49.99}], "Addr 3", order_date=today)
        db.update_daily_sales(for_date=today)
        console.print("✅ Sales logged and summaries updated.")
        
        console.rule("[bold]Step 3: Export Detailed Sales CSV[/bold]")
        csv_path = "test_sales_data_detailed.csv"
        export_status = db.export_sales_to_csv(csv_path)
        console.print(f"✅ {export_status}")
        
        console.rule("[bold]Step 4: Testing Specific Date Sales Retrieval[/bold]")
        yesterday_sales = db.get_sales_on_date("yesterday")
        console.print(Panel(json.dumps(yesterday_sales, indent=2), title="Sales for 'yesterday'"))
        
        wallet_sales_today = db.get_product_sales_on_date("leather wallet", "today")
        console.print(Panel(json.dumps(wallet_sales_today, indent=2), title="Leather Wallet Sales for 'today' (case-insensitive)"))
        
        console.rule("[bold]Step 5: Verifying General Data Retrieval[/bold]")
        all_customers = db.get_all_customers()
        console.print(Panel(json.dumps(all_customers, indent=2), title="👥 All Customers"))
        
        updated_products = db.get_all_products()
        console.print(Panel(json.dumps(updated_products, indent=2), title="📦 Final Product Inventory"))
        
        alice_orders = db.get_customer_orders(c1_id)
        console.print(Panel(json.dumps(alice_orders, indent=2), title=f"📄 Alice's Full Order History"))

    console.print(Panel("🏁 [bold green]DataManager Test Suite Finished Successfully[/bold green] 🏁"))
