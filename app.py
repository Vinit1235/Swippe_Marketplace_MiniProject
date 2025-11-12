# app.py - Swippe Quick Commerce Platform
# Complete E-Commerce Application with 27,555+ Products

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from functools import wraps
from datetime import datetime
import sqlite3
import bcrypt
import os
import pandas as pd

# Database Adapter (PostgreSQL or SQLite)
from db_adapter import get_db_connection

# RAG Chatbot - Try Gemini version first, then fallback to intelligent/standard
try:
    from rag_products_gemini import get_gemini_rag_instance
    RAG_GEMINI = get_gemini_rag_instance()
    RAG_AVAILABLE = True
    RAG_TYPE = 'gemini'
    print("✅ RAG System: Gemini AI Mode (v3.0 - FAISS + Gemini)")
except Exception as e:
    print(f"⚠️  Gemini RAG failed: {str(e)[:100]}")
    try:
        from rag_chat_intelligent import rag_query_intelligent as rag_query
        RAG_AVAILABLE = True
        RAG_TYPE = 'intelligent'
        print("✅ RAG System: Intelligent Mode (v2.0)")
    except Exception as e2:
        print(f"⚠️  RAG Intelligent mode failed: {str(e2)[:100]}")
        try:
            from rag_chat_with_db import rag_query
            RAG_AVAILABLE = True
            RAG_TYPE = 'standard'
            print("✅ RAG System: Standard Mode (v1.0)")
        except Exception:
            RAG_AVAILABLE = False
            RAG_TYPE = None
            print("⚠️  RAG System: Disabled - App will work without AI chatbot")

# Email System - Try modern template first, fallback to classic
try:
    from email_invoice_modern import send_modern_invoice_email as send_invoice_email
    EMAIL_AVAILABLE = True
    print("✅ Email System: Enabled (Modern Beautiful Template)")
except ImportError:
    try:
        from email_invoice import send_invoice_email
        EMAIL_AVAILABLE = True
        print("✅ Email System: Enabled (Classic Template)")
    except ImportError:
        EMAIL_AVAILABLE = False
        print("⚠️  Email System: Disabled")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'swippe-secret-2025'
app.config['DATABASE'] = 'instance/swippe.db'
app.config['WTF_CSRF_ENABLED'] = True
os.makedirs('instance', exist_ok=True)

# Flask-WTF Forms
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log in')

class SignupForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Sign up')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT role FROM users WHERE id = ?', (session['user_id'],))
        result = cursor.fetchone()
        conn.close()
        if not result or result[0] != 'admin':
            return redirect(url_for('products_home'))
        return f(*args, **kwargs)
    return decorated_function

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, email TEXT UNIQUE, password_hash TEXT,
        role TEXT DEFAULT 'user', created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute("PRAGMA table_info(users)")
    if 'role' not in [c[1] for c in cursor.fetchall()]:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY, product TEXT, category TEXT, sub_category TEXT,
        brand TEXT, sale_price REAL, market_price REAL, type TEXT, rating REAL, image_url TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY, user_id INTEGER, product_id INTEGER, quantity INTEGER,
        total_price REAL, status TEXT DEFAULT 'pending', ordered_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS addresses (
        id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, phone TEXT,
        address_line1 TEXT, address_line2 TEXT, city TEXT, state TEXT, pincode TEXT,
        landmark TEXT, latitude REAL, longitude REAL, is_default INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # Enhanced Routine Deliveries Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS routine_deliveries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        frequency TEXT NOT NULL CHECK(frequency IN ('daily', 'weekly', 'biweekly', 'monthly', 'custom')),
        delivery_day TEXT,
        delivery_time TEXT DEFAULT '09:00',
        next_delivery_date DATE NOT NULL,
        is_active INTEGER DEFAULT 1,
        is_paused INTEGER DEFAULT 0,
        auto_order INTEGER DEFAULT 1,
        max_orders INTEGER,
        orders_completed INTEGER DEFAULT 0,
        price_locked REAL,
        notification_enabled INTEGER DEFAULT 1,
        skip_holidays INTEGER DEFAULT 1,
        custom_interval_days INTEGER,
        start_date DATE DEFAULT CURRENT_DATE,
        end_date DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_delivery_date DATE,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
    )''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_routine_user ON routine_deliveries(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_routine_next_delivery ON routine_deliveries(next_delivery_date)')
    conn.commit()
    conn.close()
    print("[OK] Database initialized")

def ensure_sample_products():
    """Import products data and ensure primary key integrity for foreign key constraints."""
    import pandas as pd

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
    has_products_table = cursor.fetchone() is not None
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products_backup'")
    has_products_backup = cursor.fetchone() is not None

    if not has_products_table and has_products_backup:
        print("⚠️  Rescuing products table from backup...")
        cursor.execute('ALTER TABLE products_backup RENAME TO products')
        conn.commit()
        has_products_table = True
        has_products_backup = False

    if not has_products_table:
        print("⚠️  Products table missing. Recreating base schema...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                product TEXT,
                category TEXT,
                sub_category TEXT,
                brand TEXT,
                sale_price REAL,
                market_price REAL,
                type TEXT,
                rating REAL,
                image_url TEXT
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand)')
        conn.commit()
        has_products_table = True

    expected_columns = [
        'id', 'product', 'category', 'sub_category', 'brand',
        'sale_price', 'market_price', 'type', 'rating', 'image_url'
    ]

    cursor.execute("PRAGMA table_info(products)")
    schema_info = cursor.fetchall()
    product_columns = [col[1] for col in schema_info]
    has_primary_key = any(col[1] == 'id' and col[5] == 1 for col in schema_info)

    if schema_info and not has_primary_key:
        print("⚠️  Products table missing primary key. Rebuilding for foreign key integrity...")
        cursor.execute('ALTER TABLE products RENAME TO products_backup')
        cursor.execute('''
            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                product TEXT,
                category TEXT,
                sub_category TEXT,
                brand TEXT,
                sale_price REAL,
                market_price REAL,
                type TEXT,
                rating REAL,
                image_url TEXT
            )
        ''')
        select_columns = []
        for col in expected_columns:
            if col in product_columns:
                select_columns.append(col)
            else:
                select_columns.append(f"NULL AS {col}")
        cursor.execute(f'''
            INSERT OR REPLACE INTO products ({', '.join(expected_columns)})
            SELECT {', '.join(select_columns)}
            FROM products_backup
        ''')
        cursor.execute('DROP TABLE products_backup')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand)')
        conn.commit()
        cursor.execute("PRAGMA table_info(products)")
        schema_info = cursor.fetchall()
        product_columns = [col[1] for col in schema_info]
        print("✅ Products table primary key restored")

    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]

    if count == 0:
        print("📦 No products found, importing from products.xlsx...")
        try:
            excel_path = os.path.join(os.path.dirname(__file__), 'products.xlsx')

            if not os.path.exists(excel_path):
                print(f"❌ products.xlsx not found at {excel_path}")
                print("⚠️  Skipping product import. Please add products.xlsx to repository.")
                conn.close()
                return

            print(f"📂 Reading {excel_path}...")
            df = pd.read_excel(excel_path)
            print(f"✅ Loaded {len(df)} products from Excel")

            if 'index' in df.columns and 'id' not in df.columns:
                df = df.rename(columns={'index': 'id'})

            for column in expected_columns:
                if column not in df.columns:
                    if column == 'id':
                        df[column] = range(1, len(df) + 1)
                    else:
                        df[column] = None

            df = df[expected_columns]

            payload = []
            for row in df.itertuples(index=False):
                payload.append((
                    int(getattr(row, 'id')) if pd.notna(getattr(row, 'id')) else None,
                    None if pd.isna(getattr(row, 'product')) else str(getattr(row, 'product')),
                    None if pd.isna(getattr(row, 'category')) else str(getattr(row, 'category')),
                    None if pd.isna(getattr(row, 'sub_category')) else str(getattr(row, 'sub_category')),
                    None if pd.isna(getattr(row, 'brand')) else str(getattr(row, 'brand')),
                    None if pd.isna(getattr(row, 'sale_price')) else float(getattr(row, 'sale_price')),
                    None if pd.isna(getattr(row, 'market_price')) else float(getattr(row, 'market_price')),
                    None if pd.isna(getattr(row, 'type')) else str(getattr(row, 'type')),
                    None if pd.isna(getattr(row, 'rating')) else float(getattr(row, 'rating')),
                    None if pd.isna(getattr(row, 'image_url')) else str(getattr(row, 'image_url'))
                ))

            cursor.executemany('''
                INSERT OR REPLACE INTO products
                (id, product, category, sub_category, brand, sale_price, market_price, type, rating, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', payload)
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand)')
            conn.commit()

            cursor.execute("SELECT COUNT(*) FROM products")
            final_count = cursor.fetchone()[0]
            print(f"✅ Successfully imported {final_count} products!")

        except Exception as e:
            conn.rollback()
            print(f"❌ Failed to import products: {e}")
            print("⚠️  App will continue but products table will be empty.")
    else:
        print(f"📊 Database already has {count} products")

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products_backup'")
    if cursor.fetchone():
        print("ℹ️  Dropping leftover products_backup table")
        cursor.execute('DROP TABLE products_backup')
        conn.commit()

    conn.close()


def ensure_orders_schema():
    """Ensure orders table references products correctly and contains modern columns."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'")
    has_orders = cursor.fetchone() is not None

    desired_columns = [
        'id', 'user_id', 'product_id', 'quantity', 'total_price',
        'status', 'ordered_at', 'delivery_instructions',
        'payment_method', 'address_label', 'delivery_slot_minutes'
    ]

    create_orders_sql = '''
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            ordered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            delivery_instructions TEXT,
            payment_method TEXT,
            address_label TEXT,
            delivery_slot_minutes INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
        )
    '''

    def create_fresh_orders_table():
        cursor.execute(create_orders_sql)
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_product_id ON orders(product_id)')
        conn.commit()

    if not has_orders:
        print("⚠️  Orders table missing. Creating new schema...")
        create_fresh_orders_table()
        conn.close()
        return

    cursor.execute("PRAGMA table_info(orders)")
    order_schema = cursor.fetchall()
    order_columns = [col[1] for col in order_schema]

    cursor.execute("PRAGMA foreign_key_list('orders')")
    fk_info = cursor.fetchall()
    fk_targets = {fk[2] for fk in fk_info}

    needs_rebuild = False
    if any(target not in {'users', 'products'} for target in fk_targets):
        needs_rebuild = True
    if 'products_backup' in fk_targets or 'products_backup' in order_columns:
        needs_rebuild = True
    if any(col not in order_columns for col in desired_columns):
        needs_rebuild = True

    if not needs_rebuild:
        conn.close()
        return

    print("⚠️  Rebuilding orders table to restore foreign keys and columns...")
    cursor.execute('ALTER TABLE orders RENAME TO orders_backup')
    create_fresh_orders_table()

    backup_columns = []
    cursor.execute("PRAGMA table_info(orders_backup)")
    backup_schema = cursor.fetchall()
    backup_column_names = [col[1] for col in backup_schema]

    select_clauses = []
    insert_columns = []
    for column in desired_columns:
        insert_columns.append(column)
        if column in backup_column_names:
            if column == 'total_price':
                select_clauses.append('COALESCE(total_price, 0)')
            elif column == 'quantity':
                select_clauses.append('COALESCE(quantity, 1)')
            elif column == 'status':
                select_clauses.append("COALESCE(status, 'pending')")
            else:
                select_clauses.append(column)
        elif column == 'status':
            select_clauses.append("'pending'")
        elif column == 'quantity':
            select_clauses.append('1')
        elif column == 'total_price':
            select_clauses.append('0')
        else:
            select_clauses.append('NULL')

    cursor.execute(f'''
        INSERT INTO orders ({', '.join(insert_columns)})
        SELECT {', '.join(select_clauses)}
        FROM orders_backup
        WHERE user_id IS NOT NULL AND product_id IS NOT NULL
    ''')
    cursor.execute('DROP TABLE orders_backup')
    conn.commit()
    conn.close()

init_db()
ensure_sample_products()
ensure_orders_schema()

@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('products_home'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    signup_form = SignupForm()
    mode = request.args.get('mode', 'login')
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, password_hash, role FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
            session['user_id'] = user[0]
            session['email'] = email
            session['role'] = user[2]
            if session['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('loading'))
        flash('Invalid credentials', 'error')
    return render_template('auth/login.html', login_form=login_form, signup_form=signup_form, mode=mode)

@app.route('/register', methods=['GET', 'POST'])
def register():
    login_form = LoginForm()
    signup_form = SignupForm()
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)', (email, password_hash, 'user'))
            conn.commit()
            conn.close()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already exists', 'error')
            return redirect(url_for('login', mode='signup'))
    return render_template('auth/login.html', login_form=login_form, signup_form=signup_form, mode='signup')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/loading')
@login_required
def loading():
    redirect_url = url_for('products_home')
    return render_template('loading.html', redirect_url=redirect_url)

@app.route('/products')
@login_required
def products_home():
    conn = get_db_connection()
    cursor = conn.cursor()
    query = 'SELECT * FROM products WHERE 1=1'
    params = []
    if request.args.get('category'):
        query += ' AND category = ?'
        params.append(request.args['category'])
    if request.args.get('brand'):
        query += ' AND brand = ?'
        params.append(request.args['brand'])
    if request.args.get('search'):
        query += ' AND (product LIKE ? OR brand LIKE ?)'
        params.extend([f"%{request.args['search']}%", f"%{request.args['search']}%"])
    query += ' ORDER BY rating DESC LIMIT 100'
    cursor.execute(query, params)
    products = cursor.fetchall()
    cursor.execute('SELECT DISTINCT category FROM products')
    categories = [r[0] for r in cursor.fetchall()]
    cursor.execute('SELECT DISTINCT brand FROM products LIMIT 50')
    brands = [r[0] for r in cursor.fetchall()]
    conn.close()
    products_list = [{'id': p[0], 'product': p[1], 'category': p[2], 'sub_category': p[3],
                      'brand': p[4], 'sale_price': p[5], 'market_price': p[6], 'type': p[7],
                      'rating': p[8], 'image_url': None} for p in products]  # Images disabled for LinkedIn demo
    return render_template('products/home.html', products=products_list, categories=categories, brands=brands)

@app.route('/products/<int:product_id>')
@login_required
def product_detail(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    if not product:
        conn.close()
        return redirect(url_for('products_home'))
    cursor.execute('SELECT * FROM products WHERE category = ? AND id != ? LIMIT 8', (product[2], product_id))
    related = cursor.fetchall()
    conn.close()
    product_dict = {'id': product[0], 'product': product[1], 'category': product[2], 'sub_category': product[3],
                    'brand': product[4], 'sale_price': product[5], 'market_price': product[6], 'type': product[7],
                    'rating': product[8], 'image_url': None}  # Images disabled for LinkedIn demo
    related_list = [{'id': p[0], 'product': p[1], 'brand': p[4], 'sale_price': p[5],
                     'rating': p[8], 'image_url': None} for p in related]  # Images disabled
    return render_template('products/detail.html', product=product_dict, related_products=related_list)

@app.route('/api/search')
@login_required
def api_search():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify({'products': []})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Improved search: search in product name, brand, category, and sub_category
    search_query = '''
        SELECT id, product, brand, category, sale_price, rating, image_url 
        FROM products 
        WHERE product LIKE ? 
           OR brand LIKE ? 
           OR category LIKE ? 
           OR sub_category LIKE ?
        ORDER BY 
            CASE 
                WHEN LOWER(product) = LOWER(?) THEN 1
                WHEN LOWER(product) LIKE LOWER(?) THEN 2
                WHEN LOWER(brand) = LOWER(?) THEN 3
                WHEN LOWER(brand) LIKE LOWER(?) THEN 4
                ELSE 5
            END
        LIMIT 50
    '''
    
    search_pattern = f'%{query}%'
    cursor.execute(search_query, (
        search_pattern, search_pattern, search_pattern, search_pattern,
        query, f'{query}%', query, f'{query}%'
    ))
    results = cursor.fetchall()
    conn.close()
    
    products = [{
        'id': r[0], 
        'product': r[1], 
        'brand': r[2], 
        'category': r[3],
        'sale_price': r[4], 
        'rating': r[5], 
        'image_url': None  # Images disabled for LinkedIn demo
    } for r in results]
    
    return jsonify({'products': products})

@app.route('/cart')
@login_required
def cart():
    return render_template('cart.html')

@app.route('/checkout')
@login_required
def checkout():
    return render_template('checkout.html')

@app.route('/api/order', methods=['POST'])
@login_required
def create_order():
    data = request.json
    print(f"[DEBUG] Received order data: {data}")
    # Accept both 'cart' and 'items' keys for compatibility
    cart_items = data.get('cart', data.get('items', []))
    print(f"[DEBUG] Cart items count: {len(cart_items)}")
    if not cart_items:
        return jsonify({'success': False, 'message': 'Cart is empty'}), 400
    delivery_instructions = data.get('delivery_instructions')
    payment_method = data.get('payment_method')
    address_label = data.get('address') or data.get('address_label')
    delivery_slot_minutes = data.get('delivery_slot_minutes')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for item in cart_items:
            print(f"[DEBUG] Inserting order: product_id={item.get('id')}, quantity={item.get('quantity')}")
            # Handle both 'price' and 'sale_price' keys
            price = item.get('sale_price', item.get('price', 0))
            cursor.execute('''
                INSERT INTO orders (
                    user_id, product_id, quantity, total_price, status,
                    delivery_instructions, payment_method, address_label, delivery_slot_minutes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session['user_id'],
                item['id'],
                item['quantity'],
                price * item['quantity'],
                'pending',
                delivery_instructions,
                payment_method,
                address_label,
                delivery_slot_minutes
            ))
        conn.commit()
        order_id = cursor.lastrowid
        print(f"[OK] Order created: #{order_id}")
        if EMAIL_AVAILABLE:
            try:
                send_invoice_email(order_id, session.get('email'))
                print(f"[OK] Invoice sent to {session.get('email')}")
            except Exception as e:
                print(f"[WARNING] Email failed: {e}")
        conn.close()
        return jsonify({'success': True, 'order_id': order_id})
    except Exception as e:
        print(f"[ERROR] Order creation failed: {e}")
        conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/orders')
@login_required
def orders_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT o.id, o.quantity, o.total_price, o.status, o.ordered_at,
                     p.product, p.brand, p.image_url FROM orders o
                     JOIN products p ON o.product_id = p.id WHERE o.user_id = ?
                     ORDER BY o.ordered_at DESC''', (session['user_id'],))
    orders = cursor.fetchall()
    conn.close()
    
    # Convert ordered_at string to datetime object for proper formatting
    orders_list = []
    for o in orders:
        try:
            ordered_at = datetime.strptime(o[4], '%Y-%m-%d %H:%M:%S') if o[4] else datetime.now()
        except:
            ordered_at = datetime.now()
        
        orders_list.append({
            'id': o[0], 
            'quantity': o[1], 
            'total_price': o[2], 
            'status': o[3],
            'ordered_at': ordered_at,  # Now it's a datetime object
            'product_name': o[5], 
            'brand': o[6], 
            'image_url': None  # Images disabled for LinkedIn demo
        })
    
    return render_template('orders/list.html', orders=orders_list)

@app.route('/orders/tracking/<int:order_id>')
@login_required
def track_order_simple(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT o.id, o.quantity, o.total_price, o.status, o.ordered_at,
                     p.product, p.brand FROM orders o JOIN products p ON o.product_id = p.id
                     WHERE o.id = ? AND o.user_id = ?''', (order_id, session['user_id']))
    order = cursor.fetchone()
    conn.close()
    if not order:
        return redirect(url_for('orders_list'))
    
    # Convert ordered_at string to datetime object
    try:
        ordered_at = datetime.strptime(order[4], '%Y-%m-%d %H:%M:%S') if order[4] else datetime.now()
    except:
        ordered_at = datetime.now()
    
    order_dict = {
        'id': order[0], 
        'quantity': order[1], 
        'total_price': order[2], 
        'status': order[3],
        'ordered_at': ordered_at,  # Now it's a datetime object
        'product_name': order[5], 
        'brand': order[6]
    }
    return render_template('orders/tracking.html', order=order_dict)

@app.route('/tracking')
@login_required
def tracking():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get user's default address with GPS coordinates
    cursor.execute('''
        SELECT id, name, address_line1, address_line2, city, state, 
               pincode, landmark, latitude, longitude 
        FROM addresses 
        WHERE user_id = ? AND is_default = 1 
        LIMIT 1
    ''', (session['user_id'],))
    
    address = cursor.fetchone()
    conn.close()
    
    if address:
        address_data = {
            'id': address[0],
            'name': address[1],
            'address_line1': address[2],
            'address_line2': address[3] or '',
            'city': address[4],
            'state': address[5],
            'pincode': address[6],
            'landmark': address[7] or '',
            'latitude': address[8],
            'longitude': address[9]
        }
    else:
        # Fallback if no address saved
        address_data = {
            'name': 'Home',
            'address_line1': 'No address saved',
            'address_line2': '',
            'city': 'Please add an address in settings',
            'state': '',
            'pincode': '',
            'landmark': '',
            'latitude': None,
            'longitude': None
        }
    
    return render_template('tracking.html', address=address_data)

@app.route('/orders/details/<int:order_id>')
@login_required
def order_details(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT o.id, o.quantity, o.total_price, o.status, o.ordered_at,
                     p.product, p.brand, p.image_url, p.category, p.sale_price FROM orders o
                     JOIN products p ON o.product_id = p.id
                     WHERE o.id = ? AND o.user_id = ?''', (order_id, session['user_id']))
    order = cursor.fetchone()
    conn.close()
    if not order:
        return redirect(url_for('orders_list'))
    
    # Convert ordered_at string to datetime object
    try:
        ordered_at = datetime.strptime(order[4], '%Y-%m-%d %H:%M:%S') if order[4] else datetime.now()
    except:
        ordered_at = datetime.now()
    
    order_dict = {
        'id': order[0], 
        'quantity': order[1], 
        'total_price': order[2], 
        'status': order[3],
        'ordered_at': ordered_at,  # Now it's a datetime object
        'product_name': order[5], 
        'brand': order[6], 
        'image_url': None, # Images disabled for LinkedIn demo
        'category': order[8], 
        'sale_price': order[9]
    }
    return render_template('orders/tracking.html', order=order_dict)

@app.route('/api/orders')
@login_required
def api_orders():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT o.id, o.product_id, o.quantity, o.total_price, o.ordered_at, o.status,
               p.product, p.brand, p.sale_price, p.image_url
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.user_id = ?
        ORDER BY o.ordered_at DESC
    ''', (session['user_id'],))
    
    orders = []
    for row in cursor.fetchall():
        orders.append({
            'id': row[0],
            'product_id': row[1],
            'quantity': row[2],
            'total_price': row[3],
            'ordered_at': row[4],
            'status': row[5] if row[5] else 'pending',
            'product_name': row[6],
            'brand': row[7],
            'sale_price': row[8],
            'image_url': None  # Images disabled for LinkedIn demo
        })
    
    conn.close()
    return jsonify(orders)

@app.route('/api/order/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE orders SET status = "cancelled" WHERE id = ? AND user_id = ?', (order_id, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/addresses')
@login_required
def addresses():
    return render_template('addresses.html')

@app.route('/api/addresses', methods=['GET', 'POST'])
@login_required
def api_addresses():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'GET':
        cursor.execute('''SELECT id, name, phone, address_line1, address_line2, city, state,
                         pincode, landmark, latitude, longitude, is_default FROM addresses
                         WHERE user_id = ? ORDER BY is_default DESC''', (session['user_id'],))
        addresses = cursor.fetchall()
        conn.close()
        return jsonify([{'id': a[0], 'name': a[1], 'phone': a[2], 'address_line1': a[3],
                        'address_line2': a[4], 'city': a[5], 'state': a[6], 'pincode': a[7],
                        'landmark': a[8], 'latitude': a[9], 'longitude': a[10], 'is_default': a[11]} for a in addresses])
    else:
        data = request.json
        if data.get('is_default'):
            cursor.execute('UPDATE addresses SET is_default = 0 WHERE user_id = ?', (session['user_id'],))
        cursor.execute('''INSERT INTO addresses (user_id, name, phone, address_line1, address_line2,
                         city, state, pincode, landmark, latitude, longitude, is_default)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (session['user_id'], data['name'], data['phone'], data['address_line1'],
                       data.get('address_line2', ''), data['city'], data['state'], data['pincode'],
                       data.get('landmark', ''), data.get('latitude'), data.get('longitude'), data.get('is_default', 0)))
        conn.commit()
        address_id = cursor.lastrowid
        conn.close()
        return jsonify({'success': True, 'id': address_id})

@app.route('/api/addresses/<int:address_id>', methods=['PUT', 'DELETE'])
@login_required
def api_address_detail(address_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'PUT':
        data = request.json
        if data.get('is_default'):
            cursor.execute('UPDATE addresses SET is_default = 0 WHERE user_id = ?', (session['user_id'],))
        cursor.execute('''UPDATE addresses SET name = ?, phone = ?, address_line1 = ?, address_line2 = ?,
                         city = ?, state = ?, pincode = ?, landmark = ?, latitude = ?, longitude = ?, is_default = ?
                         WHERE id = ? AND user_id = ?''',
                      (data['name'], data['phone'], data['address_line1'], data.get('address_line2', ''),
                       data['city'], data['state'], data['pincode'], data.get('landmark', ''),
                       data.get('latitude'), data.get('longitude'), data.get('is_default', 0), address_id, session['user_id']))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    else:
        cursor.execute('DELETE FROM addresses WHERE id = ? AND user_id = ?', (address_id, session['user_id']))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

@app.route('/api/addresses/<int:address_id>/set-default', methods=['POST'])
@login_required
def set_default_address(address_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE addresses SET is_default = 0 WHERE user_id = ?', (session['user_id'],))
    cursor.execute('UPDATE addresses SET is_default = 1 WHERE id = ? AND user_id = ?', (address_id, session['user_id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/api/user/profile')
@login_required
def api_user_profile():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT email, created_at FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    if user:
        return jsonify({'email': user[0], 'created_at': user[1] if user[1] else 'Unknown'})
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/user/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.json
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    
    if not current_password or not new_password:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT password_hash FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    # Verify current password
    if not bcrypt.checkpw(current_password.encode('utf-8'), user[0].encode('utf-8')):
        conn.close()
        return jsonify({'success': False, 'error': 'Current password is incorrect'}), 400
    
    # Update to new password
    new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (new_hash, session['user_id']))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Password updated successfully'})

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/help')
@login_required
def help_page():
    return render_template('help.html')

@app.route('/api/support/contact', methods=['POST'])
@login_required
def support_contact():
    data = request.json
    print(f"[OK] Support: {session['email']} - {data.get('message')}")
    return jsonify({'success': True})

@app.route('/chatbot')
@login_required
def chatbot():
    return render_template('chatbot.html')

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    """Intelligent chatbot API with conversation memory"""
    data = request.json
    if not data.get('message'):
        return jsonify({'response': 'Please ask a question'})
    
    if RAG_AVAILABLE:
        try:
            user_id = session.get('user_id')
            
            # Use Gemini RAG if available (v3.0)
            if RAG_TYPE == 'gemini':
                result = RAG_GEMINI.chat_with_gemini(data['message'], use_history=True)
                return jsonify({
                    'response': result['response'],
                    'products': result.get('products', [])[:3],  # Return top 3 products
                    'type': 'gemini'
                })
            
            # Use intelligent RAG if available (v2.0 with user context)
            elif RAG_TYPE == 'intelligent':
                from datetime import datetime
                session_id = f"user_{user_id}_{datetime.now().date()}"
                response = rag_query(data['message'], user_id=user_id, session_id=session_id)
                return jsonify({'response': response, 'type': 'intelligent'})
            
            # Fallback to standard RAG (v1.0)
            else:
                response = rag_query(data['message'])
                return jsonify({'response': response, 'type': 'standard'})
            
        except Exception as e:
            print(f"Chat error: {e}")
            return jsonify({'response': '🤔 Sorry, I encountered an error. Please try again!'})
    
    return jsonify({'response': '🔧 Chatbot is currently unavailable. Please try again later.'})

@app.route('/api/chat/reset', methods=['POST'])
@login_required
def reset_chat():
    """Reset chat history for Gemini RAG"""
    if RAG_AVAILABLE and RAG_TYPE == 'gemini':
        try:
            RAG_GEMINI.reset_chat_history()
            return jsonify({'success': True, 'message': 'Chat history cleared!'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    return jsonify({'success': False, 'message': 'Gemini RAG not available'})

@app.route('/api/products/semantic-search', methods=['GET'])
@login_required
def semantic_search():
    """Semantic product search using Gemini RAG"""
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))
    
    if not query or len(query) < 2:
        return jsonify({'products': []})
    
    if RAG_AVAILABLE and RAG_TYPE == 'gemini':
        try:
            results = RAG_GEMINI.search_products(query, top_k=limit)
            return jsonify({'products': results, 'type': 'semantic'})
        except Exception as e:
            print(f"Semantic search error: {e}")
            return jsonify({'products': [], 'error': str(e)})
    
    return jsonify({'products': [], 'message': 'Semantic search not available'})

@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin"')
    admin_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM orders')
    total_orders = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM products')
    total_products = cursor.fetchone()[0]
    cursor.execute('SELECT id, email, role, created_at FROM users ORDER BY created_at DESC LIMIT 10')
    recent_users = cursor.fetchall()
    cursor.execute('SELECT o.id, u.email, o.total_price, o.status, o.ordered_at FROM orders o JOIN users u ON o.user_id = u.id ORDER BY o.ordered_at DESC LIMIT 10')
    recent_orders = cursor.fetchall()
    conn.close()
    return render_template('admin/dashboard.html', total_users=total_users, admin_count=admin_count,
                         total_orders=total_orders, total_products=total_products,
                         recent_users=recent_users, recent_orders=recent_orders)

@app.route('/admin/users')
@admin_required
def admin_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, email, role, created_at FROM users ORDER BY created_at DESC')
    users = cursor.fetchall()
    conn.close()
    users_list = [{'id': u[0], 'email': u[1], 'role': u[2], 'created_at': u[3]} for u in users]
    return render_template('admin/users.html', users=users_list, current_user_id=session['user_id'])

@app.route('/admin/users/<int:user_id>/toggle-admin', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    if user_id == session['user_id']:
        return jsonify({'success': False}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT role FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return jsonify({'success': False}), 404
    new_role = 'user' if user[0] == 'admin' else 'admin'
    cursor.execute('UPDATE users SET role = ? WHERE id = ?', (new_role, user_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'new_role': new_role})

@app.route('/home')
@login_required
def home():
    return redirect(url_for('products_home'))

@app.route('/auth')
def auth():
    mode = request.args.get('mode', 'login')
    if mode == 'signup':
        return redirect(url_for('register'))
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# ===== ROUTINE DELIVERY SYSTEM =====

@app.route('/routine')
@login_required
def routine_deliveries():
    """Display user's routine deliveries"""
    return render_template('routine.html')

@app.route('/api/routine', methods=['GET'])
@login_required
def get_routines():
    """Get all routine deliveries for current user with analytics"""
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT r.*, p.product, p.brand, p.sale_price, p.category,
               CASE 
                   WHEN r.price_locked IS NOT NULL THEN r.price_locked
                   ELSE p.sale_price
               END as effective_price,
               (julianday(r.next_delivery_date) - julianday('now')) as days_until_next
        FROM routine_deliveries r
        JOIN products p ON r.product_id = p.id
        WHERE r.user_id = ?
        ORDER BY r.is_active DESC, r.next_delivery_date ASC
    ''', (session['user_id'],))
    
    routines = []
    for row in cursor.fetchall():
        routine_dict = dict(row)
        routine_dict['image_url'] = None  # Images disabled for LinkedIn demo
        
        # Calculate total savings if price was locked
        if routine_dict['price_locked'] and routine_dict['sale_price'] > routine_dict['price_locked']:
            savings_per_order = (routine_dict['sale_price'] - routine_dict['price_locked']) * routine_dict['quantity']
            routine_dict['total_savings'] = savings_per_order * routine_dict['orders_completed']
        else:
            routine_dict['total_savings'] = 0
        
        # Calculate projected monthly cost
        frequency_multiplier = {
            'daily': 30,
            'weekly': 4,
            'biweekly': 2,
            'monthly': 1,
            'custom': 30 / (routine_dict['custom_interval_days'] or 7)
        }
        routine_dict['monthly_cost'] = routine_dict['effective_price'] * routine_dict['quantity'] * frequency_multiplier.get(routine_dict['frequency'], 1)
        
        routines.append(routine_dict)
    
    # Calculate total monthly spend
    total_monthly = sum(r['monthly_cost'] for r in routines if r['is_active'] and not r['is_paused'])
    
    conn.close()
    
    return jsonify({
        'success': True, 
        'routines': routines,
        'analytics': {
            'total_monthly_spend': round(total_monthly, 2),
            'active_routines': len([r for r in routines if r['is_active'] and not r['is_paused']]),
            'paused_routines': len([r for r in routines if r['is_paused']]),
            'total_savings': sum(r.get('total_savings', 0) for r in routines)
        }
    })

@app.route('/api/routine', methods=['POST'])
@login_required
def create_routine():
    """Create a new routine delivery with advanced options"""
    from datetime import datetime, timedelta
    data = request.json
    
    # Validate required fields
    required = ['product_id', 'quantity', 'frequency']
    if not all(k in data for k in required):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Calculate next delivery date based on frequency
    frequency = data['frequency']
    delivery_time = data.get('delivery_time', '09:00')
    delivery_day = data.get('delivery_day', '')
    custom_interval = data.get('custom_interval_days', 7)
    
    today = datetime.now().date()
    if frequency == 'daily':
        next_date = today + timedelta(days=1)
    elif frequency == 'weekly':
        next_date = today + timedelta(days=7)
    elif frequency == 'biweekly':
        next_date = today + timedelta(days=14)
    elif frequency == 'monthly':
        next_date = today + timedelta(days=30)
    elif frequency == 'custom':
        next_date = today + timedelta(days=custom_interval)
    else:
        return jsonify({'success': False, 'message': 'Invalid frequency'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get current product price for price lock option
        cursor.execute('SELECT sale_price FROM products WHERE id = ?', (data['product_id'],))
        product = cursor.fetchone()
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'}), 404
        
        price_locked = product[0] if data.get('lock_price', False) else None
        
        cursor.execute('''
            INSERT INTO routine_deliveries 
            (user_id, product_id, quantity, frequency, delivery_day, delivery_time, 
             next_delivery_date, auto_order, max_orders, price_locked, 
             notification_enabled, skip_holidays, custom_interval_days, start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'], 
            data['product_id'], 
            data['quantity'], 
            frequency, 
            delivery_day, 
            delivery_time, 
            next_date,
            data.get('auto_order', 1),
            data.get('max_orders'),
            price_locked,
            data.get('notification_enabled', 1),
            data.get('skip_holidays', 1),
            custom_interval if frequency == 'custom' else None,
            today,
            data.get('end_date')
        ))
        
        routine_id = cursor.lastrowid
        conn.commit()
        
        # Fetch the created routine with product details
        cursor.execute('''
            SELECT r.*, p.product, p.brand, p.sale_price
            FROM routine_deliveries r
            JOIN products p ON r.product_id = p.id
            WHERE r.id = ?
        ''', (routine_id,))
        
        routine = dict(zip([d[0] for d in cursor.description], cursor.fetchone()))
        routine['image_url'] = None  # Images disabled
        conn.close()
        
        return jsonify({'success': True, 'routine': routine, 'message': 'Routine delivery created!'})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/routine/<int:routine_id>', methods=['PUT'])
@login_required
def update_routine(routine_id):
    """Update a routine delivery"""
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify ownership
    cursor.execute('SELECT user_id FROM routine_deliveries WHERE id = ?', (routine_id,))
    result = cursor.fetchone()
    if not result or result[0] != session['user_id']:
        conn.close()
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Build update query dynamically
    updates = []
    params = []
    
    if 'quantity' in data:
        updates.append('quantity = ?')
        params.append(data['quantity'])
    if 'frequency' in data:
        updates.append('frequency = ?')
        params.append(data['frequency'])
    if 'delivery_time' in data:
        updates.append('delivery_time = ?')
        params.append(data['delivery_time'])
    if 'delivery_day' in data:
        updates.append('delivery_day = ?')
        params.append(data['delivery_day'])
    if 'is_paused' in data:
        updates.append('is_paused = ?')
        params.append(1 if data['is_paused'] else 0)
    
    updates.append('updated_at = CURRENT_TIMESTAMP')
    params.append(routine_id)
    
    if updates:
        query = f"UPDATE routine_deliveries SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
    
    conn.close()
    return jsonify({'success': True, 'message': 'Routine updated!'})

@app.route('/api/routine/<int:routine_id>/toggle', methods=['POST'])
@login_required
def toggle_routine(routine_id):
    """Pause/Resume a routine delivery"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify ownership
    cursor.execute('SELECT user_id, is_paused FROM routine_deliveries WHERE id = ?', (routine_id,))
    result = cursor.fetchone()
    if not result or result[0] != session['user_id']:
        conn.close()
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    new_paused = 0 if result[1] else 1
    cursor.execute('UPDATE routine_deliveries SET is_paused = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', 
                   (new_paused, routine_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'is_paused': new_paused, 
                   'message': 'Routine paused' if new_paused else 'Routine resumed'})

@app.route('/api/routine/<int:routine_id>', methods=['DELETE'])
@login_required
def delete_routine(routine_id):
    """Delete a routine delivery"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify ownership
    cursor.execute('SELECT user_id FROM routine_deliveries WHERE id = ?', (routine_id,))
    result = cursor.fetchone()
    if not result or result[0] != session['user_id']:
        conn.close()
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    cursor.execute('DELETE FROM routine_deliveries WHERE id = ?', (routine_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Routine deleted!'})

@app.route('/api/routine/suggestions', methods=['GET'])
@login_required
def routine_suggestions():
    """Get suggested products for routine delivery based on order history with AI insights"""
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Find frequently ordered products
    cursor.execute('''
        SELECT p.id, p.product, p.brand, p.sale_price, p.category,
               COUNT(*) as order_count,
               AVG(o.quantity) as avg_quantity,
               MAX(o.ordered_at) as last_ordered,
               (julianday('now') - julianday(MAX(o.ordered_at))) as days_since_last_order
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.user_id = ?
        GROUP BY p.id
        HAVING order_count >= 2
        ORDER BY order_count DESC, days_since_last_order ASC
        LIMIT 20
    ''', (session['user_id'],))
    
    suggestions = []
    for row in cursor.fetchall():
        suggestion = dict(row)
        suggestion['image_url'] = None  # Images disabled
        
        # Calculate suggested frequency based on ordering pattern
        if suggestion['days_since_last_order'] and suggestion['order_count'] > 1:
            avg_days_between = suggestion['days_since_last_order'] / (suggestion['order_count'] - 1)
            if avg_days_between <= 3:
                suggestion['recommended_frequency'] = 'daily'
            elif avg_days_between <= 10:
                suggestion['recommended_frequency'] = 'weekly'
            elif avg_days_between <= 20:
                suggestion['recommended_frequency'] = 'biweekly'
            else:
                suggestion['recommended_frequency'] = 'monthly'
        else:
            suggestion['recommended_frequency'] = 'weekly'
        
        # Calculate potential monthly savings
        suggestion['potential_monthly_savings'] = round(suggestion['sale_price'] * 0.05 * suggestion['avg_quantity'] * 4, 2)
        
        suggestions.append(suggestion)
    
    conn.close()
    
    return jsonify({'success': True, 'suggestions': suggestions})

@app.route('/api/routine/<int:routine_id>/skip-next', methods=['POST'])
@login_required
def skip_next_delivery(routine_id):
    """Skip the next scheduled delivery"""
    from datetime import datetime, timedelta
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify ownership and get current routine
    cursor.execute('''
        SELECT user_id, frequency, next_delivery_date, custom_interval_days 
        FROM routine_deliveries 
        WHERE id = ?
    ''', (routine_id,))
    result = cursor.fetchone()
    
    if not result or result[0] != session['user_id']:
        conn.close()
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    frequency = result[1]
    current_next_date = datetime.strptime(result[2], '%Y-%m-%d').date()
    custom_interval = result[3]
    
    # Calculate new next delivery date (skip one cycle)
    if frequency == 'daily':
        new_next_date = current_next_date + timedelta(days=1)
    elif frequency == 'weekly':
        new_next_date = current_next_date + timedelta(days=7)
    elif frequency == 'biweekly':
        new_next_date = current_next_date + timedelta(days=14)
    elif frequency == 'monthly':
        new_next_date = current_next_date + timedelta(days=30)
    elif frequency == 'custom' and custom_interval:
        new_next_date = current_next_date + timedelta(days=custom_interval)
    else:
        new_next_date = current_next_date + timedelta(days=7)
    
    cursor.execute('''
        UPDATE routine_deliveries 
        SET next_delivery_date = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    ''', (new_next_date, routine_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True, 
        'message': 'Next delivery skipped',
        'new_next_delivery': str(new_next_date)
    })

@app.route('/api/routine/<int:routine_id>/lock-price', methods=['POST'])
@login_required
def lock_routine_price(routine_id):
    """Lock current price for routine delivery"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify ownership and get product price
    cursor.execute('''
        SELECT r.user_id, p.sale_price
        FROM routine_deliveries r
        JOIN products p ON r.product_id = p.id
        WHERE r.id = ?
    ''', (routine_id,))
    result = cursor.fetchone()
    
    if not result or result[0] != session['user_id']:
        conn.close()
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    current_price = result[1]
    
    cursor.execute('''
        UPDATE routine_deliveries 
        SET price_locked = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    ''', (current_price, routine_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True, 
        'message': f'Price locked at ₹{current_price}',
        'locked_price': current_price
    })

@app.route('/api/routine/analytics', methods=['GET'])
@login_required
def routine_analytics():
    """Get comprehensive analytics for routine deliveries"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total spend on routine deliveries
    cursor.execute('''
        SELECT 
            COUNT(*) as total_routines,
            SUM(CASE WHEN is_active = 1 AND is_paused = 0 THEN 1 ELSE 0 END) as active_routines,
            SUM(orders_completed) as total_deliveries,
            AVG(CASE WHEN price_locked IS NOT NULL THEN price_locked ELSE 0 END) as avg_locked_price
        FROM routine_deliveries
        WHERE user_id = ?
    ''', (session['user_id'],))
    
    analytics = dict(zip([d[0] for d in cursor.description], cursor.fetchone()))
    
    # Category breakdown
    cursor.execute('''
        SELECT p.category, COUNT(*) as count
        FROM routine_deliveries r
        JOIN products p ON r.product_id = p.id
        WHERE r.user_id = ? AND r.is_active = 1
        GROUP BY p.category
    ''', (session['user_id'],))
    
    analytics['category_breakdown'] = {row[0]: row[1] for row in cursor.fetchall()}
    
    conn.close()
    
    return jsonify({'success': True, 'analytics': analytics})

@app.errorhandler(404)
def not_found(e):
    return redirect(url_for('products_home'))

@app.errorhandler(500)
def server_error(e):
    return "Internal Server Error", 500

if __name__ == '__main__':
    print("=" * 70)
    print("SWIPPE - QUICK COMMERCE PLATFORM")
    print("=" * 70)
    print(f"[OK] RAG Chatbot: {'Enabled' if RAG_AVAILABLE else 'Disabled'}")
    print(f"[OK] Email System: {'Enabled' if EMAIL_AVAILABLE else 'Disabled'}")
    print("[OK] 27,555+ Products | Admin System | GPS Addresses")
    print("=" * 70)
    print("\n🚀 Server starting at http://127.0.0.1:5000")
    print("📌 Press CTRL+C to stop\n")
    app.run(debug=False, host='127.0.0.1', port=5000, use_reloader=False)
