# هذا هو الكود الكامل والمحدث لوحدة المرتجعات

import sys
import os
import sqlite3
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QMessageBox, QHeaderView, QSpinBox, QFrame
)
from PySide6.QtCore import Qt

DB_NAME = "supermarket.db"
REFUND_FOLDER = "refunds"
os.makedirs(REFUND_FOLDER, exist_ok=True)

class ReturnsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔄 وحدة المرتجعات")
        self.setGeometry(300, 150, 950, 550)
        self.invoice_items = []

        self.setStyleSheet("""
            QWidget {
                background-color: #12121c;
                color: #dddddd;
                font-family: 'Segoe UI';
            }
            QLabel {
                font-size: 14px;
                font-weight: bold;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #1e1e2f;
                border: 1px solid #444466;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                color: #eee;
            }
            QPushButton {
                border-radius: 6px;
                padding: 10px 15px;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }
            QPushButton#load_button {
                background-color: #3a86ff;
                color: white;
            }
            QPushButton#load_button:hover {
                background-color: #5599ff;
            }
            QPushButton#process_button {
                background-color: #e74c3c;
                color: white;
            }
            QPushButton#process_button:hover {
                background-color: #c0392b;
            }
            QTableWidget {
                background-color: #1e1e2f;
                gridline-color: #444466;
                font-size: 13px;
                border-radius: 6px;
            }
            QHeaderView::section {
                background-color: #2a2a4a;
                color: #aaccff;
                padding: 6px;
                font-weight: bold;
                border: 1px solid #444466;
            }
            QFrame#top_frame {
                background-color: #1e1e2f;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        top_frame = QFrame()
        top_frame.setObjectName("top_frame")
        top_bar = QHBoxLayout(top_frame)
        top_bar.addWidget(QLabel("نوع الفاتورة:"))
        self.invoice_type_combo = QComboBox()
        self.invoice_type_combo.addItems(["مبيعات", "مشتريات"])
        top_bar.addWidget(self.invoice_type_combo)
        top_bar.addWidget(QLabel("رقم الفاتورة أو ID:"))
        self.invoice_number_input = QLineEdit(placeholderText="مثال: 1 أو INV-2023...")
        top_bar.addWidget(self.invoice_number_input, 1)
        self.load_button = QPushButton("📥 تحميل الفاتورة")
        self.load_button.setObjectName("load_button")
        self.load_button.clicked.connect(self.load_invoice_items)
        top_bar.addWidget(self.load_button)
        layout.addWidget(top_frame)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["اسم المنتج", "الكمية في الفاتورة", "الكمية المرتجعة", "سعر الوحدة"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.process_button = QPushButton("✅ تنفيذ المرتجع")
        self.process_button.setObjectName("process_button")
        self.process_button.setMinimumHeight(45)
        self.process_button.clicked.connect(self.process_return)
        layout.addWidget(self.process_button)
        
        self.setLayout(layout)

    def connect_db(self):
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    def load_invoice_items(self):
        self.invoice_items = []
        self.table.setRowCount(0)
        invoice_input = self.invoice_number_input.text().strip()
        invoice_type = self.invoice_type_combo.currentText()
        if not invoice_input:
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال رقم الفاتورة أو ID")
            return

        conn = self.connect_db()
        cursor = conn.cursor()
        
        query = ""
        if invoice_type == "مبيعات":
            query = """
                SELECT p.id as product_id, p.name, si.quantity, si.unit_price, inv.id as invoice_id, inv.customer_id, p.items_per_unit
                FROM sales_items si
                JOIN products p ON p.id = si.product_id
                JOIN sales_invoices inv ON inv.id = si.invoice_id
                WHERE inv.invoice_number = ? OR inv.id = ? 
            """
        else: # مشتريات
            query = """
                SELECT p.id as product_id, p.name, pi.quantity_units as quantity, pi.unit_price, inv.id as invoice_id, inv.supplier_id
                FROM purchase_items pi
                JOIN products p ON p.id = pi.product_id
                JOIN purchase_invoices inv ON inv.id = pi.invoice_id
                WHERE inv.invoice_number = ? OR inv.id = ?
            """
        
        cursor.execute(query, (invoice_input, invoice_input))
        results = cursor.fetchall()
        
        if not results:
            QMessageBox.warning(self, "غير موجودة", "لم يتم العثور على فاتورة بهذا الرقم أو الـ ID.")
            conn.close()
            return
            
        self.invoice_items = [dict(row) for row in results]
        
        for item in self.invoice_items:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(item['name']))
            
            unit_label = "حبة" if invoice_type == "مبيعات" else "وحدة/كرتون"
            self.table.setItem(row_idx, 1, QTableWidgetItem(f"{item['quantity']} {unit_label}"))
            
            qty_spinbox = QSpinBox()
            qty_spinbox.setRange(0, int(item['quantity']))
            self.table.setCellWidget(row_idx, 2, qty_spinbox)
            self.table.setItem(row_idx, 3, QTableWidgetItem(f"{item['unit_price']:.2f}"))

        conn.close()

    def process_return(self):
        if not self.invoice_items:
            QMessageBox.warning(self, "خطأ", "يرجى تحميل فاتورة أولاً.")
            return

        returns_to_process = []
        total_refund_value = 0
        for row, item_data in enumerate(self.invoice_items):
            returned_qty = self.table.cellWidget(row, 2).value()
            if returned_qty > 0:
                item_data['returned_qty'] = returned_qty
                returns_to_process.append(item_data)
                total_refund_value += returned_qty * item_data['unit_price']

        if not returns_to_process:
            QMessageBox.information(self, "لا يوجد", "لم يتم تحديد أي كميات للإرجاع.")
            return

        invoice_type_text = self.invoice_type_combo.currentText()
        invoice_type_db = 'sale' if invoice_type_text == 'مبيعات' else 'purchase'
        invoice_id = returns_to_process[0]['invoice_id']
        
        conn = self.connect_db()
        cursor = conn.cursor()
        try:
            # 1. تسجيل المرتجع الأساسي
            cursor.execute("""
                INSERT INTO returns (type, reference_invoice_id, reason, date) 
                VALUES (?, ?, ?, ?)
                """, 
                (invoice_type_db, invoice_id, "مرتجع من واجهة النظام", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            return_id = cursor.lastrowid
            
            # 2. تسجيل أصناف المرتجع وتحديث المخزون
            for item in returns_to_process:
                cursor.execute("INSERT INTO return_items (return_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                               (return_id, item['product_id'], item['returned_qty'], item['unit_price']))
                
                if invoice_type_text == "مبيعات":
                    cursor.execute("""
                        UPDATE products SET 
                        quantity_items = ((quantity_units * items_per_unit + quantity_items) + ?) % items_per_unit, 
                        quantity_units = CAST(((quantity_units * items_per_unit + quantity_items) + ?) / items_per_unit AS INTEGER)
                        WHERE id = ?""", 
                        (item['returned_qty'], item['returned_qty'], item['product_id']))
                else: # مشتريات
                    cursor.execute("UPDATE products SET quantity_units = quantity_units - ? WHERE id = ?",
                                   (item['returned_qty'], item['product_id']))

            # 3. تحديث الأرصدة وتسجيل القيد المحاسبي
            debit_acc, credit_acc = "", ""
            if invoice_type_text == 'مبيعات':
                debit_acc = "مرتجعات المبيعات"
                credit_acc = "حساب العملاء" # أو الصندوق
                customer_id = returns_to_process[0].get('customer_id')
                if customer_id:
                    cursor.execute("UPDATE customers SET balance = balance - ? WHERE id = ?", (total_refund_value, customer_id))
            else: # مشتريات
                debit_acc = "حساب الموردين"
                credit_acc = "مرتجعات المشتريات"
                supplier_id = returns_to_process[0].get('supplier_id')
                if supplier_id:
                    cursor.execute("UPDATE suppliers SET balance = balance - ? WHERE id = ?", (total_refund_value, supplier_id))
            
            # [إعادة إضافة] تسجيل القيد في جدول القيود اليومية
            cursor.execute("""
                INSERT INTO journal_entries (date, description, debit_account, credit_account, amount, source)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (datetime.now().strftime("%Y-%m-%d"), f"مرتجع فاتورة {invoice_type_text} رقم {self.invoice_number_input.text()}", 
                  debit_acc, credit_acc, total_refund_value, "مرتجعات"))

            conn.commit()
            
            # 4. طباعة الإيصال
            receipt_id = f"RTN-{return_id}"
            self.print_return_receipt(receipt_id, invoice_type_text, self.invoice_number_input.text(), returns_to_process, total_refund_value)
            
            QMessageBox.information(self, "نجاح", f"تم تنفيذ المرتجع بنجاح.\nتم حفظ إيصال المرتجع برقم {receipt_id}")
            self.reset_form()

        except sqlite3.Error as e:
            conn.rollback()
            QMessageBox.critical(self, "خطأ في قاعدة البيانات", f"فشلت العملية. تم التراجع عن كافة التغييرات.\nالخطأ: {e}")
        finally:
            conn.close()

    def print_return_receipt(self, receipt_id, invoice_type, original_invoice, items, total_value):
        filename = os.path.join(REFUND_FOLDER, f"{receipt_id}.txt")
        WIDTH = 42

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("سوبرماركت XYZ\n".center(WIDTH + 10))
                f.write("=" * WIDTH + "\n")
                f.write(f"إيصال مرتجع {invoice_type}\n".center(WIDTH + 10))
                f.write("-" * WIDTH + "\n")

                f.write(f"رقم المرتجع: {receipt_id}\n")
                f.write(f"التاريخ: {datetime.now().strftime('%d-%m-%Y %I:%M %p')}\n")
                f.write(f"الفاتورة الأصلية: {original_invoice}\n")
                f.write("-" * WIDTH + "\n")

                f.write(f"{'الإجمالي'.ljust(9)} {'السعر'.ljust(9)} {'الكمية'.ljust(7)} {'الصنف'.ljust(15)}\n")
                f.write("-" * WIDTH + "\n")
                
                for item in items:
                    name = item['name']
                    if len(name) > 14: name = name[:13] + "."
                    
                    qty = str(item['returned_qty'])
                    price = f"{item['unit_price']:.2f}"
                    item_total = item['returned_qty'] * item['unit_price']
                    item_total_str = f"{item_total:.2f}"

                    line = f"{item_total_str.ljust(9)} {price.ljust(9)} {qty.ljust(7)} {name.ljust(15)}\n"
                    f.write(line)
                
                f.write("=" * WIDTH + "\n")
                f.write(f"{f'{total_value:.2f}'.rjust(12)} :إجمالي قيمة المرتجع\n")
                f.write("=" * WIDTH + "\n")

        except IOError as e:
            QMessageBox.critical(self, "خطأ في الطباعة", f"فشل حفظ ملف الإيصال.\nالخطأ: {e}")

    def reset_form(self):
        self.invoice_items = []
        self.table.setRowCount(0)
        self.invoice_number_input.clear()
        self.invoice_number_input.setFocus()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ReturnsWindow()
    window.show()
    sys.exit(app.exec())