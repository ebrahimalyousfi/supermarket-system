import sys
import sqlite3
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QFormLayout
)

DB_NAME = "supermarket.db"

class SuppliersWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🤝 إدارة الموردين")
        self.setGeometry(150, 100, 1000, 550)
        self.selected_id = None

        self.setStyleSheet("""
            QWidget { background-color: #12121c; color: #ddd; font-family: 'Segoe UI'; font-size: 13px; }
            QLabel { font-weight: bold; }
            QLineEdit { background-color: #1e1e2f; border: 1px solid #444466; border-radius: 6px; padding: 8px; color: #eee; }
            QPushButton { border-radius: 6px; padding: 8px 15px; font-weight: bold; border: none; }
            QPushButton:disabled { background-color: #555; }
            QPushButton#add_btn { background-color: #00b894; color: white; }
            QPushButton#update_btn { background-color: #f39c12; color: white; }
            QPushButton#delete_btn { background-color: #d32f2f; color: white; }
            QPushButton#clear_btn { background-color: #636e72; color: white; }
            QTableWidget { background-color: #1e1e2f; color: white; gridline-color: #444466; border-radius: 6px; }
            QHeaderView::section { background-color: #2a2a4a; color: #aaccff; font-weight: bold; border: 1px solid #444466; padding: 5px; }
        """)

        # [تحسين] التصميم الجديد: جدول في اليسار ونموذج في اليمين
        main_layout = QHBoxLayout(self)

        # Left side: Table
        table_container = QVBoxLayout()
        table_container.addWidget(QLabel("📋 قائمة الموردين"))
        self.table = QTableWidget()
        self.table.setColumnCount(5) # [تحسين] إضافة عمود الرصيد
        self.table.setHorizontalHeaderLabels(["ID", "الاسم", "الهاتف", "البريد الإلكتروني", "الرصيد (لك/عليك)"])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.cellClicked.connect(self.select_supplier)
        table_container.addWidget(self.table)
        
        # Right side: Form
        form_container = QWidget()
        form_layout = QFormLayout(form_container)
        form_layout.setSpacing(10)
        
        self.name_input = QLineEdit(placeholderText="اسم الشركة الموردة")
        self.phone_input = QLineEdit(placeholderText="رقم التواصل")
        self.email_input = QLineEdit(placeholderText="البريد الإلكتروني (اختياري)")
        self.bank_input = QLineEdit(placeholderText="رقم الحساب البنكي (اختياري)")
        
        form_layout.addRow("اسم المورد:", self.name_input)
        form_layout.addRow("رقم الهاتف:", self.phone_input)
        form_layout.addRow("البريد الإلكتروني:", self.email_input)
        form_layout.addRow("الحساب البنكي:", self.bank_input)
        
        buttons_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ إضافة"); self.add_btn.setObjectName("add_btn")
        self.update_btn = QPushButton("💾 تعديل"); self.update_btn.setObjectName("update_btn")
        self.delete_btn = QPushButton("🗑️ حذف"); self.delete_btn.setObjectName("delete_btn")
        
        self.add_btn.clicked.connect(self.add_supplier)
        self.update_btn.clicked.connect(self.update_supplier)
        self.delete_btn.clicked.connect(self.delete_supplier)

        buttons_layout.addWidget(self.add_btn)
        buttons_layout.addWidget(self.update_btn)
        buttons_layout.addWidget(self.delete_btn)
        form_layout.addRow(buttons_layout)
        
        clear_btn = QPushButton("🔄 مسح الحقول"); clear_btn.setObjectName("clear_btn")
        clear_btn.clicked.connect(self.clear_inputs)
        form_layout.addWidget(clear_btn)

        main_layout.addLayout(table_container, 2) # الجدول يأخذ ضعف مساحة النموذج
        main_layout.addWidget(form_container, 1)
        
        self.load_suppliers()

    def connect_db(self):
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    def load_suppliers(self):
        self.table.setRowCount(0)
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, phone, email, balance FROM suppliers ORDER BY name")
        for row in cursor.fetchall():
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row['id'])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(row['name']))
            self.table.setItem(row_idx, 2, QTableWidgetItem(row['phone']))
            self.table.setItem(row_idx, 3, QTableWidgetItem(row['email']))
            self.table.setItem(row_idx, 4, QTableWidgetItem(f"{row['balance']:.2f}"))
        conn.close()
        self.clear_inputs()

    def clear_inputs(self):
        self.selected_id = None
        self.name_input.clear()
        self.phone_input.clear()
        self.email_input.clear()
        self.bank_input.clear()
        self.table.clearSelection()
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

    def add_supplier(self):
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()
        bank = self.bank_input.text().strip()

        if not name:
            QMessageBox.warning(self, "بيانات ناقصة", "اسم المورد مطلوب.")
            return

        conn = self.connect_db()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO suppliers (name, phone, email, bank_account) VALUES (?, ?, ?, ?)",
                           (name, phone, email, bank))
            conn.commit()
            QMessageBox.information(self, "نجاح", f"تمت إضافة المورد '{name}' بنجاح.")
            self.load_suppliers()
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "خطأ", "اسم المورد هذا موجود بالفعل.")
        finally:
            conn.close()

    def select_supplier(self, row, col):
        self.selected_id = int(self.table.item(row, 0).text())
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM suppliers WHERE id = ?", (self.selected_id,))
        supplier_data = cursor.fetchone()
        conn.close()

        if supplier_data:
            self.name_input.setText(supplier_data['name'])
            self.phone_input.setText(supplier_data['phone'])
            self.email_input.setText(supplier_data['email'])
            self.bank_input.setText(supplier_data['bank_account'])
            self.update_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)

    def update_supplier(self):
        if not self.selected_id: return

        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()
        bank = self.bank_input.text().strip()

        conn = self.connect_db()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE suppliers SET name=?, phone=?, email=?, bank_account=? WHERE id=?",
                           (name, phone, email, bank, self.selected_id))
            conn.commit()
            self.load_suppliers()
        except sqlite3.IntegrityError:
             QMessageBox.critical(self, "خطأ", "اسم المورد هذا موجود بالفعل.")
        finally:
            conn.close()

    def delete_supplier(self):
        if not self.selected_id: return
        
        conn = self.connect_db()
        cursor = conn.cursor()
        # [تصحيح] التحقق من وجود فواتير مرتبطة قبل الحذف
        cursor.execute("SELECT 1 FROM purchase_invoices WHERE supplier_id = ?", (self.selected_id,))
        if cursor.fetchone():
            QMessageBox.critical(self, "لا يمكن الحذف", "لا يمكن حذف هذا المورد لأنه مرتبط بفواتير شراء. يمكنك تعطيله بدلاً من حذفه.")
            conn.close()
            return
            
        reply = QMessageBox.question(self, "تأكيد الحذف", "هل أنت متأكد من حذف هذا المورد نهائياً؟", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            cursor.execute("DELETE FROM suppliers WHERE id = ?", (self.selected_id,))
            conn.commit()
            self.load_suppliers()
        conn.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SuppliersWindow()
    window.show()
    sys.exit(app.exec())