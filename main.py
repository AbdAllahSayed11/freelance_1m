import os
import sys
import sqlite3
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QListWidget, QPushButton, QTextEdit, 
                            QListWidgetItem, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from scraper.database import Database
from scraper.scrapers import wellness,uaeu,skmc,sharjahcmc,altaie,tawam,dhafrah,
royalclinic,mezyadmc,livhospital,hsmc,gargashhospital

SCRAPERS = {
    "wellnesssurgerycenter.com": wellness.scrape,
    "uaeu.ac.ae": uaeu.scrape,
    "skmca.ae": skmc.scrape,
    "sharjahcmc.ae": sharjahcmc.scrape,
    "altaiecenter.com": altaie.scrape,
    "Tawam Hospital": tawam.scrape,
    "Dhafrah Hospitals": dhafrah.scrape,
    "Enfield Royal Clinic": royalclinic.scrape,
    "Mezyad Health Care Center - Al Ain": mezyadmc.scrape,
    "Liv Hospital City Walk": livhospital.scrape,
    "Harley Street Medical Center": hsmc.scrape,
    "Gargash Hospital": gargashhospital.scrape,
}

class QtLogHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.append(msg)

class ScraperWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    
    def __init__(self, domain, scrape_func):
        super().__init__()
        self.domain = domain
        self.scrape_func = scrape_func
        self.is_running = True
    
    def run(self):
        try:
            self.log_signal.emit(f"[*] بدء استخراج البيانات لـ {self.domain}")
            self.progress_signal.emit(0)
            
            import inspect
            sig = inspect.signature(self.scrape_func)
            has_callback = len(sig.parameters) > 0
            
            if has_callback:
                def progress_callback(progress):
                    if self.is_running:
                        self.progress_signal.emit(progress)
                        self.log_signal.emit(f"[>] تقدم {self.domain}: {progress}%")
                self.scrape_func(progress_callback)
            else:
                self.scrape_func()
                self.progress_signal.emit(100)
            
            if self.is_running:
                self.log_signal.emit(f"[+] اكتمل استخراج بيانات {self.domain} بنجاح")
        except Exception as e:
            if self.is_running:
                self.log_signal.emit(f"[!] خطأ في استخراج بيانات {self.domain}: {str(e)}")
                self.progress_signal.emit(0)
    
    def stop(self):
        self.is_running = False

class UAEScraperGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("مستخرج بيانات الإمارات")
        self.setGeometry(100, 100, 1000, 800)
        
        # Apply the enhanced stylesheet
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
            QListWidget {
                background-color: rgba(255, 255, 255, 0.05);
                color: #e0e7ff;
                border: 2px solid rgba(0, 255, 255, 0.5);
                border-radius: 12px;
                padding: 8px;
                outline: none;
                animation: glow 3s infinite;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid rgba(0, 255, 255, 0.2);
                color: #e0e7ff;
            }
            QListWidget::item:hover {
                background-color: rgba(0, 255, 255, 0.1);
                color: #00FFFF;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00FFFF, stop:1 #FF00FF);
                color: #ffffff;
                border-radius: 8px;
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
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.05);
                border: 2px solid rgba(0, 255, 255, 0.5);
                border-radius: 10px;
                text-align: center;
                color: #e0e7ff;
                font-size: 14px;
                padding: 4px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF00FF, stop:1 #00FFFF);
                border-radius: 8px;
                animation: pulse 2s infinite;
            }
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.05);
                color: #e0e7ff;
                border: 2px solid rgba(0, 255, 255, 0.4);
                border-radius: 12px;
                padding: 12px;
                backdrop-filter: blur(10px);
                font-size: 13px;
            }
            QTextEdit:focus {
                border: 2px solid #00FFFF;
                box-shadow: 0 0 16px rgba(0, 255, 255, 0.6);
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
        """)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.scraper_list = QListWidget()
        self.scraper_list.setFont(QFont("Noto Sans Arabic", 12))
        self.scraper_list.setSpacing(4)
        for domain in SCRAPERS.keys():
            item = QListWidgetItem(domain)
            self.scraper_list.addItem(item)
        layout.addWidget(self.scraper_list)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.start_button = QPushButton("بدء استخراج الأهداف المحددة")
        self.start_button.clicked.connect(self.start_selected)
        self.start_button.setFont(QFont("Noto Sans Arabic", 12))
        button_layout.addWidget(self.start_button)
        
        self.start_all_button = QPushButton("بدء استخراج جميع الأنظمة")
        self.start_all_button.clicked.connect(self.start_all)
        self.start_all_button.setFont(QFont("Noto Sans Arabic", 12))
        button_layout.addWidget(self.start_all_button)
        
        layout.addLayout(button_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFont(QFont("Noto Sans Arabic", 10))
        self.progress_bar.setFormat("تقدم الاستخراج: %p%")
        layout.addWidget(self.progress_bar)
        
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Noto Sans Arabic", 10))
        layout.addWidget(self.console)
        
        self.log_handler = QtLogHandler(self.console)
        self.log_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s', 
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger = logging.getLogger()
        logger.addHandler(self.log_handler)
        logger.setLevel(logging.INFO)
        
        sys.stdout = Stream(self.console)
        
        self.workers = {}
        self.progress_values = {}
        
    def log_message(self, message):
        self.console.append(message)
        
    def update_progress(self, value):
        sender = self.sender()
        if sender and hasattr(sender, 'domain'):
            self.progress_values[sender.domain] = value
            total_progress = sum(self.progress_values.values()) / len(self.workers) if self.workers else 0
            self.progress_bar.setValue(int(total_progress))
        
    def start_selected(self):
        selected_items = self.scraper_list.selectedItems()
        if not selected_items:
            self.log_message("[!] لم يتم اختيار أي أهداف!")
            return
            
        for item in selected_items:
            domain = item.text()
            if domain not in self.workers:
                self.start_scraper(domain)
            else:
                self.log_message(f"[*] {domain} قيد الاستخراج بالفعل")
        
        if self.workers:
            self.toggle_buttons(True)
            
    def start_all(self):
        for domain in SCRAPERS.keys():
            if domain not in self.workers:
                self.start_scraper(domain)
            else:
                self.log_message(f"[*] {domain} قيد الاستخراج بالفعل")
                
        if self.workers:
            self.toggle_buttons(True)
            
    def start_scraper(self, domain):
        if domain in SCRAPERS:
            worker = ScraperWorker(domain, SCRAPERS[domain])
            worker.log_signal.connect(self.log_message)
            worker.progress_signal.connect(self.update_progress)
            worker.finished.connect(lambda: self.worker_finished(domain))
            self.workers[domain] = worker
            self.progress_values[domain] = 0
            worker.start()
        else:
            self.log_message(f"[!] لا يوجد مستخرج متاح لـ {domain}")
            
    def worker_finished(self, domain):
        if domain in self.workers:
            del self.workers[domain]
            del self.progress_values[domain]
        if not self.workers:
            self.toggle_buttons(False)
            self.progress_bar.setValue(100)
            self.log_message("[+] اكتملت جميع عمليات الاستخراج")
        else:
            total_progress = sum(self.progress_values.values()) / len(self.workers) if self.workers else 0
            self.progress_bar.setValue(int(total_progress))
            
    def toggle_buttons(self, running):
        self.start_button.setEnabled(not running)
        self.start_all_button.setEnabled(not running)

class Stream:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, text):
        self.text_widget.append(text.strip())

    def flush(self):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UAEScraperGUI()
    window.show()
    sys.exit(app.exec_())