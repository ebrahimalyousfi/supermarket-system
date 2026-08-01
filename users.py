from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QComboBox, QApplication
)
from PySide6.QtCore import Qt
import sqlite3
import sys

DB_NAME = "supermarket.db"

# الصلاحيات المحددة لكل دور
ROLE_PERMISSIONS = {
    "Administrator": ["users", "products", "inventory", "pos", "purchases", "suppliers", "employees", "accounting", "invoices", "returns", "reports", "settings"],
    "Sales Manager": ["pos", "invoices", "returns", "reports"],
    "Inventory Manager": ["inventory", "products", "returns"],
    "Purchasing Manager": ["purchases", "suppliers", "invoices"],
    "Accounting Manager": ["accounting", "reports"],
    "HR Manager": ["employees"],
    "Viewer": ["reports"],
}

class UsersWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("إدارة المستخدمين 👥")
        self.setGeometry(200, 100, 800, 500)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2f;
                color: white;
                font-family: 'Segoe UI';
                font-size: 14px;
            }
            QLineEdit, QComboBox {
                padding: 6px;
                border-radius: 5px;
                border: 1px solid #555;
                background-color: #2e2e3e;
                color: white;
            }
            QPushButton {
                background-color: #2d89ef;
                color: white;
                padding: 8px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1c5fb8;
            }
            QTableWidget {
                background-color: #2e2e3e;
                gridline-color: #444;
            }
            QHeaderView::section {
                background-color: #444;
                color: white;
                font-weight: bold;
            }
        """)
        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        layout = QVBoxLayout()

        form_layout = QHBoxLayout()
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("اسم المستخدم")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("كلمة المرور")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.role_input = QComboBox()
        self.role_input.addItems(ROLE_PERMISSIONS.keys())

        form_layout.addWidget(self.username_input)
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(self.role_input)
        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ إضافة")
        self.add_btn.clicked.connect(self.add_user)

        self.update_btn = QPushButton("🔄 تعديل")
        self.update_btn.setEnabled(False)
        self.update_btn.clicked.connect(self.update_user)

        self.delete_btn = QPushButton("🗑️ حذف")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_user)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.update_btn)
        btn_layout.addWidget(self.delete_btn)
        layout.addLayout(btn_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "اسم المستخدم", "الدور", "الصلاحيات", "مفعل"])
        self.table.setColumnHidden(0, True)
        self.table.cellClicked.connect(self.fill_form)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def connect_db(self):
        return sqlite3.connect(DB_NAME)

    def load_users(self):
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role, permissions, is_active FROM users")
        users = cursor.fetchall()
        conn.close()

        self.table.setRowCount(0)
        for row_data in users:
            row_num = self.table.rowCount()
            self.table.insertRow(row_num)
            for col, data in enumerate(row_data):
                item = QTableWidgetItem(str(data))
                self.table.setItem(row_num, col, item)

    def clear_inputs(self):
        self.username_input.clear()
        self.password_input.clear()
        self.role_input.setCurrentIndex(0)
        self.add_btn.setEnabled(True)
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.table.clearSelection()

    def fill_form(self, row, _):
        self.selected_id = int(self.table.item(row, 0).text())
        username = self.table.item(row, 1).text()
        role = self.table.item(row, 2).text()

        self.username_input.setText(username)
        self.password_input.setText("")
        self.role_input.setCurrentText(role)

        self.add_btn.setEnabled(False)
        self.update_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

    def add_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_input.currentText()

        if not username or not password:
            QMessageBox.warning(self, "خطأ", "يرجى ملء جميع الحقول.")
            return

        permissions = ",".join(ROLE_PERMISSIONS.get(role, []))

        conn = self.connect_db()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (username, password, role, permissions, is_active)
                VALUES (?, ?, ?, ?, 1)
            """, (username, password, role, permissions))
            conn.commit()
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "خطأ", "اسم المستخدم مستخدم بالفعل.")
        else:
            QMessageBox.information(self, "نجاح", "تمت إضافة المستخدم بنجاح.")
            self.clear_inputs()
            self.load_users()
        finally:
            conn.close()

    def update_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_input.currentText()

        if not username:
            QMessageBox.warning(self, "خطأ", "اسم المستخدم لا يمكن أن يكون فارغًا.")
            return

        permissions = ",".join(ROLE_PERMISSIONS.get(role, []))

        conn = self.connect_db()
        cursor = conn.cursor()
        if password:
            cursor.execute("""
                UPDATE users SET username=?, password=?, role=?, permissions=? WHERE id=?
            """, (username, password, role, permissions, self.selected_id))
        else:
            cursor.execute("""
                UPDATE users SET username=?, role=?, permissions=? WHERE id=?
            """, (username, role, permissions, self.selected_id))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "تم التحديث", "تم تحديث بيانات المستخدم.")
        self.clear_inputs()
        self.load_users()

    def delete_user(self):
        confirm = QMessageBox.question(self, "تأكيد الحذف", "هل تريد حذف المستخدم؟", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id=?", (self.selected_id,))
            conn.commit()
            conn.close()

            QMessageBox.information(self, "تم الحذف", "تم حذف المستخدم.")
            self.clear_inputs()
            self.load_users()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UsersWindow()
    window.show()
    sys.exit(app.exec())