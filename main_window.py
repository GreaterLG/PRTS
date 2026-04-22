# -*- coding: utf-8 -*-
import os
import json
import logging
import configparser
import uuid

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QLineEdit, QMessageBox, QApplication,
    QMenuBar, QMenu, QAction
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPalette, QBrush, QPixmap, QIcon

from websocket_client import PRTSWebSocketClient
from system_tools import (
    clean_temp_files, clear_dns_cache, schedule_shutdown,
    shutdown_now, cancel_shutdown, CountdownDialog
)
from utils import resource_path

logger = logging.getLogger("PRTS")
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".prts_config.ini")

class MainWindow(QMainWindow):
    def __init__(self, username=None, bound_client_id=None):
        super().__init__()
        self.username = username
        self.bound_client_id = bound_client_id

        self.config = configparser.ConfigParser()
        self.load_config()

        self.ws_client = None
        self.init_ui()
        self.init_menu()
        self.init_websocket()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            self.config.read(CONFIG_FILE)
        else:
            self.config["server"] = {"url": "ws://8.153.36.132:8765"}
            self.config["client"] = {"id": str(uuid.uuid4())}
            with open(CONFIG_FILE, "w") as f:
                self.config.write(f)
        if not self.config.has_option("client", "id"):
            self.config.set("client", "id", str(uuid.uuid4()))
            with open(CONFIG_FILE, "w") as f:
                self.config.write(f)

    def init_ui(self):
        self.setWindowTitle("PRTS")

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
            self.setFixedSize(550, 600)
            self.setStyleSheet("background-color: #f5f7fa;")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 自适应卡片尺寸
        card_width = int(self.width() * 0.35)
        card_height = int(self.height() * 0.68)

        card = QFrame()
        card.setObjectName("card")
        card.setFixedSize(card_width, card_height)
        card.setStyleSheet("""
            QFrame#card {
                background-color: rgba(255, 255, 255, 0.85);
                border-radius: 30px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignTop)
        card_layout.setSpacing(15)
        card_layout.setContentsMargins(25, 25, 25, 25)

        # 标题
        title = QLabel("PRTS 系统工具箱")
        title.setFont(QFont("微软雅黑", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50;")
        card_layout.addWidget(title)

        # 信息栏
        info_frame = QFrame()
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(0, 0, 0, 0)

        user_label = QLabel(f"👤 {self.username or '未登录'}")
        user_label.setFont(QFont("微软雅黑", 10))
        user_label.setStyleSheet("color: #7f8c8d;")
        info_layout.addWidget(user_label, alignment=Qt.AlignLeft)

        self.status_label = QLabel("连接中...")
        self.status_label.setFont(QFont("微软雅黑", 10))
        self.status_label.setStyleSheet("color: #f39c12;")
        info_layout.addWidget(self.status_label, alignment=Qt.AlignRight)

        card_layout.addWidget(info_frame)

        uid_short = self.config.get("client", "id")+ "..."
        uid_label = QLabel(f"🆔 {uid_short}")
        uid_label.setFont(QFont("微软雅黑", 9))
        uid_label.setStyleSheet("color: #95a5a6;")
        uid_label.setAlignment(Qt.AlignLeft)
        card_layout.addWidget(uid_label)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #bdc3c7; max-height: 1px;")
        card_layout.addWidget(line)

        # 功能按钮
        func_frame = QFrame()
        func_layout = QHBoxLayout(func_frame)
        func_layout.setSpacing(20)

        clean_btn = QPushButton("🧹 清理临时文件")
        clean_btn.setFont(QFont("微软雅黑", 11))
        clean_btn.setStyleSheet(self._button_style("#3498db"))
        clean_btn.clicked.connect(self.do_clean_temp)
        func_layout.addWidget(clean_btn)

        dns_btn = QPushButton("🌐 刷新 DNS 缓存")
        dns_btn.setFont(QFont("微软雅黑", 11))
        dns_btn.setStyleSheet(self._button_style("#2ecc71"))
        dns_btn.clicked.connect(self.do_clear_dns)
        func_layout.addWidget(dns_btn)

        card_layout.addWidget(func_frame)

        # 关机控制区域
        shutdown_group = QFrame()
        shutdown_group.setObjectName("shutdownGroup")
        shutdown_group.setStyleSheet("""
            QFrame#shutdownGroup {
                background-color: rgba(236, 240, 241, 0.6);
                border-radius: 20px;
                padding: 15px;
            }
        """)
        shutdown_layout = QVBoxLayout(shutdown_group)

        timer_layout = QHBoxLayout()
        timer_layout.setSpacing(10)
        timer_label = QLabel("定时关机(分钟):")
        timer_label.setFont(QFont("微软雅黑", 10))
        timer_layout.addWidget(timer_label)

        self.minutes_edit = QLineEdit()
        self.minutes_edit.setFixedWidth(80)
        self.minutes_edit.setFont(QFont("微软雅黑", 11))
        self.minutes_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 10px;
                padding: 6px;
                background-color: rgba(255,255,255,0.9);
            }
        """)
        timer_layout.addWidget(self.minutes_edit)

        set_btn = QPushButton("设置")
        set_btn.setStyleSheet(self._button_style("#f39c12"))
        set_btn.clicked.connect(self.do_schedule)
        timer_layout.addWidget(set_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(self._button_style("#95a5a6"))
        cancel_btn.clicked.connect(self.do_cancel_shutdown)
        timer_layout.addWidget(cancel_btn)

        shutdown_layout.addLayout(timer_layout)

        shutdown_btn = QPushButton("⚠️ 立即关机")
        shutdown_btn.setFont(QFont("微软雅黑", 13, QFont.Bold))
        shutdown_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 20px;
                padding: 15px;
            }
            QPushButton:hover { background-color: #c0392b; }
            QPushButton:pressed { background-color: #a93226; }
        """)
        shutdown_btn.clicked.connect(self.do_shutdown_now)
        shutdown_layout.addWidget(shutdown_btn)

        card_layout.addWidget(shutdown_group)

        # 底部按钮
        bottom_layout = QHBoxLayout()
        uid_btn = QPushButton("📋 查看 UID")
        uid_btn.setStyleSheet(self._button_style("#3498db", outlined=True))
        uid_btn.clicked.connect(self.show_uid)
        bottom_layout.addWidget(uid_btn)

        bind_btn = QPushButton("🔗 绑定账号")
        bind_btn.setStyleSheet(self._button_style("#2ecc71", outlined=True))
        bind_btn.clicked.connect(self.show_bind_window)
        bottom_layout.addWidget(bind_btn)

        card_layout.addLayout(bottom_layout)

        server_label = QLabel("我会一直看着你")
        server_label.setFont(QFont("微软雅黑", 8))
        server_label.setStyleSheet("color: #95a5a6;")
        server_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(server_label)

        main_layout.addWidget(card)

        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)

    def _button_style(self, color, outlined=False):
        if outlined:
            return f"""
                QPushButton {{
                    background-color: transparent;
                    color: {color};
                    border: 1px solid {color};
                    border-radius: 12px;
                    padding: 8px 12px;
                }}
                QPushButton:hover {{ background-color: {color}22; }}
                QPushButton:pressed {{ background-color: {color}44; }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border-radius: 12px;
                    padding: 10px;
                }}
                QPushButton:hover {{ background-color: {self._darken(color)}; }}
                QPushButton:pressed {{ background-color: {self._darken(color, 0.8)}; }}
            """

    def _darken(self, hex_color, factor=0.85):
        return hex_color

    def init_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("background-color: rgba(255,255,255,0.7);")
        account_menu = menubar.addMenu("个人中心")
        view_uid_action = QAction("查看我的 UID", self)
        view_uid_action.triggered.connect(self.show_uid)
        account_menu.addAction(view_uid_action)
        bind_action = QAction("绑定账号", self)
        bind_action.triggered.connect(self.show_bind_window)
        account_menu.addAction(bind_action)

    def init_websocket(self):
        self.ws_client = PRTSWebSocketClient(
            server_url=self.config.get("server", "url", fallback="ws://8.153.36.132:8765"),
            client_id=self.config.get("client", "id")
        )
        self.ws_client.connected.connect(self.on_ws_connected)
        self.ws_client.disconnected.connect(self.on_ws_disconnected)
        self.ws_client.shutdown_triggered.connect(self.handle_shutdown)
        self.ws_client.start()

    def on_ws_connected(self):
        self.status_label.setText("✅ 已连接")
        self.status_label.setStyleSheet("color: #27ae60;")

    def on_ws_disconnected(self):
        self.status_label.setText("❌ 未连接")
        self.status_label.setStyleSheet("color: #e74c3c;")

    def update_status(self):
        pass

    def handle_shutdown(self, delay, message):
        if delay == 0:
            reply = QMessageBox.question(self, "远程关机", "收到立即关机指令，是否执行？",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                shutdown_now()
        else:
            dlg = CountdownDialog(delay, message, self)
            dlg.exec_()

    def do_clean_temp(self):
        result = clean_temp_files()
        QMessageBox.information(self, "清理结果", result)

    def do_clear_dns(self):
        result = clear_dns_cache()
        QMessageBox.information(self, "DNS 缓存", result)

    def do_schedule(self):
        try:
            mins = int(self.minutes_edit.text())
            schedule_shutdown(mins)
            QMessageBox.information(self, "定时关机", f"系统将在 {mins} 分钟后关机")
        except ValueError:
            QMessageBox.warning(self, "错误", "请输入有效的分钟数")

    def do_cancel_shutdown(self):
        cancel_shutdown()
        QMessageBox.information(self, "取消定时", "已取消定时关机")

    def do_shutdown_now(self):
        reply = QMessageBox.question(self, "确认关机", "确定要立即关闭计算机吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            shutdown_now()

    def show_uid(self):
        uid = self.config.get("client", "id")
        msg = QMessageBox(self)
        msg.setWindowTitle("我的 UID")
        msg.setText(f"您的电脑唯一标识符 (UID):\n\n{uid}")
        copy_btn = msg.addButton("复制", QMessageBox.ActionRole)
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(uid))
        msg.exec_()

    def show_bind_window(self):
        if not self.username:
            QMessageBox.warning(self, "错误", "请先登录")
            return
        reply = QMessageBox.question(self, "绑定账号",
                                     f"当前登录用户: {self.username}\n\n确认将本机UID与您的账号绑定吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.ws_client and self.ws_client.is_connected:
                self.ws_client.send({
                    "action": "bind_client",
                    "username": self.username,
                    "client_id": self.config.get("client", "id")
                })
                QMessageBox.information(self, "提示", "绑定请求已发送")
                logger.info(f"请求绑定账号: {self.username} -> {self.config.get('client', 'id')[:8]}...")

    def closeEvent(self, event):
        if self.ws_client:
            self.ws_client.stop()
        event.accept()