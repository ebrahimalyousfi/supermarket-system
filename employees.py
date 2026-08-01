import sys
import sqlite3
import calendar
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QDateEdit,
    QHeaderView, QTabWidget, QFormLayout, QComboBox
)
from PySide6.QtCore import Qt, QDate

DB_NAME = "supermarket.db"

class EmployeeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧑‍💼 إدارة الموظفين والرواتب")
        self.setGeometry(200, 100, 1100, 700)
        self.selected_employee_id = None

        self.setStyleSheet("""
            QWidget { background-color: #12121c; color: #ddd; font-family: 'Segoe UI'; font-size: 13px; }
            QTabWidget::pane { border-top: 2px solid #3a3a6f; background-color: #1e1e2f; }
            QTabBar::tab { background: #12121c; color: #aaa; padding: 10px 20px; border: 1px solid #3a3a6f; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: #3a86ff; color: white; font-weight: bold; }
            QLabel { font-weight: bold; }
            QLineEdit, QDateEdit, QComboBox { background-color: #2d2d44; color: #fff; padding: 8px; border-radius: 6px; border: 1px solid #444; }
            QPushButton { border-radius: 6px; padding: 8px 15px; font-weight: bold; border: none; }
            QPushButton:disabled { background-color: #555; }
            QPushButton#add_btn { background-color: #00b894; color: white; }
            QPushButton#update_btn { background-color: #f39c12; color: white; }
            QPushButton#delete_btn { background-color: #d32f2f; color: white; }
            QPushButton#pay_btn { background-color: #2ecc71; color: white; }
            QPushButton#clear_btn { background-color: #636e72; color: white; }
            QTableWidget { background-color: #1e1e2f; color: white; gridline-color: #3a3a6f; border-radius: 6px; }
            QHeaderView::section { background-color: #2a2a4a; color: #aaccff; font-weight: bold; border: 1px solid #3a3a6f; padding: 5px; }
        """)

        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        
        self.create_employees_tab()
        self.create_attendance_tab()
        self.create_salaries_tab()
        
        main_layout.addWidget(self.tabs)
        self.tabs.currentChanged.connect(self.on_tab_change)

        self.load_employees_tab_data()

    def connect_db(self):
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn
        
    def on_tab_change(self, index):
        tab_text = self.tabs.tabText(index)
        if tab_text == "إدارة الموظفين":
            self.load_employees_tab_data()
        elif tab_text == "الحضور والانصراف":
            self.load_attendance_tab_data()
        elif tab_text == "الرواتب":
            self.load_salaries_tab_data()

    # --- تبويب إدارة الموظفين ---
    def create_employees_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)

        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setSpacing(10)

        self.name_input = QLineEdit(placeholderText="اسم الموظف الكامل")
        self.department_input = QLineEdit(placeholderText="مثال: كاشير, مبيعات")
        self.salary_input = QLineEdit(placeholderText="الراتب الشهري الأساسي")
        self.join_date_input = QDateEdit(QDate.currentDate(), calendarPopup=True)
        
        form_layout.addRow("الاسم:", self.name_input)
        form_layout.addRow("القسم:", self.department_input)
        form_layout.addRow("الراتب:", self.salary_input)
        form_layout.addRow("تاريخ التعيين:", self.join_date_input)

        buttons_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ إضافة"); self.add_btn.setObjectName("add_btn")
        self.update_btn = QPushButton("💾 تعديل"); self.update_btn.setObjectName("update_btn")
        self.delete_btn = QPushButton("🗑️ حذف"); self.delete_btn.setObjectName("delete_btn")
        
        self.add_btn.clicked.connect(self.add_employee)
        self.update_btn.clicked.connect(self.update_employee)
        self.delete_btn.clicked.connect(self.delete_employee)
        
        buttons_layout.addWidget(self.add_btn)
        buttons_layout.addWidget(self.update_btn)
        buttons_layout.addWidget(self.delete_btn)
        form_layout.addRow(buttons_layout)
        
        clear_btn = QPushButton("🔄 مسح الحقول"); clear_btn.setObjectName("clear_btn")
        clear_btn.clicked.connect(self.clear_inputs)
        form_layout.addWidget(clear_btn)

        self.employees_table = QTableWidget()
        self.employees_table.setColumnCount(5)
        self.employees_table.setHorizontalHeaderLabels(["ID", "الاسم", "القسم", "الراتب", "تاريخ التعيين"])
        self.employees_table.setColumnHidden(0, True)
        self.employees_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.employees_table.cellClicked.connect(self.select_employee)

        layout.addWidget(self.employees_table, 2)
        layout.addWidget(form_widget, 1)
        self.tabs.addTab(tab, "إدارة الموظفين")

    def load_employees_tab_data(self):
        self.employees_table.setRowCount(0)
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, department, salary, join_date FROM employees")
        for row in cursor.fetchall():
            row_idx = self.employees_table.rowCount()
            self.employees_table.insertRow(row_idx)
            self.employees_table.setItem(row_idx, 0, QTableWidgetItem(str(row['id'])))
            self.employees_table.setItem(row_idx, 1, QTableWidgetItem(row['name']))
            self.employees_table.setItem(row_idx, 2, QTableWidgetItem(row['department']))
            self.employees_table.setItem(row_idx, 3, QTableWidgetItem(str(row['salary'])))
            self.employees_table.setItem(row_idx, 4, QTableWidgetItem(row['join_date']))
        conn.close()
        self.clear_inputs()

    def select_employee(self, row, col):
        self.selected_employee_id = int(self.employees_table.item(row, 0).text())
        self.name_input.setText(self.employees_table.item(row, 1).text())
        self.department_input.setText(self.employees_table.item(row, 2).text())
        self.salary_input.setText(self.employees_table.item(row, 3).text())
        self.join_date_input.setDate(QDate.fromString(self.employees_table.item(row, 4).text(), "yyyy-MM-dd"))
        self.update_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

    def clear_inputs(self):
        self.selected_employee_id = None
        self.name_input.clear()
        self.department_input.clear()
        self.salary_input.clear()
        self.join_date_input.setDate(QDate.currentDate())
        self.employees_table.clearSelection()
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

    def add_employee(self):
        name = self.name_input.text().strip()
        department = self.department_input.text().strip()
        try:
            salary = float(self.salary_input.text())
        except ValueError:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال راتب صحيح.")
            return

        if not name or salary <= 0:
            QMessageBox.warning(self, "خطأ", "يرجى ملء اسم الموظف وإدخال راتب صحيح.")
            return
        
        join_date = self.join_date_input.date().toString("yyyy-MM-dd")
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO employees (name, department, salary, join_date) VALUES (?, ?, ?, ?)", (name, department, salary, join_date))
        conn.commit()
        conn.close()
        self.load_employees_tab_data()

    def update_employee(self):
        if not self.selected_employee_id:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار موظف لتعديله.")
            return
        
        name = self.name_input.text().strip()
        department = self.department_input.text().strip()
        try:
            salary = float(self.salary_input.text())
        except ValueError:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال راتب صحيح.")
            return

        join_date = self.join_date_input.date().toString("yyyy-MM-dd")
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE employees SET name=?, department=?, salary=?, join_date=? WHERE id=?", (name, department, salary, join_date, self.selected_employee_id))
        conn.commit()
        conn.close()
        self.load_employees_tab_data()
        
    def delete_employee(self):
        if not self.selected_employee_id:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار موظف لحذفه.")
            return
        
        reply = QMessageBox.question(self, "تأكيد الحذف", "هل أنت متأكد من حذف هذا الموظف؟ سيتم حذف سجلات حضوره ورواتبه أيضاً.", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = self.connect_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM salaries WHERE employee_id = ?", (self.selected_employee_id,))
            cursor.execute("DELETE FROM attendance WHERE employee_id = ?", (self.selected_employee_id,))
            cursor.execute("DELETE FROM employees WHERE id = ?", (self.selected_employee_id,))
            conn.commit()
            conn.close()
            self.load_employees_tab_data()

    # --- تبويب الحضور ---
    def create_attendance_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.attendance_table = QTableWidget()
        self.attendance_table.setColumnCount(4)
        self.attendance_table.setHorizontalHeaderLabels(["ID", "اسم الموظف", "حالة حضور اليوم", ""])
        self.attendance_table.setColumnHidden(0, True)
        self.attendance_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.attendance_table)
        self.tabs.addTab(tab, "الحضور والانصراف")

    def load_attendance_tab_data(self):
        self.attendance_table.setRowCount(0)
        today_str = datetime.now().strftime("%Y-%m-%d")
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM employees ORDER BY name")
        employees = cursor.fetchall()
        
        for emp in employees:
            row_idx = self.attendance_table.rowCount()
            self.attendance_table.insertRow(row_idx)
            self.attendance_table.setItem(row_idx, 0, QTableWidgetItem(str(emp['id'])))
            self.attendance_table.setItem(row_idx, 1, QTableWidgetItem(emp['name']))

            cursor.execute("SELECT status FROM attendance WHERE employee_id = ? AND date = ?", (emp['id'], today_str))
            attendance_record = cursor.fetchone()
            
            status_item = QTableWidgetItem("❌ غائب")
            status_item.setForeground(Qt.red)
            
            attend_btn = QPushButton("✅ تسجيل حضور")
            attend_btn.clicked.connect(lambda _, eid=emp['id']: self.mark_attendance(eid))
            
            if attendance_record:
                status_item.setText("✔️ حاضر")
                status_item.setForeground(Qt.green)
                attend_btn.setText("تم التسجيل")
                attend_btn.setEnabled(False)
            
            self.attendance_table.setItem(row_idx, 2, status_item)
            self.attendance_table.setCellWidget(row_idx, 3, attend_btn)
        
        conn.close()

    def mark_attendance(self, employee_id):
        today_str = datetime.now().strftime("%Y-%m-%d")
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO attendance (employee_id, date, status) VALUES (?, ?, ?)", (employee_id, today_str, "حاضر"))
        conn.commit()
        conn.close()
        self.load_attendance_tab_data()
    
    # --- تبويب الرواتب ---
    def create_salaries_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        pay_layout = QHBoxLayout()
        self.employee_salary_combo = QComboBox()
        self.month_date_edit = QDateEdit(QDate.currentDate(), calendarPopup=True)
        self.month_date_edit.setDisplayFormat("MMMM yyyy")
        self.pay_btn = QPushButton("💰 صرف راتب الشهر المحدد"); self.pay_btn.setObjectName("pay_btn")
        self.pay_btn.clicked.connect(self.pay_salary)
        
        pay_layout.addWidget(QLabel("صرف راتب للموظف:"))
        pay_layout.addWidget(self.employee_salary_combo, 1)
        pay_layout.addWidget(QLabel("عن شهر:"))
        pay_layout.addWidget(self.month_date_edit)
        pay_layout.addWidget(self.pay_btn)
        layout.addLayout(pay_layout)
        
        self.salaries_table = QTableWidget()
        self.salaries_table.setColumnCount(5)
        self.salaries_table.setHorizontalHeaderLabels(["اسم الموظف", "الشهر المرجعي", "أيام العمل", "الراتب المصروف", "تاريخ الصرف"])
        self.salaries_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.salaries_table)
        self.tabs.addTab(tab, "الرواتب")

    def load_salaries_tab_data(self):
        self.employee_salary_combo.clear()
        conn = self.connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM employees ORDER BY name")
        for emp in cursor.fetchall():
            self.employee_salary_combo.addItem(emp['name'], emp['id'])
        
        self.salaries_table.setRowCount(0)
        cursor.execute("""
            SELECT e.name, s.month, s.days_present, s.total_salary, s.payment_date
            FROM salaries s JOIN employees e ON s.employee_id = e.id ORDER BY s.payment_date DESC
        """)
        for row in cursor.fetchall():
            row_idx = self.salaries_table.rowCount()
            self.salaries_table.insertRow(row_idx)
            self.salaries_table.setItem(row_idx, 0, QTableWidgetItem(row['name']))
            self.salaries_table.setItem(row_idx, 1, QTableWidgetItem(row['month']))
            self.salaries_table.setItem(row_idx, 2, QTableWidgetItem(str(row['days_present'])))
            self.salaries_table.setItem(row_idx, 3, QTableWidgetItem(f"{row['total_salary']:.2f}"))
            self.salaries_table.setItem(row_idx, 4, QTableWidgetItem(row['payment_date']))
        conn.close()

    def pay_salary(self):
        employee_id = self.employee_salary_combo.currentData()
        if not employee_id:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار موظف.")
            return

        target_date = self.month_date_edit.date().toPython()
        month_str = target_date.strftime("%Y-%m")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1 FROM salaries WHERE employee_id = ? AND month = ?", (employee_id, month_str))
            if cursor.fetchone():
                QMessageBox.warning(self, "مكرر", f"راتب شهر {month_str} لهذا الموظف تم صرفه مسبقاً.")
                return
                
            year, month = target_date.year, target_date.month
            _, num_days_in_month = calendar.monthrange(year, month)
            
            cursor.execute("SELECT salary FROM employees WHERE id = ?", (employee_id,))
            base_salary_row = cursor.fetchone()
            if not base_salary_row: return # Employee not found
            base_salary = base_salary_row['salary']
            
            cursor.execute("SELECT COUNT(*) FROM attendance WHERE employee_id = ? AND strftime('%Y-%m', date) = ? AND status = 'حاضر'", (employee_id, month_str))
            days_present = cursor.fetchone()[0]

            final_salary = round((base_salary / num_days_in_month) * days_present, 2)
            payment_date = datetime.now().strftime("%Y-%m-%d")
            
            cursor.execute("INSERT INTO salaries (employee_id, month, days_present, total_salary, payment_date) VALUES (?, ?, ?, ?, ?)",
                           (employee_id, month_str, days_present, final_salary, payment_date))
            cursor.execute("UPDATE employees SET last_payment = ? WHERE id = ?", (payment_date, employee_id))
            conn.commit()
            QMessageBox.information(self, "نجاح", f"تم صرف راتب بقيمة {final_salary} للموظف المحدد.")
            self.load_salaries_tab_data()
        except sqlite3.Error as e:
            conn.rollback()
            QMessageBox.critical(self, "خطأ", f"فشل صرف الراتب: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EmployeeWindow()
    window.show()
    sys.exit(app.exec())