import sys
import sqlite3
import os
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox, QMessageBox, QDateEdit,
    QFormLayout
)
from PySide6.QtCore import Qt, QDate

DB_NAME = "supermarket.db"
# --- [إضافة] تعريف مجلد الفواتير ---
RECEIPT_FOLDER = "purchase_receipts"

# --- [إضافة] التأكد من وجود المجلد، وإنشاؤه إذا لم يكن موجودًا ---
if not os.path.exists(RECEIPT_FOLDER):
    os.makedirs(RECEIPT_FOLDER)

class PurchaseWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧾 وحدة المشتريات")
        self.setGeometry(150, 100, 1200, 700)
        self.cart = []

        # ... (Stylesheet remains the same) ...
        self.setStyleSheet("""
            QWidget { background-color: #11111f; color: #dddddd; font-family: 'Segoe UI'; }
            QLineEdit, QSpinBox, QComboBox, QDateEdit {
                background-color: #1e1e2f; border: 1px solid #444466; border-radius: 6px;
                padding: 6px; font-size: 14px; color: #eee;
            }
            QPushButton {
                background-color: #3a86ff; color: white; border-radius: 6px; padding: 8px 12px;
                font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #5599ff; }
            QTableWidget { background-color: #1e1e2f; gridline-color: #444466; font-size: 13px; }
            QHeaderView::section {
                background-color: #2a2a4a; color: #aaccff; padding: 5px;
                font-weight: bold; border: 1px solid #444466;
            }
            QLabel#total_label { font-size: 18px; font-weight: bold; color: #00ff99; }
        """)

        self.layout = QVBoxLayout(self)
        self.create_top_section()
        self.create_table()
        self.create_bottom_section()
        self.load_products()
        self.load_suppliers()

    def connect_db(self):
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    def create_top_section(self):
        form_layout = QFormLayout()
        
        self.supplier_combo = QComboBox()
        self.product_combo = QComboBox()
        self.product_combo.setEditable(True) # Make it searchable
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 10000)
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("سعر شراء الوحدة (الكرتون)")
        self.expiry_input = QDateEdit(QDate.currentDate().addYears(1))
        self.expiry_input.setCalendarPopup(True)

        form_layout.addRow("المورد:", self.supplier_combo)
        form_layout.addRow("المنتج:", self.product_combo)
        form_layout.addRow("الكمية (وحدة/كرتون):", self.quantity_input)
        form_layout.addRow("سعر الوحدة:", self.price_input)
        form_layout.addRow("تاريخ الانتهاء:", self.expiry_input)
        
        self.add_btn = QPushButton("➕ إضافة للسلة")
        self.add_btn.clicked.connect(self.add_product_to_cart)
        form_layout.addRow(self.add_btn)
        
        self.layout.addLayout(form_layout)

    def create_table(self):
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "المنتج", "الكمية (وحدة)", "سعر الوحدة", "الإجمالي", "تاريخ الانتهاء"])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)

    def create_bottom_section(self):
        layout = QHBoxLayout()
        self.invoice_number_input = QLineEdit()
        self.invoice_number_input.setPlaceholderText("رقم فاتورة المورد (اختياري)")
        self.discount_input = QLineEdit("0")
        self.tax_input = QLineEdit("0")
        self.total_label = QLabel("الإجمالي: 0.00 ريال")
        self.total_label.setObjectName("total_label")
        self.save_btn = QPushButton("💾 حفظ الفاتورة")
        self.save_btn.clicked.connect(self.finalize_purchase)

        # Connect signals
        self.discount_input.textChanged.connect(self.update_total_label)
        self.tax_input.textChanged.connect(self.update_total_label)
        
        form_layout = QFormLayout()
        form_layout.addRow("رقم الفاتورة:", self.invoice_number_input)
        form_layout.addRow("الخصم (مبلغ):", self.discount_input)
        form_layout.addRow("الضريبة (%):", self.tax_input)

        layout.addLayout(form_layout)
        layout.addWidget(self.total_label)
        layout.addWidget(self.save_btn)
        self.layout.addLayout(layout)

    def load_products(self):
        self.product_combo.clear()
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM products ORDER BY name ASC")
        for row in cursor.fetchall():
            self.product_combo.addItem(row['name'], row['id'])
        conn.close()

    def load_suppliers(self):
        self.supplier_combo.clear()
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM suppliers ORDER BY name ASC")
        self.supplier_combo.addItem("مورد عام", None) # Add a generic supplier
        for row in cursor.fetchall():
            self.supplier_combo.addItem(row['name'], row['id'])
        conn.close()

    def add_product_to_cart(self):
        product_id = self.product_combo.currentData()
        product_name = self.product_combo.currentText()
        quantity = self.quantity_input.value()
        price_text = self.price_input.text()
        expiry_date = self.expiry_input.date().toString("yyyy-MM-dd")

        if not price_text:
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال السعر.")
            return
        try:
            price = float(price_text)
        except ValueError:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال سعر صحيح.")
            return

        total = quantity * price

        for item in self.cart:
            if item["id"] == product_id and item["expiry"] == expiry_date:
                item["quantity"] += quantity
                break
        else:
            self.cart.append({"id": product_id, "name": product_name, "quantity": quantity, "price": price, "expiry": expiry_date})
        
        self.refresh_cart()

    def refresh_cart(self):
        self.table.setRowCount(0)
        for row_idx, item in enumerate(self.cart):
            total = item['quantity'] * item['price']
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(item["id"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(item["name"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(item["quantity"])))
            self.table.setItem(row_idx, 3, QTableWidgetItem(f"{item['price']:.2f}"))
            self.table.setItem(row_idx, 4, QTableWidgetItem(f"{total:.2f}"))
            self.table.setItem(row_idx, 5, QTableWidgetItem(item["expiry"]))
        self.update_total_label()

    def update_total_label(self):
        try:
            discount = float(self.discount_input.text() or "0")
            tax_percent = float(self.tax_input.text() or "0")
        except ValueError:
            discount, tax_percent = 0, 0
        
        subtotal = sum(i['quantity'] * i['price'] for i in self.cart)
        total_after_discount = subtotal - discount
        tax_amount = total_after_discount * (tax_percent / 100)
        final_total = total_after_discount + tax_amount
        self.total_label.setText(f"الإجمالي: {final_total:.2f} ريال")

    def finalize_purchase(self):
        if not self.cart:
            QMessageBox.warning(self, "تنبيه", "سلة المشتريات فارغة.")
            return
        if self.supplier_combo.currentIndex() == -1:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار مورد.")
            return

        supplier_id = self.supplier_combo.currentData()
        # --- [تعديل] الحصول على اسم المورد للطباعة ---
        supplier_name = self.supplier_combo.currentText()
        invoice_number = self.invoice_number_input.text().strip() or "PUR-" + datetime.now().strftime("%Y%m%d%H%M%S")
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            discount = float(self.discount_input.text() or "0")
            tax_percent = float(self.tax_input.text() or "0")
        except ValueError:
            QMessageBox.warning(self, "خطأ", "قيم الخصم والضريبة غير صحيحة.")
            return

        conn = self.connect_db()
        cursor = conn.cursor()

        try:
            subtotal = sum(i['quantity'] * i['price'] for i in self.cart)
            total_after_discount = subtotal - discount
            tax_amount = total_after_discount * (tax_percent / 100)
            final_total = total_after_discount + tax_amount

            # 1. حفظ الفاتورة
            cursor.execute("""
                INSERT INTO purchase_invoices (invoice_number, date, supplier_id, total, discount, tax, paid_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (invoice_number, date, supplier_id, final_total, discount, tax_amount, final_total))
            invoice_id = cursor.lastrowid

            # 2. حفظ الأصناف وتحديث المخزون
            for item in self.cart:
                total_item_price = item['quantity'] * item['price']
                cursor.execute("""
                    INSERT INTO purchase_items (invoice_id, product_id, quantity_units, unit_price, total_price, expiry_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (invoice_id, item["id"], item["quantity"], item["price"], total_item_price, item["expiry"]))
                
                cursor.execute("""
                    UPDATE products 
                    SET quantity_units = quantity_units + ?,
                        expiry_date = ? 
                    WHERE id = ?
                """, (item["quantity"], item["expiry"], item["id"]))
            
            conn.commit()
            
            # --- [تعديل] استدعاء دالة الطباعة مع تمرير البيانات اللازمة ---
            self.print_receipt(invoice_number, date, supplier_name, self.cart, final_total, discount, tax_amount)
            
            QMessageBox.information(self, "نجاح", f"تم حفظ فاتورة المشتريات وتحديث المخزون.\nتم حفظ نسخة نصية من الفاتورة في مجلد '{RECEIPT_FOLDER}'.")
            
            self.cart = []
            self.refresh_cart()
            self.invoice_number_input.clear()
            self.discount_input.setText("0")
            self.tax_input.setText("0")

        except sqlite3.Error as e:
            conn.rollback()
            QMessageBox.critical(self, "خطأ في قاعدة البيانات", f"فشلت العملية. تم التراجع عن كافة التغييرات.\nالخطأ: {e}")
        finally:
            conn.close()

    # --- [إضافة وتعديل] دالة طباعة الفاتورة إلى ملف نصي ---
    def print_receipt(self, invoice_number, date_str, supplier_name, items, total, discount, tax):
        """
        تنشئ هذه الدالة ملفًا نصيًا يمثل فاتورة حرارية.
        """
        filename = os.path.join(RECEIPT_FOLDER, f"{invoice_number}.txt")
        WIDTH = 42  # عرض الفاتورة بالرموز

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                # ترويسة الفاتورة
                f.write("سوبرماركت XYZ\n".center(WIDTH + 10)) # +10 for better center with arabic
                f.write("صنعاء\n".center(WIDTH + 10))
                f.write("الهاتف:\n".center(WIDTH + 10))
                f.write("=" * WIDTH + "\n")
                f.write("فاتورة مشتريات\n".center(WIDTH+10))
                f.write("-" * WIDTH + "\n")

                # معلومات الفاتورة
                f.write(f"رقم الفاتورة: {invoice_number}\n")
                # تحويل التاريخ إلى صيغة مقروءة
                formatted_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %I:%M %p')
                f.write(f"التاريخ: {formatted_date}\n")
                f.write(f"المورد: {supplier_name}\n")
                f.write("-" * WIDTH + "\n")

                # ترويسة الأصناف
                f.write(f"{'الإجمالي'.ljust(9)} {'السعر'.ljust(9)} {'الكمية'.ljust(7)} {'الصنف'.ljust(15)}\n")
                f.write("-" * WIDTH + "\n")

                # قائمة الأصناف
                subtotal = 0
                for item in items:
                    name = item['name']
                    if len(name) > 14: # قص اسم المنتج الطويل
                        name = name[:13] + "."
                    
                    qty = str(item['quantity'])
                    price = f"{item['price']:.2f}"
                    item_total_val = item['quantity'] * item['price']
                    item_total_str = f"{item_total_val:.2f}"
                    subtotal += item_total_val

                    # تنظيم الأعمدة (من اليمين لليسار)
                    line = f"{item_total_str.ljust(9)} {price.ljust(9)} {qty.ljust(7)} {name.ljust(15)}\n"
                    f.write(line)
                
                f.write("-" * WIDTH + "\n")

                # الحسابات النهائية
                f.write(f"{f'{subtotal:.2f}'.rjust(12)} :الإجمالي الفرعي\n")
                f.write(f"{f'{-discount:.2f}'.rjust(12)} :الخصم\n")
                f.write(f"{f'{tax:.2f}'.rjust(12)} :الضريبة\n")
                f.write("=" * WIDTH + "\n")
                f.write(f"{f'{total:.2f}'.rjust(12)} :الإجمالي النهائي\n")
                f.write("=" * WIDTH + "\n")

                # رسالة ختامية
                f.write("شكراً لتعاملكم معنا\n".center(WIDTH + 10))

        except IOError as e:
            QMessageBox.critical(self, "خطأ في الطباعة", f"فشل حفظ ملف الفاتورة النصي.\nالخطأ: {e}")


if __name__ == "__main__":
    # هذا الجزء ضروري للتجربة، تأكد من إنشاء قاعدة بيانات بسيطة
    def setup_database():
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        # إنشاء الجداول إذا لم تكن موجودة
        cursor.execute("CREATE TABLE IF NOT EXISTS suppliers (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, quantity_units REAL DEFAULT 0, expiry_date TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS purchase_invoices (id INTEGER PRIMARY KEY, invoice_number TEXT, date TEXT, supplier_id INTEGER, total REAL, discount REAL, tax REAL, paid_amount REAL)")
        cursor.execute("CREATE TABLE IF NOT EXISTS purchase_items (id INTEGER PRIMARY KEY, invoice_id INTEGER, product_id INTEGER, quantity_units REAL, unit_price REAL, total_price REAL, expiry_date TEXT)")
        
        # إضافة بيانات افتراضية (للتجربة فقط)
        try:
            cursor.execute("INSERT INTO suppliers (name) VALUES (?), (?), (?)", ("مورد أ", "شركة التوزيع المتحدة", "مورد ج"))
            cursor.execute("INSERT INTO products (name) VALUES (?), (?), (?)", ("بيبسي كرتون", "مياه نوفا كرتون", "أرز أبو كاس 10كغ"))
        except sqlite3.IntegrityError:
            pass # البيانات موجودة بالفعل
        conn.commit()
        conn.close()

    setup_database()
    app = QApplication(sys.argv)
    window = PurchaseWindow()
    window.show()
    sys.exit(app.exec())