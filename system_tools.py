# -*- coding: utf-8 -*-
import os
import subprocess
import tempfile
import shutil
import threading
import time
from PyQt5.QtWidgets import QMessageBox, QPushButton, QVBoxLayout, QLabel, QDialog

def clean_temp_files():
    try:
        temp_dir = tempfile.gettempdir()
        count = 0
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    count += 1
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
                    count += 1
            except:
                pass
        return f"清理完成，共删除 {count} 个临时文件/文件夹"
    except Exception as e:
        return f"清理失败: {e}"

def clear_dns_cache():
    try:
        result = subprocess.run("ipconfig /flushdns", shell=True, capture_output=True, text=True)
        if "Successfully flushed" in result.stdout:
            return "DNS 缓存刷新成功"
        else:
            return f"刷新失败: {result.stdout}"
    except Exception as e:
        return f"执行失败: {e}"

def shutdown_now():
    os.system("shutdown /s /t 0")

def schedule_shutdown(minutes: int):
    seconds = minutes * 60
    os.system(f"shutdown /s /t {seconds}")

def cancel_shutdown():
    os.system("shutdown /a")

class CountdownDialog(QDialog):
    """延迟关机倒计时窗口"""
    def __init__(self, seconds, message, parent=None):
        super().__init__(parent)
        self.seconds = seconds
        self.message = message
        self.setWindowTitle("远程关机")
        self.setFixedSize(320, 160)
        self.setModal(True)
        self.init_ui()
        self.start_countdown()

    def init_ui(self):
        layout = QVBoxLayout()
        msg_label = QLabel(self.message)
        msg_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(msg_label)

        self.time_label = QLabel(f"系统将在 {self.seconds} 秒后关机...")
        self.time_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c;")
        layout.addWidget(self.time_label)

        cancel_btn = QPushButton("取消关机")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover { background-color: #e67e22; }
        """)
        cancel_btn.clicked.connect(self.cancel)
        layout.addWidget(cancel_btn)

        self.setLayout(layout)

    def start_countdown(self):
        def countdown():
            remain = self.seconds
            while remain > 0:
                time.sleep(1)
                remain -= 1
                self.time_label.setText(f"系统将在 {remain} 秒后关机...")
            self.accept()
            shutdown_now()
        threading.Thread(target=countdown, daemon=True).start()

    def cancel(self):
        cancel_shutdown()
        self.reject()