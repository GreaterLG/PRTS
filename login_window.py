# -*- coding: utf-8 -*-
import os
import json
import logging
import configparser
import base64
from cryptography.fernet import Fernet
import websocket

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QBrush, QPixmap, QIcon

from utils import resource_path

logger = logging.getLogger("PRTS")
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".prts_config.ini")

class WebSocketThread(QThread):
    connected = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, server_url):
        super().__init__()
        self.server_url = server_url
        self.ws = None

    def run(self):
        try:
            self.ws = websocket.WebSocket()
            self.ws.connect(self.server_url, timeout=5)
            self.connected.emit()
        except Exception as e:
            self.error.emit(str(e))

class LoginWindow(QWidget):
    login_success_signal = pyqtSignal(str, str)  # username, bound_client_id

    def __init__(self, server_url="ws://8.153.36.132:8765"):
        super().__init__()
        self.server_url = server_url
        self.ws = None
        self.ws_thread = None
        self.username = None
        self.bound_client_id = None

        self.config = configparser.ConfigParser()
        self.load_config()

        self.init_ui()
        self.connect_websocket()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            self.config.read(CONFIG_FILE)
        else:
            self.config["server"] = {"url": self.server_url}
            self.config["client"] = {}
            self.config["login"] = {}
            with open(CONFIG_FILE, "w") as f:
                self.config.write(f)

    def encrypt_password(self, password):
        key = Fernet.generate_key()
        cipher = Fernet(key)
        encrypted = cipher.encrypt(password.encode())
        return base64.b64encode(key + b"::" + encrypted).decode()

    def decrypt_password(self, encrypted_str):
        try:
            data = base64.b64decode(encrypted_str)
            key, encrypted = data.split(b"::", 1)
            cipher = Fernet(key)
            return cipher.decrypt(encrypted).decode()
        except:
            return ""

    def save_login_info(self, username, password, remember):
        self.config["login"]["username"] = username
        if remember:
            self.config["login"]["password"] = self.encrypt_password(password)
        else:
            if self.config.has_option("login", "password"):
                self.config.remove_option("login", "password")
        with open(CONFIG_FILE, "w") as f:
            self.config.write(f)

    def init_ui(self):
        self.setWindowTitle("PRTS 登录")

        # 设置窗口图标
        icon_path = resource_path("prtscl.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # ---------- 背景图片缩放至 30% ----------
        bg_path = resource_path("prts.png")
        if os.path.exists(bg_path):
            original_pixmap = QPixmap(bg_path)
            target_width = int(original_pixmap.width() * 0.3)
            target_height = int(original_pixmap.height() * 0.3)
            scaled_pixmap = original_pixmap.scaled(
                target_width, target_height,
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.setFixedSize(target_width, target_height)

            palette = QPalette()
            palette.setBrush(QPalette.Window, QBrush(scaled_pixmap))
            self.setPalette(palette)
        else:
            self.setFixedSize(400, 500)
            self.setStyleSheet("background-color: #f0f4fa;")

        # 主布局（卡片居中）
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("card")
        card.setFixedSize(340, 420)
        card.setStyleSheet("""
            QFrame#card {
                background-color: rgba(255, 255, 255, 0.85);
                border-radius: 20px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignCenter)
        card_layout.setSpacing(15)
        card_layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("🔧 PRTS")
        title.setFont(QFont("微软雅黑", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50;")
        card_layout.addWidget(title)

        subtitle = QLabel("系统工具箱")
        subtitle.setFont(QFont("微软雅黑", 12))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #7f8c8d;")
        card_layout.addWidget(subtitle)

        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("用户名")
        self.user_edit.setFont(QFont("微软雅黑", 11))
        self.user_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 12px;
                padding: 10px;
                background-color: rgba(255,255,255,0.9);
            }
            QLineEdit:focus { border: 1px solid #3498db; }
        """)
        card_layout.addWidget(self.user_edit)

        self.pwd_edit = QLineEdit()
        self.pwd_edit.setPlaceholderText("密码")
        self.pwd_edit.setEchoMode(QLineEdit.Password)
        self.pwd_edit.setFont(QFont("微软雅黑", 11))
        self.pwd_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 12px;
                padding: 10px;
                background-color: rgba(255,255,255,0.9);
            }
            QLineEdit:focus { border: 1px solid #3498db; }
        """)
        card_layout.addWidget(self.pwd_edit)

        self.remember_check = QCheckBox("记住密码")
        self.remember_check.setFont(QFont("微软雅黑", 9))
        self.remember_check.setStyleSheet("color: #34495e;")
        card_layout.addWidget(self.remember_check)

        if self.config.has_option("login", "username"):
            self.user_edit.setText(self.config.get("login", "username"))
            if self.config.has_option("login", "password"):
                pwd = self.decrypt_password(self.config.get("login", "password"))
                self.pwd_edit.setText(pwd)
                self.remember_check.setChecked(True)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        self.login_btn = QPushButton("登录")
        self.login_btn.setFont(QFont("微软雅黑", 11, QFont.Bold))
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 12px;
                padding: 10px;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:pressed { background-color: #1c5980; }
        """)
        self.login_btn.clicked.connect(self.do_login)
        btn_layout.addWidget(self.login_btn)

        self.register_btn = QPushButton("注册")
        self.register_btn.setFont(QFont("微软雅黑", 11, QFont.Bold))
        self.register_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border-radius: 12px;
                padding: 10px;
            }
            QPushButton:hover { background-color: #27ae60; }
            QPushButton:pressed { background-color: #1e8449; }
        """)
        self.register_btn.clicked.connect(self.do_register)
        btn_layout.addWidget(self.register_btn)

        card_layout.addLayout(btn_layout)

        self.status_label = QLabel("正在连接服务器...")
        self.status_label.setFont(QFont("微软雅黑", 9))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #95a5a6;")
        card_layout.addWidget(self.status_label)

        main_layout.addWidget(card)
        self.setLayout(main_layout)

    def connect_websocket(self):
        self.ws_thread = WebSocketThread(self.server_url)
        self.ws_thread.connected.connect(self.on_ws_connected)
        self.ws_thread.error.connect(self.on_ws_error)
        self.ws_thread.start()

    def on_ws_connected(self):
        self.ws = self.ws_thread.ws
        self.status_label.setText("✅ 服务器已连接")
        self.status_label.setStyleSheet("color: #27ae60;")
        logger.info("登录窗口连接服务器成功")

    def on_ws_error(self, err_msg):
        self.status_label.setText("❌ 无法连接服务器")
        self.status_label.setStyleSheet("color: #e74c3c;")
        logger.error(f"登录窗口连接失败: {err_msg}")

    def do_login(self):
        username = self.user_edit.text().strip()
        password = self.pwd_edit.text()
        if not username or not password:
            QMessageBox.warning(self, "错误", "请输入用户名和密码")
            return
        if not self.ws:
            QMessageBox.warning(self, "错误", "未连接到服务器")
            return

        try:
            self.ws.send(json.dumps({"action": "login", "username": username, "password": password}))
            resp = self.ws.recv()
            data = json.loads(resp)
            if data.get("success"):
                logger.info(f"用户 {username} 登录成功")
                self.username = username
                self.bound_client_id = data.get("bound_client_id")
                self.save_login_info(username, password, self.remember_check.isChecked())
                self.close()
                self.login_success_signal.emit(username, self.bound_client_id or "")
            else:
                QMessageBox.critical(self, "登录失败", data.get("error", "未知错误"))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"登录请求失败: {e}")

    def do_register(self):
        username = self.user_edit.text().strip()
        password = self.pwd_edit.text()
        if not username or not password:
            QMessageBox.warning(self, "错误", "请输入用户名和密码")
            return
        if not self.ws:
            QMessageBox.warning(self, "错误", "未连接到服务器")
            return

        try:
            self.ws.send(json.dumps({"action": "register_user", "username": username, "password": password}))
            resp = self.ws.recv()
            data = json.loads(resp)
            if data.get("success"):
                QMessageBox.information(self, "注册成功", "注册成功，请登录")
                logger.info(f"新用户注册: {username}")
            else:
                QMessageBox.critical(self, "注册失败", data.get("result", "未知错误"))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"注册请求失败: {e}")

    def closeEvent(self, event):
        if self.ws:
            self.ws.close()
        event.accept()