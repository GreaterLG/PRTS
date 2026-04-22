# -*- coding: utf-8 -*-
import json
import threading
import time
import websocket
import logging
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger("PRTS")

class PRTSWebSocketClient(QObject):
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    message_received = pyqtSignal(dict)
    shutdown_triggered = pyqtSignal(int, str)  # delay, message

    def __init__(self, server_url, client_id):
        super().__init__()
        self.url = server_url
        self.client_id = client_id
        self.ws = None
        self.running = False
        self._connected = False

    @property
    def is_connected(self):
        return self._connected

    def start(self):
        self.running = True
        self._connect()

    def _connect(self):
        if not self.running:
            return
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        threading.Thread(target=self.ws.run_forever, daemon=True).start()

    def _on_open(self, ws):
        self._connected = True
        logger.info("WebSocket 连接成功")
        self.connected.emit()
        ws.send(json.dumps({"type": "register", "client_id": self.client_id}))
        threading.Thread(target=self._heartbeat, daemon=True).start()

    def _heartbeat(self):
        while self.running and self._connected:
            time.sleep(30)
            try:
                if self.ws and self.ws.sock and self.ws.sock.connected:
                    self.ws.send(json.dumps({"type": "ping"}))
            except:
                break

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
        except:
            return
        logger.debug(f"收到消息: {data}")
        if data.get("action") == "shutdown":
            self.shutdown_triggered.emit(0, "立即关机")
        elif data.get("action") == "delayed_shutdown":
            delay = data.get("delay", 30)
            msg = data.get("message", "远程关机指令")
            self.shutdown_triggered.emit(delay, msg)
        self.message_received.emit(data)

    def _on_error(self, ws, error):
        logger.error(f"WebSocket 错误: {error}")

    def _on_close(self, ws, code, msg):
        self._connected = False
        logger.warning("WebSocket 连接关闭，5秒后重连...")
        self.disconnected.emit()
        if self.running:
            time.sleep(5)
            self._connect()

    def send(self, data):
        if self.ws and self._connected:
            self.ws.send(json.dumps(data))

    def stop(self):
        self.running = False
        if self.ws:
            self.ws.close()
        logger.info("WebSocket 客户端已停止")