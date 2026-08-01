import sys
import sqlite3
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout,
    QHeaderView, QMessageBox, QDialog
)

# تأكد من أن هذا هو اسم ملف قاعدة البيانات الصحيح
DB_NAME = "supermarket.db"

class AddDialog(QDialog):
    """
    نافذة منبثقة بسيطة لإضافة عنصر جديد (فئة أو وحدة)
    """
    def __init__(self, title, table_name):
        super().__init__()
        self.setWindowTitle(f"إضافة {title}")
        self.setFixedSize(320, 120)
        self.table_name = table_name

        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2f;
                color: #ffffff;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #2e2e3f;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #3a86ff;
                color: white;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #5599ff;
            }
        """)

        layout = QVBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText(f"أدخل اسم {title}")
        self.add_btn = QPushButton("إضافة")
        self.add_btn.clicked.connect(self.add_item)

        layout.addWidget(self.input)
        layout.addWidget(self.add_btn)
        self.setLayout(layout)

    def add_item(self):
        name = self.input.text().strip()
        if not name:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال اسم صالح.")
            return
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        try:
            cur.execute(f"INSERT INTO {self.table_name} (name) VALUES (?)", (name,))
            conn.commit()
            self.accept()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "مكرر", f"الاسم '{name}' موجود مسبقًا.")
        finally:
            conn.close()


class ProductsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🛒 إدارة المنتجات")
        self.setGeometry(200, 100, 1200, 650)

        self.setStyleSheet("""
            QWidget {
                background-color: #121228;
                color: #ddd;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            QLabel {
                font-size: 16px;
                font-weight: bold;
            }
            QLineEdit, QComboBox {
                background-color: #1f1f3f;
                border: 1px solid #3a3a6f;
                border-radius: 6px;
                padding: 6px;
                font-size: 14px;
                color: #eee;
            }
            QPushButton {
                background-color: #3a86ff;
                color: white;
                border-radius: 7px;
                padding: 10px 15px;
                font-size: 15px;
                font-weight: bold;
                min-width: 130px;
                max-width: 150px;
            }
            QPushButton:hover {
                background-color: #5599ff;
            }
            QTableWidget {
                background-color: #1e1e2f;
                gridline-color: #444466;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #2a2a4a;
                color: #aaccff;
                padding: 6px;
                font-weight: bold;
                border: 1px solid #444466;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.create_form()
        self.create_buttons()
        self.create_table()

        self.load_categories()
        self.load_units()
        self.load_products()

    def connect_db(self):
        # [تحسين] استخدام Row factory لجلب البيانات كأسماء أعمدة لتسهيل القراءة
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    def create_form(self):
        form_layout = QHBoxLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم المنتج")

        self.category_combo = QComboBox()
        self.unit_combo = QComboBox()

        self.items_per_unit_input = QLineEdit()
        self.items_per_unit_input.setPlaceholderText("عدد الحبات في الوحدة (كرتون)")

        self.wholesale_price_input = QLineEdit()
        self.wholesale_price_input.setPlaceholderText("سعر الجملة للوحدة")

        self.retail_price_input = QLineEdit()
        self.retail_price_input.setPlaceholderText("سعر التجزئة للحبة")

        self.quantity_units_input = QLineEdit()
        self.quantity_units_input.setPlaceholderText("الكمية الأولية (بالوحدات/الكراتين)")
        
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("الباركود")

        widgets = [
            self.name_input, self.category_combo, self.unit_combo,
            self.items_per_unit_input, self.wholesale_price_input,
            self.retail_price_input, self.quantity_units_input,
            self.barcode_input
        ]

        for w in widgets:
            form_layout.addWidget(w)

        self.layout.addLayout(form_layout)

    def create_buttons(self):
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ إضافة منتج")
        self.add_btn.clicked.connect(self.add_product)

        self.unit_btn = QPushButton("➕ وحدة جديدة")
        self.unit_btn.clicked.connect(self.add_unit)

        self.cat_btn = QPushButton("➕ تصنيف جديد")
        self.cat_btn.clicked.connect(self.add_category)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.unit_btn)
        btn_layout.addWidget(self.cat_btn)
        self.layout.addLayout(btn_layout)

    def create_table(self):
        self.table = QTableWidget()
        # [تحسين] تعديل رؤوس الأعمدة لتعكس الحقيقة
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "اسم المنتج", "التصنيف", "الوحدة", "حبات/وحدة",
            "سعر الجملة", "سعر التجزئة", "كمية الوحدات", "إجمالي الكمية (حبة)", "الباركود"
        ])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)

    def load_categories(self):
        self.category_combo.clear()
        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM categories")
        rows = cur.fetchall()
        for row in rows:
            self.category_combo.addItem(row["name"], row["id"])
        conn.close()

    def load_units(self):
        self.unit_combo.clear()
        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM units")
        rows = cur.fetchall()
        for row in rows:
            self.unit_combo.addItem(row["name"], row["id"])
        conn.close()

    def add_category(self):
        dlg = AddDialog("تصنيف", "categories")
        if dlg.exec():
            self.load_categories()

    def add_unit(self):
        dlg = AddDialog("وحدة", "units")
        if dlg.exec():
            self.load_units()

    def add_product(self):
        name = self.name_input.text().strip()
        category_id = self.category_combo.currentData()
        unit_id = self.unit_combo.currentData()
        items_per_unit = self.items_per_unit_input.text().strip()
        wholesale_price = self.wholesale_price_input.text().strip()
        retail_price = self.retail_price_input.text().strip()
        quantity_units = self.quantity_units_input.text().strip()
        barcode = self.barcode_input.text().strip()

        if not all([name, category_id is not None, unit_id is not None, items_per_unit,
                    wholesale_price, retail_price]):
            QMessageBox.warning(self, "تنبيه", "يرجى تعبئة جميع الحقول.")
            return

        try:
            items_per_unit = int(items_per_unit)
            wholesale_price = float(wholesale_price)
            retail_price = float(retail_price)
            # إذا كان حقل الكمية فارغاً، نعتبره صفر
            quantity_units = int(quantity_units) if quantity_units else 0

            # --- [التصحيح الحسابي الرئيسي] ---
            # عند إضافة منتج جديد، الكمية الأولية تكون بالوحدات الكاملة (كراتين).
            # لذا، كمية الحبات المفردة (quantity_items) يجب أن تكون صفر.
            quantity_items = 0

        except ValueError:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال قيم رقمية صحيحة للأسعار والكميات.")
            return
        
        if items_per_unit <= 0:
            QMessageBox.warning(self, "خطأ", "عدد الحبات في الوحدة يجب أن يكون أكبر من صفر.")
            return

        conn = self.connect_db()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO products 
                (name, category_id, unit_id, items_per_unit, wholesale_price,
                 retail_price, quantity_units, quantity_items, barcode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, category_id, unit_id, items_per_unit, wholesale_price,
                  retail_price, quantity_units, quantity_items, barcode))
            conn.commit()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "خطأ", "الباركود أو اسم المنتج مكرر.")
            return
        finally:
            conn.close()

        self.load_products()
        self.clear_inputs()

    def load_products(self):
        self.table.setRowCount(0)
        conn = self.connect_db()
        cur = conn.cursor()
        # [تحسين] استعلام يجلب أسماء الفئات والوحدات مباشرة
        cur.execute("""
            SELECT p.id, p.name, c.name as category_name, u.name as unit_name,
                   p.items_per_unit, p.wholesale_price, p.retail_price,
                   p.quantity_units, p.quantity_items, p.barcode
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN units u ON p.unit_id = u.id
        """)
        rows = cur.fetchall()
        for row in rows:
            row_index = self.table.rowCount()
            self.table.insertRow(row_index)

            # --- [التصحيح الحسابي للعرض] ---
            # حساب إجمالي الكمية بالحبات لعرضها في الجدول
            total_items_quantity = (row['quantity_units'] * row['items_per_unit']) + row['quantity_items']
            
            # عرض البيانات في الجدول
            self.table.setItem(row_index, 0, QTableWidgetItem(str(row['id'])))
            self.table.setItem(row_index, 1, QTableWidgetItem(row['name']))
            self.table.setItem(row_index, 2, QTableWidgetItem(row['category_name'] or 'N/A'))
            self.table.setItem(row_index, 3, QTableWidgetItem(row['unit_name'] or 'N/A'))
            self.table.setItem(row_index, 4, QTableWidgetItem(str(row['items_per_unit'])))
            self.table.setItem(row_index, 5, QTableWidgetItem(str(row['wholesale_price'])))
            self.table.setItem(row_index, 6, QTableWidgetItem(str(row['retail_price'])))
            self.table.setItem(row_index, 7, QTableWidgetItem(str(row['quantity_units'])))
            # عرض الإجمالي المحسوب بدلاً من القيمة المخزنة المضللة
            self.table.setItem(row_index, 8, QTableWidgetItem(str(total_items_quantity)))
            self.table.setItem(row_index, 9, QTableWidgetItem(row['barcode']))
        
        conn.close()

    def clear_inputs(self):
        self.name_input.clear()
        self.items_per_unit_input.clear()
        self.wholesale_price_input.clear()
        self.retail_price_input.clear()
        self.quantity_units_input.clear()
        self.barcode_input.clear()
        if self.category_combo.count() > 0:
            self.category_combo.setCurrentIndex(-1) # تحسين: مسح الاختيار
        if self.unit_combo.count() > 0:
            self.unit_combo.setCurrentIndex(-1) # تحسين: مسح الاختيار


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # ملاحظة: يجب تشغيل ملف database.py مرة واحدة على الأقل لإنشاء الجداول
    window = ProductsWindow()
    window.show()
    sys.exit(app.exec())