import sys
import os
import shutil
import sqlite3
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QFileDialog, QFormLayout
)
from PySide6.QtCore import Qt

DB_NAME = "supermarket.db"
BACKUP_DEFAULT_FOLDER = "backups"

# --- Helper functions to interact with settings table ---
def get_setting(key, default=''):
    """Fetches a setting value from the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else default

def save_setting(key, value):
    """Saves a setting value to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # INSERT OR REPLACE is perfect for settings
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()
# --- End of helper functions ---

class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        # تم تحديث العنوان ليعكس المحتوى الجديد
        self.setWindowTitle("🗃️ إدارة البيانات والنسخ الاحتياطي")
        self.setGeometry(300, 200, 600, 300)

        self.setStyleSheet("""
            QWidget { background-color: #11111f; color: #dddddd; font-family: 'Segoe UI'; }
            QLabel { font-size: 14px; font-weight: bold; }
            QLineEdit { 
                background-color: #1e1e2f; border: 1px solid #444466; 
                border-radius: 6px; padding: 6px; font-size: 14px; color: #eee;
            }
            QPushButton { 
                border-radius: 6px; padding: 10px 20px; font-size: 14px; font-weight: bold;
                margin-top: 10px;
            }
            QPushButton#backup_btn { background-color: #3a86ff; color: white; }
            QPushButton#backup_btn:hover { background-color: #5599ff; }
            QPushButton#restore_btn { background-color: #f39c12; color: white; }
            QPushButton#restore_btn:hover { background-color: #f1c40f; }
            QPushButton#reset_btn { background-color: #d32f2f; color: white; }
            QPushButton#reset_btn:hover { background-color: #e57373; }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignCenter)

        # --- تم دمج واجهة النسخ الاحتياطي مباشرة هنا ---

        # Backup Section
        backup_layout = QHBoxLayout()
        backup_label = QLabel("مسار النسخ الاحتياطي:")
        self.backup_folder_input = QLineEdit()
        self.backup_folder_input.setPlaceholderText(BACKUP_DEFAULT_FOLDER)
        # تحميل مسار النسخ الاحتياطي عند بدء التشغيل
        self.backup_folder_input.setText(get_setting('backup_folder', BACKUP_DEFAULT_FOLDER))

        backup_layout.addWidget(backup_label)
        backup_layout.addWidget(self.backup_folder_input)
        
        main_layout.addLayout(backup_layout)
        
        backup_btn = QPushButton("إنشاء نسخة احتياطية الآن")
        backup_btn.setObjectName("backup_btn")
        backup_btn.clicked.connect(self.create_backup)
        main_layout.addWidget(backup_btn, alignment=Qt.AlignCenter)

        # Restore Section
        restore_btn = QPushButton("📁 استعادة نسخة احتياطية")
        restore_btn.setObjectName("restore_btn")
        restore_btn.clicked.connect(self.restore_backup)
        main_layout.addWidget(restore_btn, alignment=Qt.AlignCenter)

        # Reset Section
        reset_btn = QPushButton("🔥 إعادة تعيين بيانات البرنامج")
        reset_btn.setObjectName("reset_btn")
        reset_btn.clicked.connect(self.reset_data)
        main_layout.addWidget(reset_btn, alignment=Qt.AlignCenter)

    def create_backup(self):
        # حفظ المسار المدخل في الإعدادات قبل استخدامه
        folder_path = self.backup_folder_input.text().strip()
        save_setting('backup_folder', folder_path)

        folder = folder_path or BACKUP_DEFAULT_FOLDER
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
            except Exception as e:
                QMessageBox.warning(self, "خطأ", f"تعذر إنشاء المجلد:\n{str(e)}")
                return

        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_path = os.path.join(folder, f"supermarket_backup_{now}.db")

        try:
            shutil.copyfile(DB_NAME, backup_path)
            QMessageBox.information(self, "نجاح", f"تم إنشاء النسخة الاحتياطية بنجاح:\n{backup_path}")
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل النسخ الاحتياطي:\n{str(e)}")

    def restore_backup(self):
        msg = "هل أنت متأكد من رغبتك في استعادة نسخة احتياطية؟\n" \
              "سيتم استبدال جميع البيانات الحالية بالبيانات الموجودة في النسخة الاحتياطية.\n" \
              "هذه العملية لا يمكن التراجع عنها!"
        reply = QMessageBox.warning(self, "تحذير خطير", msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            file_path, _ = QFileDialog.getOpenFileName(self, "اختر ملف النسخة الاحتياطية", "", "ملفات قاعدة البيانات (*.db)")
            if file_path:
                try:
                    # For a safe restore, the application should close and let an external script do the copy.
                    # A simpler, but riskier way for a desktop app is to copy it and ask user to restart.
                    # We will show a message that app needs to restart.
                    shutil.copyfile(file_path, DB_NAME)
                    QMessageBox.information(self, "نجاح", 
                        "تم استعادة النسخة الاحتياطية بنجاح.\n" \
                        "يجب إعادة تشغيل البرنامج الآن لتطبيق التغييرات.")
                    QApplication.quit() # Close the application
                except Exception as e:
                    QMessageBox.critical(self, "فشل", f"فشلت عملية الاستعادة:\n{e}")
    
    def reset_data(self):
        msg1 = "هل أنت متأكد تماماً من رغبتك في إعادة تعيين كافة البيانات؟"
        msg2 = "سيتم حذف جميع الفواتير والمنتجات والمشتريات نهائياً. لا يمكن التراجع عن هذا الإجراء."
        reply1 = QMessageBox.critical(self, "تحذير نهائي", f"{msg1}\n{msg2}", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply1 == QMessageBox.Yes:
            reply2 = QMessageBox.critical(self, "تأكيد أخير", "للتأكيد، اضغط 'Yes' مرة أخرى للمتابعة.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply2 == QMessageBox.Yes:
                tables_to_clear = [
                    "sales_items", "sales_invoices",
                    "purchase_items", "purchase_invoices",
                    "products", "stock_movements", "login_logs"
                ]
                try:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    for table in tables_to_clear:
                        cursor.execute(f"DELETE FROM {table};")
                        # Reset autoincrement counter
                        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}';")
                    conn.commit()
                    conn.close()
                    QMessageBox.information(self, "نجاح", "تم إعادة تعيين بيانات البرنامج بنجاح. يفضل إعادة تشغيل البرنامج.")
                except Exception as e:
                    QMessageBox.critical(self, "فشل", f"فشلت عملية إعادة التعيين:\n{e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SettingsWindow()
    window.show()
    sys.exit(app.exec())