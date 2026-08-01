import sys
import sqlite3
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)

DB_NAME = "supermarket.db"

class InventoryWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📦 إدارة المخزون")
        self.setGeometry(200, 100, 1200, 600)

        self.setStyleSheet("""
            QWidget {
                background-color: #121228;
                color: #dddddd;
                font-family: 'Segoe UI';
            }
            QLineEdit {
                background-color: #1e1e2f;
                border: 1px solid #444466;
                border-radius: 6px;
                padding: 6px;
                font-size: 14px;
                color: #eee;
            }
            QPushButton {
                background-color: #3a86ff;
                color: white;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5599ff;
            }
            QTableWidget {
                background-color: #1e1e2f;
                gridline-color: #444466;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #2a2a4a;
                color: #aaccff;
                padding: 5px;
                font-weight: bold;
                border: 1px solid #444466;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.create_top_bar()
        self.create_table()
        self.load_inventory() # تحميل كل المنتجات عند الفتح

    def create_top_bar(self):
        top_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 ابحث باسم المنتج أو الباركود...")
        # [تحسين] البحث يتنفذ عند الضغط على Enter أو تغيير النص
        self.search_input.returnPressed.connect(self.search_inventory)
        self.search_input.textChanged.connect(self.search_inventory)

        self.refresh_btn = QPushButton("🔄 تحديث وعرض الكل")
        self.refresh_btn.clicked.connect(self.clear_search_and_refresh)

        top_layout.addWidget(self.search_input)
        top_layout.addWidget(self.refresh_btn)

        self.layout.addLayout(top_layout)
    
    def clear_search_and_refresh(self):
        self.search_input.clear() # مسح البحث يؤدي تلقائياً للتحديث بسبب textChanged
        self.load_inventory()

    def create_table(self):
        self.table = QTableWidget()
        # [تحسين] إضافة عمود لإجمالي الكمية بالحبات
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "اسم المنتج", "الوحدة", "حبات/وحدة",
            "كمية الكراتين", "حبات متبقية", "إجمالي الحبات", "الحد الأدنى (كرتون)",
            "تاريخ الانتهاء", "الحالة"
        ])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)

    def connect_db(self):
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    def search_inventory(self):
        keyword = self.search_input.text().strip()
        self.load_inventory(keyword)

    def load_inventory(self, keyword=None):
        self.table.setRowCount(0)
        conn = self.connect_db()
        cur = conn.cursor()

        # [تحسين] دمج دالتي البحث والتحميل في دالة واحدة
        query = """
            SELECT 
                p.id, p.name, u.name as unit_name,
                p.items_per_unit, p.quantity_units, 
                p.quantity_items, p.min_quantity, p.expiry_date, p.barcode
            FROM products p
            LEFT JOIN units u ON p.unit_id = u.id
        """
        params = []
        if keyword:
            query += " WHERE p.name LIKE ? OR p.barcode LIKE ?"
            params.extend([f"%{keyword}%", f"%{keyword}%"])

        cur.execute(query, params)
        rows = cur.fetchall()

        for row in rows:
            self.populate_table_row(row)

        conn.close()
        
    def populate_table_row(self, row_data):
        row_index = self.table.rowCount()
        self.table.insertRow(row_index)

        # --- [التصحيح الحسابي والمنطقي الرئيسي] ---
        
        # 1. حساب الكميات الفعلية
        quantity_units = row_data['quantity_units']
        quantity_items = row_data['quantity_items']
        items_per_unit = row_data['items_per_unit']
        min_quantity_units = row_data['min_quantity'] # الحد الأدنى بالكراتين
        
        # حساب إجمالي الكمية بالحبات
        total_items = (quantity_units * items_per_unit) + quantity_items
        
        # حساب الحد الأدنى بالحبات
        min_items_threshold = min_quantity_units * items_per_unit

        # 2. تحديد الحالة بناءً على المنطق الصحيح
        status = ""
        if total_items <= 0:
            status = "❌ منتهي"
        elif total_items <= min_items_threshold:
            status = "⚠️ ناقص"
        else:
            status = "✅ متوفر"

        # 3. تعبئة الجدول بالبيانات الصحيحة
        self.table.setItem(row_index, 0, QTableWidgetItem(str(row_data['id'])))
        self.table.setItem(row_index, 1, QTableWidgetItem(row_data['name']))
        self.table.setItem(row_index, 2, QTableWidgetItem(row_data['unit_name'] or 'N/A'))
        self.table.setItem(row_index, 3, QTableWidgetItem(str(items_per_unit)))
        self.table.setItem(row_index, 4, QTableWidgetItem(str(quantity_units)))
        self.table.setItem(row_index, 5, QTableWidgetItem(str(quantity_items)))
        self.table.setItem(row_index, 6, QTableWidgetItem(str(total_items))) # عرض إجمالي الحبات
        self.table.setItem(row_index, 7, QTableWidgetItem(str(min_quantity_units)))
        self.table.setItem(row_index, 8, QTableWidgetItem(row_data['expiry_date'] or 'لا يوجد'))
        self.table.setItem(row_index, 9, QTableWidgetItem(status))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InventoryWindow()
    window.show()
    sys.exit(app.exec())