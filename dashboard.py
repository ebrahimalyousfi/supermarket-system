# dashboard.py
import sys
import sqlite3
from datetime import date
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QGridLayout, QHBoxLayout, QFrame
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

# --- استيراد الوحدات (تأكد من وجود الملفات في نفس المجلد) ---
# ملاحظة: إذا كان أي ملف غير موجود، سيحدث خطأ. قم بالتعليق على الأسطر غير المستخدمة.
from users import UsersWindow
from products import ProductsWindow
from inventory import InventoryWindow
from pos import POSWindow
from purchases import PurchaseWindow # تم تصحيح اسم الملف من purchases
from suppliers import SuppliersWindow
from employees import EmployeeWindow
from accounting import AccountingWindow
from reports import ReportsWindow
from invoices import PreviousInvoicesWindow
from returns import ReturnsWindow
from settings import SettingsWindow

DB_NAME = "supermarket.db"

class DashboardWindow(QWidget):
    def __init__(self, login_window=None, user_info=None):
        super().__init__()
        self.login_window = login_window
        self.user_info = user_info or {}
        self.setWindowTitle(f"🧭 لوحة التحكم - {self.user_info.get('username', 'Guest')}")
        self.setGeometry(100, 100, 1000, 600)
        self.module_windows = {} # [تصحيح] قاموس لتخزين النوافذ المفتوحة

        self.setStyleSheet("""
            QWidget { background-color: #1e1e2f; color: #ffffff; font-family: 'Segoe UI'; }
            QLabel#title_label { font-size: 20px; font-weight: bold; color: #aaccff; }
            QLabel.stat_title { font-size: 14px; color: #aaa; }
            QLabel.stat_value { font-size: 22px; font-weight: bold; color: #00ff99; }
            QPushButton {
                background-color: #2d89ef; padding: 15px; border-radius: 8px;
                color: white; font-size: 14px; font-weight: bold; min-height: 60px;
            }
            QPushButton:hover { background-color: #4a9fff; }
            QPushButton#logout_btn { background-color: #d32f2f; }
            QPushButton#logout_btn:hover { background-color: #e57373; }
            QFrame#stat_frame { background-color: #2e2e3e; border-radius: 10px; }
        """)

        # [تصحيح] فصل الصلاحيات والتحقق من وجود "all"
        permissions_str = self.user_info.get("permissions", "")
        self.is_admin = "all" in permissions_str
        self.allowed_modules = permissions_str.split(",")
        
        self.setup_ui()
        self.update_stats()

    def connect_db(self):
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        title = QLabel(f"مرحباً {self.user_info.get('username', '')}")
        title.setObjectName("title_label")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # إنشاء مربعات الإحصائيات مع عناوين، ولكن بقيم مبدئية
        stats_layout = QHBoxLayout()
        self.sales_label = self.create_stat_box("💳 المبيعات اليومية")
        self.invoices_label = self.create_stat_box("📄 عدد فواتير اليوم")
        stats_layout.addWidget(self.sales_label)
        stats_layout.addWidget(self.invoices_label)
        main_layout.addLayout(stats_layout)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("color: #444;")
        main_layout.addWidget(separator)

        grid = QGridLayout()
        # إضافة الأزرار مع التحقق من الصلاحيات
        self.add_nav_button(grid, "👥 المستخدمون", "users", UsersWindow, 0, 0)
        self.add_nav_button(grid, "🛒 المنتجات", "products", ProductsWindow, 0, 1)
        self.add_nav_button(grid, "📦 المخزون", "inventory", InventoryWindow, 0, 2)
        self.add_nav_button(grid, "💳 نقطة البيع", "pos", POSWindow, 0, 3)
        self.add_nav_button(grid, "🧾 المشتريات", "purchases", PurchaseWindow, 1, 0)
        self.add_nav_button(grid, "🤝 الموردون", "suppliers", SuppliersWindow, 1, 1)
        self.add_nav_button(grid, "🧑‍💼 الموظفون", "employees", EmployeeWindow, 1, 2)
        self.add_nav_button(grid, "💼 الحسابات", "accounting", AccountingWindow, 1, 3)
        self.add_nav_button(grid, "📁 الفواتير السابقة", "invoices", PreviousInvoicesWindow, 2, 0)
        self.add_nav_button(grid, "🔄 المرتجعات", "returns", ReturnsWindow, 2, 1)
        self.add_nav_button(grid, "📊 التقارير", "reports", ReportsWindow, 2, 2)
        self.add_nav_button(grid, "⚙️ الإعدادات", "settings", SettingsWindow, 2, 3)
        main_layout.addLayout(grid)
        main_layout.addStretch()

        logout_btn = QPushButton("🔒 تسجيل الخروج")
        logout_btn.setObjectName("logout_btn")
        logout_btn.clicked.connect(self.logout)
        main_layout.addWidget(logout_btn, alignment=Qt.AlignLeft)

    # [تصحيح] دالة لتحديث الإحصائيات من قاعدة البيانات
    def update_stats(self):
        today_str = date.today().strftime("%Y-%m-%d")
        conn = self.connect_db()
        try:
            cur = conn.cursor()
            # 1. المبيعات اليومية
            cur.execute("SELECT SUM(total) FROM sales_invoices WHERE date(date) = ?", (today_str,))
            daily_sales = cur.fetchone()[0] or 0
            
            # 2. عدد فواتير اليوم
            cur.execute("SELECT COUNT(id) FROM sales_invoices WHERE date(date) = ?", (today_str,))
            daily_invoices = cur.fetchone()[0] or 0
            
            # تحديث الواجهة
            self.sales_label.findChild(QLabel, "stat_value").setText(f"{daily_sales:.2f}")
            self.invoices_label.findChild(QLabel, "stat_value").setText(str(daily_invoices))

        except sqlite3.Error as e:
            print(f"Error updating stats: {e}")
        finally:
            conn.close()

    def add_nav_button(self, layout, text, module_key, target_class, row, col):
        # [تصحيح] منطق التحقق من الصلاحيات
        if self.is_admin or module_key in self.allowed_modules:
            btn = QPushButton(text)
            btn.clicked.connect(lambda: self.open_module(target_class))
            layout.addWidget(btn, row, col)

    def create_stat_box(self, title):
        frame = QFrame()
        frame.setObjectName("stat_frame")
        layout = QVBoxLayout(frame)
        label_title = QLabel(title)
        label_title.setAlignment(Qt.AlignCenter)
        label_title.setProperty("class", "stat_title")
        label_value = QLabel("...") # قيمة مبدئية
        label_value.setObjectName("stat_value")
        label_value.setProperty("class", "stat_value")
        label_value.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_title)
        layout.addWidget(label_value)
        return frame

    def open_module(self, window_class):
        # [تصحيح] إدارة فعالة للنوافذ
        if window_class not in self.module_windows:
            # إنشاء النافذة فقط إذا لم تكن موجودة
            self.module_windows[window_class] = window_class()
            self.module_windows[window_class].closeEvent = lambda event, wc=window_class: self.on_module_close(event, wc)
        
        self.hide()
        self.module_windows[window_class].show()

    def on_module_close(self, event, window_class):
        # عند إغلاق نافذة الوحدة، أظهر لوحة التحكم مرة أخرى
        self.show()
        # قم بتحديث الإحصائيات لأن البيانات قد تكون تغيرت
        self.update_stats()
        event.accept()

    def logout(self):
        self.close()
        # إغلاق جميع نوافذ الوحدات المفتوحة
        for window in self.module_windows.values():
            window.close()
        if self.login_window:
            self.login_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # ملاحظة: قم بالتعليق على استيراد أي وحدة غير موجودة لتجنب خطأ
    window = DashboardWindow(user_info={"username": "admin", "permissions": "all"})
    window.show()
    sys.exit(app.exec())