import sys
import sqlite3
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QMessageBox, QHeaderView, QTabWidget, QFormLayout,
    QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt
from PySide6.QtCore import QDate
DB_NAME = "supermarket.db"

# --- نافذة منبثقة للمعاملات اليدوية ---
class TransactionDialog(QDialog):
    def __init__(self, accounts, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إضافة معاملة مالية")
        self.setMinimumWidth(400)
        self.setStyleSheet(parent.styleSheet())

        layout = QFormLayout(self)
        self.transaction_type = QComboBox()
        self.transaction_type.addItems(["إيداع في الصندوق/البنك", "تسجيل مصروفات", "سداد لمورد", "تحصيل من عميل"])
        self.account_combo = QComboBox()
        # فلترة الحسابات حسب نوع العملية
        self.accounts = accounts
        self.transaction_type.currentIndexChanged.connect(self.filter_accounts)
        
        self.amount_input = QLineEdit(placeholderText="0.00")
        self.desc_input = QLineEdit(placeholderText="وصف العملية (اختياري)")

        layout.addRow("نوع العملية:", self.transaction_type)
        layout.addRow("الحساب:", self.account_combo)
        layout.addRow("المبلغ:", self.amount_input)
        layout.addRow("الوصف:", self.desc_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)
        self.filter_accounts() # استدعاء أولي لفلترة الحسابات

    def filter_accounts(self):
        self.account_combo.clear()
        current_type = self.transaction_type.currentText()
        
        if current_type == "إيداع في الصندوق/البنك":
            # يمكن الإيداع فقط في الأصول (الصندوق، البنك)
            filtered = [acc['name'] for acc in self.accounts if acc['type'] == 'أصل']
        elif current_type == "تسجيل مصروفات":
            # يمكن تسجيل المصروفات فقط على حسابات المصروفات
            filtered = [acc['name'] for acc in self.accounts if acc['type'] == 'مصروف']
        else: # سداد وتحصيل
            # يمكن استخدام أي حساب
            filtered = [acc['name'] for acc in self.accounts]
            
        self.account_combo.addItems(filtered)

    def get_data(self):
        return {
            "type": self.transaction_type.currentText(),
            "account": self.account_combo.currentText(),
            "amount": self.amount_input.text(),
            "description": self.desc_input.text()
        }

# --- الواجهة الرئيسية للحسابات ---
class AccountingWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("💼 الحسابات العامة (شجرة الحسابات)")
        self.setGeometry(200, 100, 1100, 700)
        self.accounts_list = []

        self.setStyleSheet("""
            QWidget { background-color: #12121c; color: #eee; font-family: 'Segoe UI'; }
            QTabWidget::pane { border: none; background-color: #1e1e2f; }
            QLabel { font-size: 14px; }
            QLineEdit, QComboBox {
                background-color: #2d2d44; color: #fff; padding: 8px;
                border-radius: 6px; border: 1px solid #444; font-size: 14px;
            }
            QPushButton {
                background-color: #00b894; color: white; padding: 10px;
                font-weight: bold; border-radius: 6px; border: none;
            }
            QPushButton:hover { background-color: #55efc4; }
            QTableWidget {
                background-color: #1e1e2f; color: white; gridline-color: #3a3a6f;
                border: 1px solid #3a3a6f; font-size: 13px;
            }
            QHeaderView::section {
                background-color: #2a2a4a; color: #aaccff; padding: 6px;
                font-weight: bold; border: 1px solid #3a3a6f;
            }
            QLabel#balance_status {
                font-weight: bold; font-size: 16px; padding: 10px; border-radius: 6px;
            }
            QLabel#balance_status[balanced="true"] { color: #2ecc71; background-color: rgba(46, 204, 113, 0.1); }
            QLabel#balance_status[balanced="false"] { color: #e74c3c; background-color: rgba(231, 76, 60, 0.1); }
        """)

        main_layout = QVBoxLayout(self)
        
        # --- شريط الأدوات العلوي ---
        top_bar = QHBoxLayout()
        self.add_transaction_btn = QPushButton("➕ معاملة يدوية (إيداع/مصروف/سداد)")
        self.add_transaction_btn.clicked.connect(self.open_transaction_dialog)
        self.refresh_btn = QPushButton("🔄 تحديث الأرصدة")
        self.refresh_btn.clicked.connect(self.calculate_all_balances)
        
        top_bar.addWidget(self.add_transaction_btn)
        top_bar.addStretch()
        top_bar.addWidget(self.refresh_btn)
        main_layout.addLayout(top_bar)

        # --- جدول ملخص الحسابات ---
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(5)
        self.accounts_table.setHorizontalHeaderLabels(["الحساب", "النوع", "إجمالي مدين", "إجمالي دائن", "الرصيد النهائي"])
        self.accounts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.accounts_table)
        
        # --- شريط الإجماليات السفلي ---
        bottom_bar = QHBoxLayout()
        self.total_debit_label = QLabel("إجمالي المدين: 0.00")
        self.total_credit_label = QLabel("إجمالي الدائن: 0.00")
        self.balance_status_label = QLabel("الحالة: متزن")
        self.balance_status_label.setObjectName("balance_status")
        
        for label in [self.total_debit_label, self.total_credit_label, self.balance_status_label]:
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 8px; background-color: #2a2a4a; border-radius: 6px;")
        
        bottom_bar.addWidget(self.total_debit_label, 1)
        bottom_bar.addWidget(self.total_credit_label, 1)
        bottom_bar.addWidget(self.balance_status_label, 1)
        main_layout.addLayout(bottom_bar)

        self.load_accounts_from_db()
        self.calculate_all_balances()

    def connect_db(self):
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    def load_accounts_from_db(self):
        conn = self.connect_db()
        try:
            # جلب كل الحسابات مع أنواعها وتخزينها
            self.accounts_list = pd.read_sql_query("SELECT name, type FROM chart_of_accounts", conn).to_dict('records')
        finally:
            conn.close()

    def calculate_all_balances(self):
        self.accounts_table.setRowCount(0)
        conn = self.connect_db()
        try:
            # 1. جلب كل القيود اليدوية
            manual_entries = pd.read_sql_query("SELECT * FROM journal_entries", conn)
            
            # 2. حساب الإجماليات من الفواتير مباشرة
            sales_total = pd.read_sql_query("SELECT SUM(total) as total FROM sales_invoices", conn).iloc[0]['total'] or 0
            purchases_total = pd.read_sql_query("SELECT SUM(total) as total FROM purchase_invoices", conn).iloc[0]['total'] or 0
            # (يمكن إضافة المرتجعات هنا بنفس الطريقة إذا أردت)

            # 3. تجميع كل الحركات
            balances = {acc['name']: {'debit': 0, 'credit': 0} for acc in self.accounts_list}
            
            # إضافة القيود اليدوية
            for _, row in manual_entries.iterrows():
                if row['debit_account'] in balances:
                    balances[row['debit_account']]['debit'] += row['amount']
                if row['credit_account'] in balances:
                    balances[row['credit_account']]['credit'] += row['amount']
            
            # إضافة حركات الفواتير التلقائية
            if 'المبيعات' in balances:
                balances['المبيعات']['credit'] += sales_total
            if 'الصندوق' in balances: # افتراض أن المبيعات النقدية تذهب للصندوق
                balances['الصندوق']['debit'] += sales_total
                
            if 'المخزون' in balances:
                balances['المخزون']['debit'] += purchases_total
            if 'الموردون (الذمم الدائنة)' in balances:
                balances['الموردون (الذمم الدائنة)']['credit'] += purchases_total

            # 4. عرض النتائج في الجدول
            grand_total_debit = 0
            grand_total_credit = 0

            for acc in self.accounts_list:
                acc_name = acc['name']
                acc_type = acc['type']
                acc_balance = balances.get(acc_name, {'debit': 0, 'credit': 0})
                
                total_debit = acc_balance['debit']
                total_credit = acc_balance['credit']
                
                balance = 0
                if acc_type in ['أصل', 'مصروف']:
                    balance = total_debit - total_credit
                else: # التزام، إيراد، حقوق ملكية
                    balance = total_credit - total_debit

                row_idx = self.accounts_table.rowCount()
                self.accounts_table.insertRow(row_idx)
                self.accounts_table.setItem(row_idx, 0, QTableWidgetItem(acc_name))
                self.accounts_table.setItem(row_idx, 1, QTableWidgetItem(acc_type))
                self.accounts_table.setItem(row_idx, 2, QTableWidgetItem(f"{total_debit:.2f}"))
                self.accounts_table.setItem(row_idx, 3, QTableWidgetItem(f"{total_credit:.2f}"))
                self.accounts_table.setItem(row_idx, 4, QTableWidgetItem(f"{balance:.2f}"))
                
                grand_total_debit += total_debit
                grand_total_credit += total_credit

            # 5. تحديث ملصقات الإجماليات
            self.total_debit_label.setText(f"إجمالي المدين: {grand_total_debit:.2f}")
            self.total_credit_label.setText(f"إجمالي الدائن: {grand_total_credit:.2f}")

            is_balanced = abs(grand_total_debit - grand_total_credit) < 0.01
            self.balance_status_label.setProperty("balanced", is_balanced)
            self.balance_status_label.setText("الحالة: متزن" if is_balanced else "الحالة: غير متزن!")
            self.balance_status_label.style().unpolish(self.balance_status_label)
            self.balance_status_label.style().polish(self.balance_status_label)

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء حساب الأرصدة: {e}")
        finally:
            conn.close()

    def open_transaction_dialog(self):
        dialog = TransactionDialog(self.accounts_list, self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                amount = float(data['amount'])
                if amount <= 0: raise ValueError
            except (ValueError, TypeError):
                QMessageBox.warning(self, "خطأ", "يرجى إدخال مبلغ صحيح.")
                return

            debit_acc, credit_acc = "", ""
            desc = data['description'] or data['type']

            if data['type'] == "إيداع في الصندوق/البنك":
                debit_acc = data['account']
                credit_acc = "رأس المال"
            elif data['type'] == "تسجيل مصروفات":
                debit_acc = data['account']
                credit_acc = "الصندوق"
            elif data['type'] == "سداد لمورد":
                debit_acc = "الموردون (الذمم الدائنة)"
                credit_acc = data['account']
            elif data['type'] == "تحصيل من عميل":
                debit_acc = data['account']
                credit_acc = "العملاء (الذمم المدينة)"

            self.add_manual_entry(desc, debit_acc, credit_acc, amount)

    def add_manual_entry(self, description, debit_acc, credit_acc, amount):
        conn = self.connect_db()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO journal_entries (date, description, debit_account, credit_account, amount, source)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (QDate.currentDate().toString("yyyy-MM-dd"), description, debit_acc, credit_acc, amount, "يدوي"))
            conn.commit()
            QMessageBox.information(self, "نجاح", "تم تسجيل العملية بنجاح.")
            self.calculate_all_balances() # تحديث الواجهة مباشرة
        except sqlite3.Error as e:
            QMessageBox.critical(self, "خطأ قاعدة البيانات", str(e))
        finally:
            conn.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AccountingWindow()
    window.show()
    sys.exit(app.exec())