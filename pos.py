import sys
import sqlite3
import os
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, 
    QSpinBox, QComboBox, QDialog, QFormLayout
)
from PySide6.QtCore import Qt

DB_NAME = "supermarket.db"
RECEIPT_FOLDER = "sales_receipts"
if not os.path.exists(RECEIPT_FOLDER):
    os.makedirs(RECEIPT_FOLDER)

# --- كلاس لإضافة عميل جديد ---
class AddCustomerDialog(QDialog):
    """نافذة منبثقة لإضافة عميل جديد."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("➕ إضافة عميل جديد")
        self.setMinimumWidth(350)
        # يرث نفس تصميم النافذة الأم
        self.setStyleSheet(parent.styleSheet() if parent else "") 

        layout = QFormLayout(self)
        self.name_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.address_input = QLineEdit()
        
        layout.addRow("اسم العميل:", self.name_input)
        layout.addRow("رقم الهاتف:", self.phone_input)
        layout.addRow("العنوان (اختياري):", self.address_input)

        self.save_btn = QPushButton("💾 حفظ العميل")
        self.save_btn.setObjectName("save_btn")
        self.save_btn.clicked.connect(self.save_customer)
        layout.addWidget(self.save_btn)

    def save_customer(self):
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        address = self.address_input.text().strip()

        if not name or not phone:
            QMessageBox.warning(self, "بيانات ناقصة", "يجب إدخال اسم العميل ورقم هاتفه على الأقل.")
            return

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)", (name, phone, address))
            conn.commit()
            QMessageBox.information(self, "نجاح", f"تمت إضافة العميل '{name}' بنجاح.")
            self.accept() # لإغلاق النافذة وإرجاع إشارة نجاح
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "خطأ", "رقم الهاتف هذا مسجل لعميل آخر.")
        finally:
            conn.close()

# --- النافذة الرئيسية لنقاط البيع ---
class POSWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("💳 نقطة البيع (POS)")
        self.setGeometry(100, 100, 1100, 700)
        self.cart = []
        
        self.setStyleSheet("""
            QWidget { background-color: #11111f; color: #dddddd; font-family: 'Segoe UI'; }
            QLineEdit, QSpinBox, QComboBox {
                background-color: #1e1e2f; border: 1px solid #444466; border-radius: 6px;
                padding: 8px; font-size: 14px; color: #eee;
            }
            QPushButton {
                border-radius: 6px; padding: 8px 12px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #5599ff; }
            QPushButton#pay_btn { background-color: #2ecc71; color: white; }
            QPushButton#pay_btn:hover { background-color: #27ae60; }
            QPushButton#save_btn { background-color: #00b894; color: white; }
            QPushButton#save_btn:hover { background-color: #55efc4; }
            QTableWidget {
                background-color: #1e1e2f; gridline-color: #444466; font-size: 14px;
            }
            QHeaderView::section {
                background-color: #2a2a4a; color: #aaccff; padding: 5px; font-weight: bold;
            }
            QLabel#total_label {
                font-size: 20px; font-weight: bold; color: #00ff99; padding: 5px;
                border: 1px solid #00ff99; border-radius: 6px;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.create_top_section()
        self.create_cart_section()
        self.create_bottom_section()
        self.load_customers()
        self.barcode_input.setFocus()

    def connect_db(self):
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn
        
    def create_top_section(self):
        top_layout = QVBoxLayout()
        customer_layout = QHBoxLayout()
        
        self.customer_combo = QComboBox()
        self.customer_combo.setMinimumWidth(250)
        self.customer_combo.setEditable(True) # Make it searchable
        
        self.add_customer_btn = QPushButton("➕")
        self.add_customer_btn.setToolTip("إضافة عميل جديد")
        self.add_customer_btn.setFixedSize(40, 40)
        self.add_customer_btn.clicked.connect(self.open_add_customer_dialog)

        customer_layout.addWidget(QLabel("العميل:"))
        customer_layout.addWidget(self.customer_combo, 1)
        customer_layout.addWidget(self.add_customer_btn)
        
        product_layout = QHBoxLayout()
        self.barcode_input = QLineEdit(placeholderText="📷 أدخل الباركود واضغط Enter...")
        self.barcode_input.returnPressed.connect(self.add_product_by_barcode)
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 1000)
        self.quantity_input.setValue(1)
        self.quantity_input.setPrefix("الكمية: ")

        product_layout.addWidget(self.barcode_input, 3)
        product_layout.addWidget(self.quantity_input, 1)

        top_layout.addLayout(customer_layout)
        top_layout.addLayout(product_layout)
        self.layout.addLayout(top_layout)

    def create_cart_section(self):
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "اسم المنتج", "سعر الحبة", "الكمية (حبة)", "الإجمالي"])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.layout.addWidget(self.table, 1)

    def create_bottom_section(self):
        bottom_layout = QHBoxLayout()
        form_layout = QFormLayout()

        self.discount_input = QLineEdit("0")
        self.tax_input = QLineEdit("0")
        self.paid_amount_input = QLineEdit()
        self.paid_amount_input.setPlaceholderText("المبلغ المدفوع (للبيع الآجل)")

        self.discount_input.textChanged.connect(self.update_total_label)
        self.tax_input.textChanged.connect(self.update_total_label)

        form_layout.addRow("الخصم (مبلغ):", self.discount_input)
        form_layout.addRow("الضريبة (%):", self.tax_input)
        form_layout.addRow("المبلغ المدفوع:", self.paid_amount_input)

        self.total_label = QLabel("الإجمالي: 0.00 ريال")
        self.total_label.setObjectName("total_label")
        self.total_label.setAlignment(Qt.AlignCenter)
        self.pay_btn = QPushButton("💵 إنهاء البيع")
        self.pay_btn.setObjectName("pay_btn")
        self.pay_btn.setMinimumHeight(60)
        self.pay_btn.clicked.connect(self.finalize_sale)
        
        bottom_layout.addLayout(form_layout)
        bottom_layout.addWidget(self.total_label, 1)
        bottom_layout.addWidget(self.pay_btn, 1)
        self.layout.addLayout(bottom_layout)
    
    # --- [تصحيح] تم إعادة هذه الدالة إلى حالتها الأصلية ---
    def load_customers(self):
        self.customer_combo.clear()
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, phone FROM customers ORDER BY name ASC")
        for customer in cursor.fetchall():
            self.customer_combo.addItem(f"{customer['name']} ({customer['phone']})", customer['id'])
        conn.close()
        # Set "عميل نقدي" as default
        cash_customer_index = self.customer_combo.findText("عميل نقدي", Qt.MatchContains)
        if cash_customer_index != -1:
            self.customer_combo.setCurrentIndex(cash_customer_index)

    def open_add_customer_dialog(self):
        dialog = AddCustomerDialog(self)
        if dialog.exec():
            self.load_customers()
            last_item_index = self.customer_combo.count() - 1
            self.customer_combo.setCurrentIndex(last_item_index)

    def add_product_by_barcode(self):
        barcode = self.barcode_input.text().strip()
        qty_to_add = self.quantity_input.value()
        if not barcode: return

        conn = self.connect_db()
        product = conn.cursor().execute("SELECT * FROM products WHERE barcode = ?", (barcode,)).fetchone()
        conn.close()

        if not product:
            QMessageBox.warning(self, "غير موجود", "المنتج غير موجود.")
            return

        available_items_total = (product['quantity_units'] * product['items_per_unit']) + product['quantity_items']
        current_cart_qty = sum(item['quantity'] for item in self.cart if item["id"] == product['id'])
        
        if (qty_to_add + current_cart_qty) > available_items_total:
            QMessageBox.warning(self, "كمية غير كافية", f"الكمية المطلوبة ({qty_to_add + current_cart_qty}) تتجاوز المتوفر ({available_items_total}).")
            return

        item_found = False
        for item in self.cart:
            if item["id"] == product['id']:
                item["quantity"] += qty_to_add
                item_found = True
                break
        
        if not item_found:
            self.cart.append({
                "id": product['id'], "name": product['name'], "price": product['retail_price'],
                "quantity": qty_to_add, "items_per_unit": product['items_per_unit']
            })

        self.refresh_cart()
        self.barcode_input.clear()
        self.barcode_input.setFocus()
        self.quantity_input.setValue(1)

    def refresh_cart(self):
        self.table.setRowCount(0)
        for row_idx, item in enumerate(self.cart):
            total_price = item['quantity'] * item['price']
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(item["id"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(item["name"]))
            self.table.setItem(row_idx, 2, QTableWidgetItem(f"{item['price']:.2f}"))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(item["quantity"])))
            self.table.setItem(row_idx, 4, QTableWidgetItem(f"{total_price:.2f}"))
        self.update_total_label()

    def update_total_label(self):
        try:
            discount = float(self.discount_input.text() or "0")
            tax_percent = float(self.tax_input.text() or "0")
        except ValueError:
            discount, tax_percent = 0, 0

        subtotal = sum(item['quantity'] * item['price'] for item in self.cart)
        total_after_discount = subtotal - discount
        tax_amount = total_after_discount * (tax_percent / 100)
        final_total = total_after_discount + tax_amount

        self.paid_amount_input.setText(f"{final_total:.2f}")
        self.total_label.setText(f"الإجمالي: {final_total:.2f} ريال")
        
    def finalize_sale(self):
        if not self.cart:
            QMessageBox.warning(self, "تنبيه", "السلة فارغة.")
            return

        customer_id = self.customer_combo.currentData()
        customer_name = self.customer_combo.currentText() # للحصول على اسم العميل للطباعة

        if not customer_id:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار عميل.")
            return

        try:
            discount = float(self.discount_input.text() or "0")
            tax_percent = float(self.tax_input.text() or "0")
            paid_amount = float(self.paid_amount_input.text() or "0")
        except ValueError:
            QMessageBox.warning(self, "خطأ", "قيم الخصم أو الضريبة أو المبلغ المدفوع غير صحيحة.")
            return

        subtotal = sum(i['quantity'] * i['price'] for i in self.cart)
        total_after_discount = subtotal - discount
        tax_amount = total_after_discount * (tax_percent / 100)
        final_total = total_after_discount + tax_amount
        remaining_balance = final_total - paid_amount

        conn = self.connect_db()
        cursor = conn.cursor()
        try:
            # التحقق النهائي من المخزون
            for item in self.cart:
                product = cursor.execute("SELECT name, quantity_units, quantity_items, items_per_unit FROM products WHERE id = ?", (item['id'],)).fetchone()
                available_items = (product['quantity_units'] * product['items_per_unit']) + product['quantity_items']
                if item['quantity'] > available_items:
                    raise ValueError(f"المخزون غير كافٍ للمنتج: {item['name']}. المتوفر: {available_items}")
            
            # 1. حفظ الفاتورة
            invoice_number = "INV-" + datetime.now().strftime("%Y%m%d%H%M%S")
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO sales_invoices (invoice_number, date, customer_id, total, discount, tax, paid_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (invoice_number, date, customer_id, final_total, discount, tax_amount, paid_amount))
            invoice_id = cursor.lastrowid

            # 2. حفظ الأصناف وتحديث المخزون
            for item in self.cart:
                cursor.execute("""
                    INSERT INTO sales_items (invoice_id, product_id, quantity, unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?)
                """, (invoice_id, item["id"], item["quantity"], item["price"], item['quantity'] * item['price']))
                cursor.execute("""
                    UPDATE products SET 
                        quantity_items = ((quantity_units * items_per_unit + quantity_items) - ?) % items_per_unit,
                        quantity_units = ((quantity_units * items_per_unit + quantity_items) - ?) / items_per_unit
                    WHERE id = ?
                """, (item['quantity'], item['quantity'], item['id']))
            
            # 3. تحديث رصيد العميل
            if abs(remaining_balance) > 0.01:
                cursor.execute("UPDATE customers SET balance = balance + ? WHERE id = ?", (remaining_balance, customer_id))
            
            conn.commit()
            
            self.print_receipt(invoice_number, date, customer_name, self.cart, final_total, discount, tax_amount, paid_amount)
            QMessageBox.information(self, "نجاح", f"تم حفظ الفاتورة رقم {invoice_number} بنجاح.\nتم حفظ نسخة نصية من الفاتورة في مجلد '{RECEIPT_FOLDER}'.")
            self.reset_form()
            
        except ValueError as ve:
            conn.rollback()
            QMessageBox.critical(self, "خطأ في المخزون", str(ve))
        except sqlite3.Error as e:
            conn.rollback()
            QMessageBox.critical(self, "خطأ في قاعدة البيانات", f"فشلت العملية. تم التراجع عن كافة التغييرات.\nالخطأ: {e}")
        finally:
            conn.close()

    def reset_form(self):
        self.cart = []
        self.table.setRowCount(0)
        self.discount_input.setText("0")
        self.tax_input.setText("0")
        self.paid_amount_input.clear()
        self.total_label.setText("الإجمالي: 0.00 ريال")
        self.load_customers() # لإعادة العميل الافتراضي
        self.barcode_input.setFocus()
        
    def print_receipt(self, invoice_number, date_str, customer_name, items, total, discount, tax, paid):
        """
        تنشئ هذه الدالة ملفًا نصيًا يمثل فاتورة مبيعات حرارية.
        """
        filename = os.path.join(RECEIPT_FOLDER, f"{invoice_number}.txt")
        WIDTH = 42  # عرض الفاتورة بالرموز

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                # ترويسة الفاتورة
                f.write("سوبرماركت XYZ\n".center(WIDTH + 10))
                f.write("صنعاء\n".center(WIDTH + 10))
                f.write("الهاتف: \n".center(WIDTH + 10))
                f.write("=" * WIDTH + "\n")
                f.write("فاتورة مبيعات\n".center(WIDTH + 10))
                f.write("-" * WIDTH + "\n")

                # معلومات الفاتورة
                f.write(f"الرقم: {invoice_number}\n")
                formatted_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %I:%M %p')
                f.write(f"التاريخ: {formatted_date}\n")
                f.write(f"العميل: {customer_name}\n")
                f.write("-" * WIDTH + "\n")

                # ترويسة الأصناف
                f.write(f"{'الإجمالي'.ljust(9)} {'السعر'.ljust(9)} {'الكمية'.ljust(7)} {'الصنف'.ljust(15)}\n")
                f.write("-" * WIDTH + "\n")

                # قائمة الأصناف
                subtotal = 0
                for item in items:
                    name = item['name']
                    if len(name) > 14:
                        name = name[:13] + "."
                    
                    qty = str(item['quantity'])
                    price = f"{item['price']:.2f}"
                    item_total_val = item['quantity'] * item['price']
                    item_total_str = f"{item_total_val:.2f}"
                    subtotal += item_total_val

                    line = f"{item_total_str.ljust(9)} {price.ljust(9)} {qty.ljust(7)} {name.ljust(15)}\n"
                    f.write(line)
                
                f.write("-" * WIDTH + "\n")

                # الحسابات النهائية
                remaining = total - paid
                f.write(f"{f'{subtotal:.2f}'.rjust(12)} :الإجمالي الفرعي\n")
                f.write(f"{f'{-discount:.2f}'.rjust(12)} :الخصم\n")
                f.write(f"{f'{tax:.2f}'.rjust(12)} :الضريبة\n")
                f.write("=" * WIDTH + "\n")
                f.write(f"{f'{total:.2f}'.rjust(12)} :الإجمالي النهائي\n")
                f.write(f"{f'{paid:.2f}'.rjust(12)} :المدفوع\n")
                f.write(f"{f'{remaining:.2f}'.rjust(12)} :المتبقي\n")
                f.write("=" * WIDTH + "\n")

                # رسالة ختامية
                f.write("شكراً لتسوقكم معنا\n".center(WIDTH + 10))

        except IOError as e:
            QMessageBox.critical(self, "خطأ في الطباعة", f"فشل حفظ ملف الفاتورة النصي.\nالخطأ: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = POSWindow()
    window.show()
    sys.exit(app.exec())