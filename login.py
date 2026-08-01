# login.py
from PySide6.QtWidgets import (
    QApplication, QWidget, QLineEdit, QLabel, QPushButton, QVBoxLayout, QMessageBox
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
import sys
import sqlite3

from database import initialize_database, create_connection
from dashboard import DashboardWindow

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔐 تسجيل الدخول")
        self.setGeometry(100, 100, 400, 250)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2f;
                color: #ffffff;
                font-family: 'Segoe UI';
                font-size: 14px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #444;
                border-radius: 6px;
                background-color: #2e2e3e;
                color: #fff;
            }
            QPushButton {
                background-color: #008cff;
                padding: 10px;
                border-radius: 6px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005fff;
            }
        """)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        title = QLabel("تسجيل الدخول")
        title.setFont(QFont("Segoe UI", 18))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("اسم المستخدم")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("كلمة المرور")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.login_btn = QPushButton("تسجيل الدخول")
        self.login_btn.clicked.connect(self.login)
        layout.addWidget(self.login_btn)

        self.setLayout(layout)

    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال اسم المستخدم وكلمة المرور.")
            return

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, role, permissions 
            FROM users 
            WHERE username=? AND password=? AND is_active=1
        """, (username, password))
        result = cursor.fetchone()

        if result:
            user_id, username, role, permissions = result

            # سجل الدخول في جدول login_logs
            cursor.execute("INSERT INTO login_logs (user_id) VALUES (?)", (user_id,))
            conn.commit()
            conn.close()

            self.hide()
            self.dashboard = DashboardWindow(
                login_window=self,
                user_info={
                    "user_id": user_id,
                    "username": username,
                    "role": role,
                    "permissions": permissions if permissions != "all" else "users,products,inventory,pos,purchases,suppliers,employees,accounting,reports,invoices,returns,settings"
                }
            )
            self.dashboard.show()
        else:
            conn.close()
            QMessageBox.critical(self, "خطأ", "اسم المستخدم أو كلمة المرور غير صحيحة أو الحساب غير مفعل.")

if __name__ == "__main__":
    initialize_database()
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())