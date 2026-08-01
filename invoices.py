import sys
import os
import sqlite3
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel, QFileDialog, QMessageBox,
    QHeaderView, QSplitter
)
from PySide6.QtCore import Qt

DB_NAME = "supermarket.db"
REPORTS_FOLDER = "exported_invoices"
os.makedirs(REPORTS_FOLDER, exist_ok=True)

class PreviousInvoicesWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📁 عرض الفواتير السابقة")
        self.setGeometry(200, 150, 1100, 700)

        self.setStyleSheet("""
            QWidget { background-color: #12121c; color: #dddddd; font-family: 'Segoe UI'; }
            QSplitter::handle { background-color: #444466; }
            QLineEdit, QComboBox {
                background-color: #1e1e2f; border: 1px solid #444466; border-radius: 6px;
                padding: 8px; font-size: 14px; color: #eee;
            }
            QPushButton {
                background-color: #3a86ff; color: white; border-radius: 6px;
                padding: 8px 12px; font-size: 14px; font-weight: bold; border: none;
            }
            QPushButton:hover { background-color: #5599ff; }
            QPushButton#export_btn { background-color: #1D6F42; }
            QPushButton#export_btn:hover { background-color: #27ae60; }
            QTableWidget {
                background-color: #1e1e2f; gridline-color: #444466;
                font-size: 13px; border-radius: 6px;
            }
            QHeaderView::section {
                background-color: #2a2a4a; color: #aaccff; padding: 6px;
                font-weight: bold; border: 1px solid #444466;
            }
            QLabel { font-size: 14px; }
        """)

        # --- التصميم الرئيسي ---
        layout = QVBoxLayout(self)
        
        # --- شريط التحكم العلوي ---
        top_bar = QHBoxLayout()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["مبيعات", "مشتريات", "مرتجعات"])
        self.search_input = QLineEdit(placeholderText="🔍 ابحث بالرقم، التاريخ، اسم العميل/المورد...")
        self.search_button = QPushButton("بحث")
        self.export_button = QPushButton("📄 تصدير إلى Excel")
        self.export_button.setObjectName("export_btn")

        top_bar.addWidget(QLabel("نوع الفاتورة:"))
        top_bar.addWidget(self.type_combo)
        top_bar.addWidget(self.search_input, 1)
        top_bar.addWidget(self.search_button)
        top_bar.addWidget(self.export_button)
        layout.addLayout(top_bar)

        # --- مقسم الواجهة (للفواتير والأصناف) ---
        splitter = QSplitter(Qt.Vertical)
        
        # --- جدول الفواتير (الجزء العلوي) ---
        self.invoices_table = QTableWidget()
        self.invoices_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.invoices_table.setEditTriggers(QTableWidget.NoEditTriggers)
        splitter.addWidget(self.invoices_table)

        # --- جدول الأصناف (الجزء السفلي) ---
        self.items_table = QTableWidget()
        self.items_table.setEditTriggers(QTableWidget.NoEditTriggers)
        splitter.addWidget(self.items_table)

        splitter.setSizes([400, 300]) # تحديد الأحجام الأولية للجزئين
        layout.addWidget(splitter)
        self.setLayout(layout)

        # --- ربط الإشارات (Signals) ---
        self.search_button.clicked.connect(self.search_invoices)
        self.type_combo.currentIndexChanged.connect(self.search_invoices)
        self.invoices_table.itemSelectionChanged.connect(self.load_invoice_details)
        self.export_button.clicked.connect(self.export_to_excel)

        # تحميل البيانات الأولية
        self.search_invoices()

    def connect_db(self):
        return sqlite3.connect(DB_NAME)

    def search_invoices(self):
        invoice_type = self.type_combo.currentText()
        search_term = f"%{self.search_input.text().strip()}%"
        
        conn = self.connect_db()
        query = ""
        params = ()

        if invoice_type == "مبيعات":
            self.invoices_table.setColumnCount(6)
            self.invoices_table.setHorizontalHeaderLabels(["ID", "رقم الفاتورة", "التاريخ", "العميل", "الإجمالي", "المدفوع"])
            query = """
                SELECT inv.id, inv.invoice_number, inv.date, c.name, inv.total, inv.paid_amount
                FROM sales_invoices inv
                LEFT JOIN customers c ON inv.customer_id = c.id
                WHERE inv.invoice_number LIKE ? OR inv.date LIKE ? OR c.name LIKE ?
                ORDER BY inv.id DESC
            """
            params = (search_term, search_term, search_term)

        elif invoice_type == "مشتريات":
            self.invoices_table.setColumnCount(6)
            self.invoices_table.setHorizontalHeaderLabels(["ID", "رقم الفاتورة", "التاريخ", "المورد", "الإجمالي", "المدفوع"])
            query = """
                SELECT inv.id, inv.invoice_number, inv.date, s.name, inv.total, inv.paid_amount
                FROM purchase_invoices inv
                LEFT JOIN suppliers s ON inv.supplier_id = s.id
                WHERE inv.invoice_number LIKE ? OR inv.date LIKE ? OR s.name LIKE ?
                ORDER BY inv.id DESC
            """
            params = (search_term, search_term, search_term)

        else: # مرتجعات
            self.invoices_table.setColumnCount(4)
            self.invoices_table.setHorizontalHeaderLabels(["ID", "التاريخ", "النوع", "الفاتورة الأصلية"])
            query = "SELECT id, date, type, reference_invoice_id FROM returns ORDER BY id DESC"
            # البحث في المرتجعات مبسط هنا، يمكن تطويره إذا لزم الأمر
            
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            self.populate_table(self.invoices_table, results)
            self.invoices_table.setColumnHidden(0, True) # إخفاء عمود الـ ID
            self.items_table.setRowCount(0) # مسح جدول الأصناف
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء البحث: {e}")
        finally:
            conn.close()

    def load_invoice_details(self):
        selected_rows = self.invoices_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        selected_row = selected_rows[0].row()
        invoice_id = self.invoices_table.item(selected_row, 0).text()
        invoice_type = self.type_combo.currentText()
        
        conn = self.connect_db()
        query = ""
        params = (invoice_id,)

        if invoice_type == "مبيعات":
            self.items_table.setColumnCount(4)
            self.items_table.setHorizontalHeaderLabels(["المنتج", "الكمية", "سعر الوحدة", "الإجمالي"])
            query = """
                SELECT p.name, si.quantity, si.unit_price, si.total_price
                FROM sales_items si
                JOIN products p ON si.product_id = p.id
                WHERE si.invoice_id = ?
            """
        elif invoice_type == "مشتريات":
            self.items_table.setColumnCount(4)
            self.items_table.setHorizontalHeaderLabels(["المنتج", "الكمية (وحدة)", "سعر الوحدة", "الإجمالي"])
            query = """
                SELECT p.name, pi.quantity_units, pi.unit_price, pi.total_price
                FROM purchase_items pi
                JOIN products p ON pi.product_id = p.id
                WHERE pi.invoice_id = ?
            """
        else: # مرتجعات
            self.items_table.setColumnCount(4)
            self.items_table.setHorizontalHeaderLabels(["المنتج", "الكمية المرتجعة", "السعر", "الإجمالي"])
            query = """
                SELECT p.name, ri.quantity, ri.price, (ri.quantity * ri.price)
                FROM return_items ri
                JOIN products p ON ri.product_id = p.id
                WHERE ri.return_id = ?
            """

        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            self.populate_table(self.items_table, results)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تحميل تفاصيل الفاتورة: {e}")
        finally:
            conn.close()
            
    def populate_table(self, table, data):
        table.setRowCount(0)
        for row_idx, row_data in enumerate(data):
            table.insertRow(row_idx)
            for col_idx, col_data in enumerate(row_data):
                item = QTableWidgetItem(str(col_data))
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row_idx, col_idx, item)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def export_to_excel(self):
        selected_rows = self.invoices_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "تنبيه", "يرجى تحديد فاتورة لتصديرها.")
            return

        selected_row = selected_rows[0].row()
        invoice_id = self.invoices_table.item(selected_row, 0).text()
        invoice_num = self.invoices_table.item(selected_row, 1).text()
        invoice_type = self.type_combo.currentText()

        # جلب بيانات الفاتورة الرئيسية والأصناف باستخدام pandas
        conn = self.connect_db()
        try:
            if invoice_type == "مبيعات":
                df_invoice = pd.read_sql_query("SELECT inv.invoice_number, inv.date, c.name as customer, inv.total, inv.discount, inv.tax, inv.paid_amount FROM sales_invoices inv LEFT JOIN customers c ON inv.customer_id = c.id WHERE inv.id = ?", conn, params=(invoice_id,))
                df_items = pd.read_sql_query("SELECT p.name as product, si.quantity, si.unit_price, si.total_price FROM sales_items si JOIN products p ON si.product_id = p.id WHERE si.invoice_id = ?", conn, params=(invoice_id,))
            elif invoice_type == "مشتريات":
                df_invoice = pd.read_sql_query("SELECT inv.invoice_number, inv.date, s.name as supplier, inv.total, inv.discount, inv.tax, inv.paid_amount FROM purchase_invoices inv LEFT JOIN suppliers s ON inv.supplier_id = s.id WHERE inv.id = ?", conn, params=(invoice_id,))
                df_items = pd.read_sql_query("SELECT p.name as product, pi.quantity_units, pi.unit_price, pi.total_price FROM purchase_items pi JOIN products p ON pi.product_id = p.id WHERE pi.invoice_id = ?", conn, params=(invoice_id,))
            else: # مرتجعات
                df_invoice = pd.read_sql_query("SELECT id, date, type, reference_invoice_id FROM returns WHERE id = ?", conn, params=(invoice_id,))
                df_items = pd.read_sql_query("SELECT p.name as product, ri.quantity, ri.price, (ri.quantity * ri.price) as total FROM return_items ri JOIN products p ON ri.product_id = p.id WHERE ri.return_id = ?", conn, params=(invoice_id,))
        finally:
            conn.close()

        # حفظ إلى ملف Excel
        default_filename = os.path.join(REPORTS_FOLDER, f"Invoice_{invoice_num.replace('/', '_')}.xlsx")
        filename, _ = QFileDialog.getSaveFileName(self, "حفظ كـ Excel", default_filename, "Excel Files (*.xlsx)")
        
        if filename:
            try:
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    df_invoice.to_excel(writer, sheet_name='Invoice Summary', index=False)
                    df_items.to_excel(writer, sheet_name='Invoice Items', index=False)
                QMessageBox.information(self, "نجاح", f"تم تصدير الفاتورة بنجاح إلى:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل تصدير الملف: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PreviousInvoicesWindow()
    window.show()
    sys.exit(app.exec())