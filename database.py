# database.py
import sqlite3

def create_connection():
    return sqlite3.connect("supermarket.db")

def initialize_database():
    conn = create_connection()
    cursor = conn.cursor()

    # users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            permissions TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)

    # login logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category_id INTEGER,
    unit_id INTEGER,
    items_per_unit INTEGER NOT NULL,
    wholesale_price REAL,
    retail_price REAL,
    quantity_units INTEGER DEFAULT 0,        -- عدد الكراتين المتوفرة
    quantity_items INTEGER DEFAULT 0,        -- عدد الحبات المتبقية (غير كاملة كرتون)
    barcode TEXT UNIQUE,
    expiry_date TEXT,                        -- تاريخ الانتهاء إن وجد
    min_quantity INTEGER DEFAULT 0,          -- الحد الأدنى للتنبيه
    supplier_id INTEGER,
    FOREIGN KEY(category_id) REFERENCES categories(id),
    FOREIGN KEY(unit_id) REFERENCES units(id),
    FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
)
""")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            type TEXT NOT NULL, -- شراء، بيع، مرتجع، تعديل يدوي...
            quantity INTEGER NOT NULL,
            notes TEXT,
            FOREIGN KEY(product_id) REFERENCES products(id)
)
""")
    # products table
   

    # inventory table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            quantity INTEGER,
            expiry_date TEXT,
            alert_level INTEGER DEFAULT 10,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)
    cursor.execute("""
CREATE TABLE IF NOT EXISTS sales_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL, -- الكمية المباعة (بالحبة)
    unit_price REAL NOT NULL,
    total_price REAL NOT NULL,
    FOREIGN KEY(invoice_id) REFERENCES sales_invoices(id),
    FOREIGN KEY(product_id) REFERENCES products(id)
)
""")

    # pos sales
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            customer_name TEXT,
            total REAL,
            discount REAL,
            tax REAL,
            paid REAL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    cursor.execute("""
CREATE TABLE IF NOT EXISTS purchase_invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number TEXT UNIQUE,
    date TEXT NOT NULL,
    supplier_id INTEGER,
    total REAL NOT NULL,
    discount REAL DEFAULT 0,
    tax REAL DEFAULT 0,
    paid_amount REAL NOT NULL,
    notes TEXT,
    FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
)
""")
    cursor.execute("""
CREATE TABLE IF NOT EXISTS purchase_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity_units INTEGER NOT NULL,     -- كم كرتون أو كيس تم شراءه
    unit_price REAL NOT NULL,            -- سعر الوحدة (الكرتون)
    total_price REAL NOT NULL,           -- المجموع للسطر
    expiry_date TEXT,                    -- تاريخ الانتهاء للصنف إن وجد
    FOREIGN KEY(invoice_id) REFERENCES purchase_invoices(id),
    FOREIGN KEY(product_id) REFERENCES products(id)
)
""")
    # في ملف database.py، داخل دالة initialize_database()

# استبدل هذا الكود
    cursor.execute("""
CREATE TABLE IF NOT EXISTS sales_invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number TEXT UNIQUE,
    date TEXT NOT NULL,
    customer_id INTEGER, -- تم التعديل هنا
    total REAL NOT NULL,
    discount REAL DEFAULT 0,
    tax REAL DEFAULT 0,
    paid_amount REAL NOT NULL,
    notes TEXT,
    FOREIGN KEY(customer_id) REFERENCES customers(id) -- تم إضافة هذا السطر
)
""")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            price REAL,
            FOREIGN KEY(sale_id) REFERENCES sales(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)

    # purchases
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT DEFAULT CURRENT_TIMESTAMP,
            supplier_id INTEGER,
            user_id INTEGER,
            total REAL,
            discount REAL,
            paid REAL,
            FOREIGN KEY(supplier_id) REFERENCES suppliers(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            price REAL,
            FOREIGN KEY(purchase_id) REFERENCES purchases(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)

    # suppliers table
    # في ملف database.py، داخل دالة initialize_database()
# استبدل الكود القديم لإنشاء جدول الموردين بهذا الكود
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE, -- اسم المورد يجب أن يكون فريداً
        phone TEXT,
        email TEXT,
        bank_account TEXT,
        last_interaction TEXT,
        balance REAL DEFAULT 0.0 -- [إضافة جديدة] رصيد المورد
    )
""")

    # employees
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            department TEXT,
            salary REAL,
            join_date TEXT,
            last_payment TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            date TEXT,
            status TEXT,
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )
    """)
    cursor.execute("""
CREATE TABLE IF NOT EXISTS salaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER,
    month TEXT,
    days_present INTEGER,
    total_salary REAL,
    payment_date TEXT,
    FOREIGN KEY(employee_id) REFERENCES employees(id)
)
""")

    # accounting journal
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounting (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            description TEXT,
            debit REAL,
            credit REAL,
            account_name TEXT,
            reference_id INTEGER
        )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS journal_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        description TEXT,
        debit_account TEXT,
        credit_account TEXT,
        amount REAL NOT NULL,
        source TEXT  -- مثل (مبيعات، مرتجعات، يدوي، مشتريات...)
    )
""")

    # reports placeholder (no table needed)

    # invoices table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_type TEXT,  -- sale, purchase, return
            reference_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # returns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS returns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,  -- 'sale' or 'purchase'
            reference_invoice_id INTEGER,
            reason TEXT,
            date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS return_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            return_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            price REAL,
            FOREIGN KEY(return_id) REFERENCES returns(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)
    # في ملف database.py، داخل دالة initialize_database()

# ... (بعد جداول أخرى)

# Customers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE,
            address TEXT,
            balance REAL DEFAULT 0.0 -- رصيد العميل (لتتبع الديون)
    )
""")

    # settings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE,
            value TEXT
        )
    """)
# في ملف database.py، داخل دالة initialize_database()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chart_of_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL -- (مثال: أصل، التزام، إيراد، مصروف)
    )
""")
# إضافة حسابات افتراضية إذا كان الجدول فارغاً
    cursor.execute("SELECT COUNT(*) FROM chart_of_accounts")
    if cursor.fetchone()[0] == 0:
            default_accounts = [
                ('الصندوق', 'أصل'),
                ('البنك', 'أصل'),
                ('المخزون', 'أصل'),
                ('العملاء (الذمم المدينة)', 'أصل'),
                ('المبيعات', 'إيراد'),
                ('تكلفة البضاعة المباعة', 'مصروف'),
                ('مصروفات إيجار', 'مصروف'),
                ('مصروفات رواتب', 'مصروف'),
                ('الموردون (الذمم الدائنة)', 'التزام'),
                ('رأس المال', 'حقوق الملكية')
            ]
            cursor.executemany("INSERT INTO chart_of_accounts (name, type) VALUES (?, ?)", default_accounts)
            conn.commit()

    conn.commit()
    # إنشاء مستخدم افتراضي إذا لم يكن موجودًا
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO users (username, password, role, permissions, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, ("admin", "admin", "Administrator", "all", 1))
        print("✅ تم إنشاء المستخدم الافتراضي: اسم المستخدم: admin / كلمة المرور: admin")
    conn.commit()
    conn.close()
