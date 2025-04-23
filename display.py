import sys
import sqlite3
import requests
import webbrowser
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTableWidget, QTableWidgetItem, QLineEdit, QPushButton,
                            QLabel, QHeaderView, QSplitter, QScrollArea, QMessageBox)
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtCore import Qt, QTimer

class DatabaseViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("عارض الأطباء - تطبيق استخراج البيانات | By A.S & Abdallah")
        self.setGeometry(100, 100, 1200, 700)
        
        self.conn = sqlite3.connect("scraper_data.db")
        self.cursor = self.conn.cursor()
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        self.search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("البحث في جميع الحقول...")
        self.search_input.textChanged.connect(self.filter_data)
        
        self.clear_button = QPushButton("مسح")
        self.clear_button.clicked.connect(self.clear_search)
        
        self.export_button = QPushButton("تصدير البيانات إلى XLSX")
        self.export_button.clicked.connect(self.export_to_excel)
        
        self.search_layout.addWidget(self.search_input)
        self.search_layout.addWidget(self.clear_button)
        self.search_layout.addWidget(self.export_button)
        self.main_layout.addLayout(self.search_layout)
        
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)
        
        self.table_widget = QTableWidget()
        self.table_widget.setAlternatingRowColors(False)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_widget.itemSelectionChanged.connect(self.display_details)
        self.splitter.addWidget(self.table_widget)
        
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)
        
        self.image_label = QLabel("اختر صفًا لعرض الصورة")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedHeight(300)
        self.right_layout.addWidget(self.image_label)
        
        self.data_scroll = QScrollArea()
        self.data_widget = QWidget()
        self.data_layout = QVBoxLayout(self.data_widget)
        self.data_scroll.setWidget(self.data_widget)
        self.data_scroll.setWidgetResizable(True)
        self.right_layout.addWidget(self.data_scroll)
        
        self.splitter.addWidget(self.right_widget)
        self.splitter.setSizes([800, 400])
        
        self.load_data()
        
        # Apply the cyberpunk stylesheet from main.py
        self.setStyleSheet("""
            @keyframes pulse {
                0% { box-shadow: 0 0 8px #00FFFF, 0 0 16px #FF00FF; }
                50% { box-shadow: 0 0 16px #00FFFF, 0 0 24px #FF00FF; }
                100% { box-shadow: 0 0 8px #00FFFF, 0 0 16px #FF00FF; }
            }
            @keyframes glow {
                0% { border-color: #00FFFF; }
                50% { border-color: #FF00FF; }
                100% { border-color: #00FFFF; }
            }
            QMainWindow, QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a2e, stop:0.5 #2a2a4a, stop:1 #1a1a2e);
                color: #e0e7ff;
                font-family: 'Noto Sans Arabic', 'Orbitron', 'Arial', sans-serif;
                font-size: 14px;
                border-radius: 12px;
            }
            QTableWidget {
                background-color: rgba(255, 255, 255, 0.05);
                color: #e0e7ff;
                border: 2px solid rgba(0, 255, 255, 0.5);
                border-radius: 12px;
                padding: 8px;
                outline: none;
                animation: glow 3s infinite;
                gridline-color: rgba(0, 255, 255, 0.2);
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid rgba(0, 255, 255, 0.2);
                color: #e0e7ff;
            }
            QTableWidget::item:hover {
                background-color: rgba(0, 255, 255, 0.1);
                color: #00FFFF;
            }
            QTableWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00FFFF, stop:1 #FF00FF);
                color: #ffffff;
                border-radius: 8px;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a2e, stop:1 #2a2a4a);
                color: #e0e7ff;
                padding: 8px;
                border: 1px solid rgba(0, 255, 255, 0.5);
                font-size: 14px;
                font-weight: 600;
            }
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.05);
                color: #e0e7ff;
                border: 2px solid rgba(0, 255, 255, 0.4);
                border-radius: 12px;
                padding: 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #00FFFF;
                box-shadow: 0 0 16px rgba(0, 255, 255, 0.6);
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FF00FF, stop:1 #00FFFF);
                color: #ffffff;
                border: 2px solid #00FFFF;
                border-radius: 16px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: 600;
                letter-spacing: 1px;
                animation: pulse 2.5s infinite;
                transition: all 0.3s ease;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #00FFFF, stop:1 #FF00FF);
                border-color: #FF00FF;
                box-shadow: 0 0 20px rgba(0, 255, 255, 0.8);
                color: #ffffff;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a2e, stop:1 #2a2a4a);
                box-shadow: inset 0 0 12px #FF00FF;
                border-color: #FF00FF;
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.05);
                color: #6b7280;
                border: 2px dashed #4b5e8b;
                animation: none;
                box-shadow: none;
                opacity: 0.6;
            }
            QLabel {
                background-color: rgba(255, 255, 255, 0.05);
                color: #e0e7ff;
                border: 2px solid rgba(0, 255, 255, 0.4);
                border-radius: 12px;
                padding: 12px;
                font-size: 14px;
            }
            QScrollArea {
                background-color: rgba(255, 255, 255, 0.05);
                border: 2px solid rgba(0, 255, 255, 0.4);
                border-radius: 12px;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 12px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FF00FF, stop:1 #00FFFF);
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QMessageBox {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a2e, stop:0.5 #2a2a4a, stop:1 #1a1a2e);
                color: #e0e7ff;
                font-family: 'Noto Sans Arabic', 'Orbitron', 'Arial', sans-serif;
                font-size: 14px;
                border: 2px solid rgba(0, 255, 255, 0.5);
                border-radius: 12px;
            }
            QMessageBox QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FF00FF, stop:1 #00FFFF);
                color: #ffffff;
                border: 2px solid #00FFFF;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 600;
            }
            QMessageBox QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #00FFFF, stop:1 #FF00FF);
                border-color: #FF00FF;
                box-shadow: 0 0 16px rgba(0, 255, 255, 0.8);
            }
        """)

    def load_data(self):
        self.cursor.execute("SELECT * FROM doctors")
        self.all_data = self.cursor.fetchall()
        self.columns = [description[0] for description in self.cursor.description]
        
        self.table_widget.setRowCount(len(self.all_data))
        self.table_widget.setColumnCount(len(self.columns))
        self.table_widget.setHorizontalHeaderLabels(self.columns)
        
        for row_idx, row_data in enumerate(self.all_data):
            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data) if cell_data else "")
                item.setTextAlignment(Qt.AlignCenter)
                self.table_widget.setItem(row_idx, col_idx, item)
        
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def filter_data(self):
        search_text = self.search_input.text().lower()
        self.table_widget.setRowCount(0)
        
        filtered_data = [
            row for row in self.all_data
            if any(search_text in str(cell).lower() for cell in row)
        ]
        
        self.table_widget.setRowCount(len(filtered_data))
        for row_idx, row_data in enumerate(filtered_data):
            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data) if cell_data else "")
                item.setTextAlignment(Qt.AlignCenter)
                self.table_widget.setItem(row_idx, col_idx, item)

    def clear_search(self):
        self.search_input.clear()
        self.load_data()

    def export_to_excel(self):
        try:
            df = pd.read_sql_query("SELECT * FROM doctors", self.conn)
            output_file = "doctors_data.xlsx"
            df.to_excel(output_file, index=False, engine='openpyxl')
            self.show_notification(f"تم تصدير البيانات بنجاح إلى {output_file}!")
        except Exception as e:
            self.show_notification(f"خطأ في تصدير البيانات: {str(e)}")

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
            elif item.layout():
                self.clear_layout(item.layout())

    def display_details(self):
        self.clear_layout(self.data_layout)
        
        selected_items = self.table_widget.selectedItems()
        if not selected_items:
            self.image_label.setText("اختر صفًا لعرض الصورة")
            self.image_label.setPixmap(QPixmap())
            self.data_layout.addWidget(QLabel("اختر صفًا لعرض التفاصيل"))
            return
        
        row = selected_items[0].row()
        row_data = [self.table_widget.item(row, col).text() for col in range(self.table_widget.columnCount())]
        data_dict = dict(zip(self.columns, row_data))
        
        image_url_col = self.columns.index("image_url") if "image_url" in self.columns else -1
        default_image_url = "https://c8.alamy.com/comp/2FJR92X/flat-male-doctor-avatar-in-medical-face-protection-mask-and-stethoscope-healthcare-vector-illustration-people-cartoon-avatar-profile-character-icon-2FJR92X.jpg"
        
        if image_url_col != -1:
            image_url = row_data[image_url_col]
            if image_url and image_url.startswith("http"):
                try:
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
                    response = requests.get(image_url, headers=headers, timeout=10)
                    response.raise_for_status()
                    pixmap = QPixmap()
                    pixmap.loadFromData(response.content)
                    if pixmap.isNull():
                        response = requests.get(default_image_url, headers=headers, timeout=10)
                        response.raise_for_status()
                        pixmap.loadFromData(response.content)
                    scaled_pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.image_label.setPixmap(scaled_pixmap)
                except requests.exceptions.RequestException as e:
                    try:
                        response = requests.get(default_image_url, headers=headers, timeout=10)
                        response.raise_for_status()
                        pixmap = QPixmap()
                        pixmap.loadFromData(response.content)
                        scaled_pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.image_label.setPixmap(scaled_pixmap)
                    except:
                        self.image_label.setText("فشل في تحميل الصورة الافتراضية")
                        self.image_label.setPixmap(QPixmap())
            else:
                try:
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
                    response = requests.get(default_image_url, headers=headers, timeout=10)
                    response.raise_for_status()
                    pixmap = QPixmap()
                    pixmap.loadFromData(response.content)
                    scaled_pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.image_label.setPixmap(scaled_pixmap)
                except:
                    self.image_label.setText("فشل في تحميل الصورة الافتراضية")
                    self.image_label.setPixmap(QPixmap())
        else:
            self.image_label.setText("لم يتم العثور على عمود رابط الصورة")
        
        fields_to_display = ["name", "specialty", "location", "profile_url", "source"]
        for field in fields_to_display:
            value = data_dict.get(field, "غير متاح")
            field_layout = QHBoxLayout()
            
            label = QLabel(f"{field.upper()}: {value}")
            label.setWordWrap(True)
            field_layout.addWidget(label)
            
            if field in ["name", "specialty", "location"]:
                copy_button = QPushButton("نسخ")
                copy_button.clicked.connect(lambda _, v=value: self.copy_to_clipboard(v))
                field_layout.addWidget(copy_button)
            
            if field in ["profile_url", "source"] and value.startswith("http"):
                go_button = QPushButton("فتح")
                go_button.clicked.connect(lambda _, url=value: webbrowser.open(url))
                field_layout.addWidget(go_button)
            
            self.data_layout.addLayout(field_layout)
        
        copy_all_button = QPushButton(f"نسخ بيانات {data_dict.get('name', 'الطبيب')}")
        copy_all_button.clicked.connect(lambda: self.copy_all_data(row_data))
        self.data_layout.addWidget(copy_all_button, alignment=Qt.AlignCenter)
        
        self.data_widget.adjustSize()

    def copy_to_clipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.show_notification(f"تم النسخ: {text[:20]}..." if len(text) > 20 else f"تم النسخ: {text}")

    def copy_all_data(self, row_data):
        data_text = "\n".join([f"{col}: {val}" for col, val in zip(self.columns, row_data)])
        clipboard = QApplication.clipboard()
        clipboard.setText(data_text)
        self.show_notification("تم نسخ جميع البيانات!")

    def show_notification(self, message):
        msg = QMessageBox(self)
        msg.setWindowTitle("إشعار")
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Ok)
        QTimer.singleShot(4000, msg.accept)
        msg.exec_()

    def closeEvent(self, event):
        self.conn.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont("Noto Sans Arabic", 10))
    window = DatabaseViewer()
    window.show()
    sys.exit(app.exec_())