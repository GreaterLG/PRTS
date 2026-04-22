# -*- coding: utf-8 -*-
import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from login_window import LoginWindow
from main_window import MainWindow
from utils import resource_path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("prts.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 设置应用程序全局图标（影响任务栏）
    icon_path = resource_path("prtscl.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    login = LoginWindow()
    login.show()

    def on_login_success(username, bound_client_id):
        global main_win
        main_win = MainWindow(username, bound_client_id)
        main_win.show()
        login.close()

    login.login_success_signal.connect(on_login_success)
    sys.exit(app.exec_())