import sys
import sqlite3
import pandas as pd
import os
from datetime import datetime

# --- استيراد مكتبات الواجهة والرسومات ---
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QTextEdit, QDateEdit,
    QFileDialog, QMessageBox, QFrame, QSizePolicy
)
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QFont

# --- استيراد مكونات Matplotlib للرسم البياني ---
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

DB_NAME = "supermarket.db"
REPORTS_FOLDER = "generated_reports"
os.makedirs(REPORTS_FOLDER, exist_ok=True)


# فئة مخصصة لعرض الرسوم البيانية داخل الواجهة (تبقى كما هي)
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        try:
            # محاولة استخدام خط شائع. إذا فشل، سيستخدم الافتراضي
            matplotlib.rcParams['font.family'] = 'Arial'
        except:
            print("لم يتم العثور على خط Arial، قد لا تظهر الحروف العربية بشكل صحيح في الرسم البياني.")
            
        fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#1e1e2f')
        self.axes = fig.add_subplot(111)
        self.axes.tick_params(axis='x', colors='white')
        self.axes.tick_params(axis='y', colors='white')
        self.axes.xaxis.label.set_color('white')
        self.axes.yaxis.label.set_color('white')
        self.axes.title.set_color('white')
        fig.tight_layout(pad=3.0)
        super(MplCanvas, self).__init__(fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


class ReportsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📊 وحدة التقارير والتحليل")
        self.resize(1100, 700)
        self.current_df = None
        self.current_report_title = ""

        self.setStyleSheet("""
            QWidget { background-color: #12121c; color: #eee; font-family: 'Segoe UI'; }
            QFrame#controls_frame { background-color: #1e1e2f; border-radius: 8px; }
            QPushButton {
                background-color: #3a86ff; color: white; padding: 8px 15px;
                border-radius: 6px; font-weight: bold; border: none; font-size: 13px;
            }
            QPushButton:hover { background-color: #5599ff; }
            QPushButton#export_excel_btn { background-color: #1D6F42; }
            QPushButton#export_excel_btn:hover { background-color: #27ae60; }
            
            QComboBox, QDateEdit {
                background-color: #12121c; color: white; padding: 6px 10px;
                border: 1px solid #444466; border-radius: 6px; font-size: 14px;
            }
            QTextEdit {
                background-color: #1e1e2f; color: #eee; border-radius: 6px;
                font-family: 'Consolas', 'Courier New', monospace; font-size: 13px;
            }
            QLabel { font-weight: bold; font-size: 14px; }
        """)

        # --- التصميم الرئيسي ---
        main_layout = QVBoxLayout(self)
        
        # --- قسم التحكم ---
        controls_frame = QFrame()
        controls_frame.setObjectName("controls_frame")
        controls_layout = QHBoxLayout(controls_frame)
        
        self.report_type = QComboBox()
        self.report_type.addItems([
            "ملخص المبيعات اليومي", "المنتجات الأكثر مبيعاً", "ملخص المشتريات اليومي",
            "تقرير الرواتب المدفوعة", "أرصدة الموردين", "أرصدة العملاء"
        ])
        self.report_type.currentIndexChanged.connect(self.toggle_date_fields)

        self.start_date = QDateEdit(QDate.currentDate().addMonths(-1))
        self.end_date = QDateEdit(QDate.currentDate())
        for date_edit in [self.start_date, self.end_date]:
            date_edit.setCalendarPopup(True)

        self.generate_btn = QPushButton("📊 توليد التقرير")
        self.generate_btn.clicked.connect(self.generate_report)
        
        controls_layout.addWidget(QLabel("التقرير:"))
        controls_layout.addWidget(self.report_type, 1)
        self.start_date_label = QLabel("من:")
        self.end_date_label = QLabel("إلى:")
        controls_layout.addWidget(self.start_date_label)
        controls_layout.addWidget(self.start_date)
        controls_layout.addWidget(self.end_date_label)
        controls_layout.addWidget(self.end_date)
        controls_layout.addStretch()
        controls_layout.addWidget(self.generate_btn)
        
        main_layout.addWidget(controls_frame)
        
        # --- قسم العرض (نص ورسم بياني) ---
        display_layout = QHBoxLayout()
        self.report_output = QTextEdit()
        self.report_output.setReadOnly(True)
        display_layout.addWidget(self.report_output, 1)

        self.chart_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        display_layout.addWidget(self.chart_canvas, 1)
        main_layout.addLayout(display_layout, 1)

        # --- قسم التصدير ---
        export_layout = QHBoxLayout()
        self.export_excel_btn = QPushButton("📄 تصدير إلى Excel")
        self.export_excel_btn.setObjectName("export_excel_btn")
        self.export_excel_btn.clicked.connect(self.export_to_excel)
        
        export_layout.addStretch()
        export_layout.addWidget(self.export_excel_btn)
        self.export_excel_btn.setEnabled(False) # تعطيل الزر حتى يتم توليد تقرير

        main_layout.addLayout(export_layout)
        self.toggle_date_fields()

    def connect_db(self):
        return sqlite3.connect(DB_NAME)

    def toggle_date_fields(self):
        report_name = self.report_type.currentText()
        show_dates = report_name not in ["أرصدة الموردين", "أرصدة العملاء"]
        for widget in [self.start_date, self.start_date_label, self.end_date, self.end_date_label]:
            widget.setVisible(show_dates)

    def generate_report(self):
        report_name = self.report_type.currentText()
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd 23:59:59")
        self.current_report_title = f"{report_name} من {start_date} إلى {end_date[:10]}"
        
        conn = self.connect_db()
        try:
            if report_name == "ملخص المبيعات اليومي":
                query = "SELECT date(date) as 'اليوم', SUM(total) as 'إجمالي_المبيعات' FROM sales_invoices WHERE date BETWEEN ? AND ? GROUP BY اليوم ORDER BY اليوم"
                self.current_df = pd.read_sql_query(query, conn, params=(start_date, end_date))
                
            elif report_name == "المنتجات الأكثر مبيعاً":
                query = """
                    SELECT p.name as 'المنتج', SUM(si.quantity) as 'الكمية_المباعة'
                    FROM sales_items si
                    JOIN products p ON p.id = si.product_id
                    JOIN sales_invoices inv ON inv.id = si.invoice_id
                    WHERE inv.date BETWEEN ? AND ?
                    GROUP BY p.name ORDER BY الكمية_المباعة DESC LIMIT 10
                """
                self.current_df = pd.read_sql_query(query, conn, params=(start_date, end_date))

            elif report_name == "ملخص المشتريات اليومي":
                query = "SELECT date(date) as 'اليوم', SUM(total) as 'إجمالي_المشتريات' FROM purchase_invoices WHERE date BETWEEN ? AND ? GROUP BY اليوم ORDER BY اليوم"
                self.current_df = pd.read_sql_query(query, conn, params=(start_date, end_date))
            
            elif report_name == "تقرير الرواتب المدفوعة":
                query = """
                    SELECT e.name as 'الموظف', s.month as 'الشهر', s.total_salary as 'الراتب'
                    FROM salaries s
                    JOIN employees e ON s.employee_id = e.id
                    WHERE s.payment_date BETWEEN ? AND ?
                    ORDER BY s.payment_date
                """
                self.current_df = pd.read_sql_query(query, conn, params=(start_date, end_date))

            elif report_name == "أرصدة الموردين":
                query = "SELECT name as 'المورد', phone as 'الهاتف', balance as 'الرصيد' FROM suppliers WHERE balance != 0 ORDER BY balance DESC"
                self.current_df = pd.read_sql_query(query, conn)
                self.current_report_title = "تقرير أرصدة الموردين"

            elif report_name == "أرصدة العملاء":
                query = "SELECT name as 'العميل', phone as 'الهاتف', balance as 'الرصيد' FROM customers WHERE balance != 0 ORDER BY balance DESC"
                self.current_df = pd.read_sql_query(query, conn)
                self.current_report_title = "تقرير أرصدة العملاء"

            else:
                self.current_df = pd.DataFrame()

        except Exception as e:
            QMessageBox.critical(self, "خطأ في الاستعلام", f"لا يمكن جلب البيانات.\nتأكد من أن أسماء الجداول والأعمدة في قاعدة البيانات صحيحة.\n\nالخطأ: {e}")
            self.current_df = None
            return
        finally:
            conn.close()

        if self.current_df is None or self.current_df.empty:
            self.report_output.setText("لا توجد بيانات لعرضها في الفترة المحددة.")
            self.chart_canvas.axes.clear()
            self.chart_canvas.draw()
            self.export_excel_btn.setEnabled(False)
            return
        
        self.report_output.setText(self.current_df.to_string())
        self.display_chart(report_name)
        self.export_excel_btn.setEnabled(True)

    def display_chart(self, report_name):
        self.chart_canvas.axes.clear()
        ax = self.chart_canvas.axes
        df = self.current_df
        
        try:
            if report_name == "ملخص المبيعات اليومي":
                df.plot(kind='bar', x=df.columns[0], y=df.columns[1], ax=ax, legend=False, color='#3a86ff')
                ax.set_title("إجمالي المبيعات اليومية", color='white')
            elif report_name == "المنتجات الأكثر مبيعاً":
                df.sort_values(df.columns[1]).plot(kind='barh', x=df.columns[0], y=df.columns[1], ax=ax, legend=False, color='#00b894')
                ax.set_title("أكثر 10 منتجات مبيعاً", color='white')
            elif report_name == "ملخص المشتريات اليومي":
                df.plot(kind='line', x=df.columns[0], y=df.columns[1], ax=ax, legend=False, color='#e74c3c', marker='o')
                ax.set_title("إجمالي المشتريات اليومية", color='white')
            elif report_name in ["أرصدة الموردين", "أرصدة العملاء", "تقرير الرواتب المدفوعة"]:
                 df.plot(kind='barh', x=df.columns[0], y=df.columns[2], ax=ax, legend=False, color='#f39c12')
                 ax.set_title(report_name, color='white')
            else:
                 self.chart_canvas.axes.clear()
        
            ax.set_xlabel(df.columns[0], color='white')
            ax.set_ylabel(df.columns[1], color='white')
            ax.set_xticklabels(ax.get_xticklabels(), rotation=25, ha="right")
            ax.grid(axis='y', linestyle='--', alpha=0.6)
            self.chart_canvas.figure.tight_layout()
            self.chart_canvas.draw()
        except Exception as e:
            print(f"خطأ في رسم المخطط: {e}")

    def export_to_excel(self):
        if self.current_df is None: return
        
        default_filename = os.path.join(REPORTS_FOLDER, f"{self.current_report_title.replace(' ', '_').replace(':', '')}.xlsx")
        filename, _ = QFileDialog.getSaveFileName(self, "حفظ كـ Excel", default_filename, "Excel Files (*.xlsx)")
        
        if filename:
            try:
                self.current_df.to_excel(filename, index=False, engine='openpyxl')
                QMessageBox.information(self, "نجاح", f"تم حفظ التقرير بنجاح في:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل حفظ الملف: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ReportsWindow()
    window.show()
    sys.exit(app.exec())