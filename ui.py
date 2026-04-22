# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import configparser
import uuid
import os
import json
import logging
from system_tools import clean_temp_files, clear_dns_cache, schedule_shutdown, shutdown_now, cancel_shutdown
from websocket_client import PRTSWebSocketClient

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

CONFIG_FILE = "config.ini"
LOG_FILE = "prts.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PRTS")

class PRTSApp:
    def __init__(self, username=None, bound_client_id=None):
        self.username = username
        self.bound_client_id = bound_client_id

        self.root = ttk.Window(themename="minty")
        self.root.title("PRTS 系统工具箱")
        self.root.geometry("550x600")
        self.root.resizable(False, False)

        self.set_background()          # 关键方法
        self.config = configparser.ConfigParser()
        self.load_config()

        self.ws_client = None
        self.create_main_card()

        self.root.after(200, self.init_websocket)
        self.update_status()
        logger.info(f"PRTS 客户端启动，UID: {self.config.get('client', 'id')[:8]}...，用户: {self.username or '未登录'}")

    def set_background(self):
        """设置背景图片（毛玻璃效果）"""
        if not HAS_PIL:
            self.root.configure(bg="#f5f7fa")
            return
        try:
            if os.path.exists("prts.png"):
                img = Image.open("prts.png")
                img = img.resize((550, 600), Image.Resampling.LANCZOS)
                self.bg_image = ImageTk.PhotoImage(img)
                bg_label = tk.Label(self.root, image=self.bg_image)
                bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                overlay = tk.Frame(self.root, bg="#f5f7fa")
                overlay.place(x=0, y=0, relwidth=1, relheight=1)
                overlay.lower(bg_label)
            else:
                self.root.configure(bg="#f5f7fa")
        except Exception as e:
            logger.error(f"背景图片加载失败: {e}")
            self.root.configure(bg="#f5f7fa")

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

    def init_websocket(self):
        self.ws_client = PRTSWebSocketClient(
            server_url=self.config.get("server", "url", fallback="ws://8.153.36.132:8765"),
            client_id=self.config.get("client", "id"),
            on_message_callback=self.on_ws_message
        )
        self.ws_client.start()

    def create_main_card(self):
        self.card = ttk.Frame(self.root, bootstyle="light", padding=25)
        self.card.place(relx=0.5, rely=0.5, anchor="center", width=500, height=550)

        title = ttk.Label(self.card, text="PRTS 系统工具箱", font=("微软雅黑", 22, "bold"), bootstyle="inverse-primary")
        title.pack(pady=(0, 5))

        info_frame = ttk.Frame(self.card)
        info_frame.pack(fill="x", pady=5)

        user_label = ttk.Label(info_frame, text=f"👤 {self.username or '未登录'}", font=("微软雅黑", 10), bootstyle="secondary")
        user_label.pack(side="left", padx=5)

        self.status_var = tk.StringVar(value="连接中...")
        self.status_badge = ttk.Label(info_frame, textvariable=self.status_var, font=("微软雅黑", 10), bootstyle="warning")
        self.status_badge.pack(side="right", padx=5)

        uid_short = self.config.get("client", "id")[:8] + "..."
        uid_label = ttk.Label(info_frame, text=f"🆔 {uid_short}", font=("微软雅黑", 9), bootstyle="light")
        uid_label.pack(side="right", padx=5)

        ttk.Separator(self.card, bootstyle="primary").pack(fill="x", pady=10)

        func_frame = ttk.Frame(self.card)
        func_frame.pack(fill="both", expand=True, pady=10)
        self.create_func_button(func_frame, "🧹 清理临时文件", self.do_clean_temp, 0, 0)
        self.create_func_button(func_frame, "🌐 刷新 DNS 缓存", self.do_clear_dns, 0, 1)

        shutdown_frame = ttk.Labelframe(self.card, text="⏻ 关机控制", bootstyle="info", padding=15)
        shutdown_frame.pack(fill="x", pady=15)

        timer_row = ttk.Frame(shutdown_frame)
        timer_row.pack(fill="x", pady=5)
        ttk.Label(timer_row, text="定时关机(分钟):", font=("微软雅黑", 10)).pack(side="left", padx=5)
        self.minutes_entry = ttk.Entry(timer_row, width=8, font=("微软雅黑", 11), bootstyle="primary")
        self.minutes_entry.pack(side="left", padx=5)
        ttk.Button(timer_row, text="设置", command=self.do_schedule, bootstyle="warning", width=8).pack(side="left", padx=5)
        ttk.Button(timer_row, text="取消", command=self.do_cancel_shutdown, bootstyle="secondary", width=8).pack(side="left", padx=5)

        shutdown_btn = ttk.Button(shutdown_frame, text="⚠️ 立即关机", command=self.do_shutdown_now,
                                  bootstyle="danger", width=20, padding=10)
        shutdown_btn.pack(pady=15)

        menu_frame = ttk.Frame(self.card)
        menu_frame.pack(fill="x", pady=10)
        ttk.Button(menu_frame, text="📋 查看 UID", command=self.show_uid, bootstyle="outline-primary").pack(side="left", padx=5)
        ttk.Button(menu_frame, text="🔗 绑定账号", command=self.show_bind_window, bootstyle="outline-success").pack(side="left", padx=5)

        ttk.Label(self.card, text="服务器: 8.153.36.132:8765", font=("微软雅黑", 8), bootstyle="secondary").pack(side="bottom", pady=5)

    def create_func_button(self, parent, text, command, row, col):
        btn = ttk.Button(parent, text=text, command=command, bootstyle="primary-outline", width=20, padding=8)
        btn.grid(row=row, column=col, padx=10, pady=10)

    def update_status(self):
        if self.ws_client and self.ws_client.connected:
            self.status_var.set("✅ 已连接")
            self.status_badge.config(bootstyle="success")
        else:
            self.status_var.set("❌ 未连接")
            self.status_badge.config(bootstyle="danger")
        self.root.after(1000, self.update_status)

    def on_ws_message(self, data):
        if data.get("type") == "status":
            logger.info(f"服务端状态: {data.get('message')}")

    def do_clean_temp(self):
        logger.info("执行清理临时文件")
        result = clean_temp_files()
        messagebox.showinfo("清理结果", result)

    def do_clear_dns(self):
        logger.info("执行刷新DNS缓存")
        result = clear_dns_cache()
        messagebox.showinfo("DNS 缓存", result)

    def do_schedule(self):
        try:
            mins = int(self.minutes_entry.get())
            schedule_shutdown(mins)
            logger.info(f"设置定时关机: {mins} 分钟后")
            messagebox.showinfo("定时关机", f"系统将在 {mins} 分钟后关机")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的分钟数")

    def do_cancel_shutdown(self):
        cancel_shutdown()
        logger.info("取消定时关机")
        messagebox.showinfo("取消定时", "已取消定时关机")

    def do_shutdown_now(self):
        if messagebox.askyesno("确认关机", "确定要立即关闭计算机吗？"):
            logger.warning("用户确认立即关机")
            shutdown_now()

    def show_uid(self):
        uid = self.config.get("client", "id")
        win = ttk.Toplevel(self.root, title="我的 UID", resizable=(False, False))
        win.geometry("450x180")
        ttk.Label(win, text="您的电脑唯一标识符 (UID):", font=("微软雅黑", 11)).pack(pady=15)
        uid_entry = ttk.Entry(win, font=("微软雅黑", 10), width=45, justify="center", bootstyle="primary")
        uid_entry.insert(0, uid)
        uid_entry.config(state="readonly")
        uid_entry.pack(pady=5)
        ttk.Button(win, text="复制到剪贴板", command=lambda: self.root.clipboard_append(uid), bootstyle="info").pack(pady=10)
        logger.info("查看UID")

    def show_bind_window(self):
        if not self.username:
            messagebox.showerror("错误", "请先登录")
            return
        win = ttk.Toplevel(self.root, title="绑定账号", resizable=(False, False))
        win.geometry("350x180")
        ttk.Label(win, text=f"当前登录用户: {self.username}", font=("微软雅黑", 10)).pack(pady=15)
        ttk.Label(win, text="点击确认将本机UID与您的账号绑定", font=("微软雅黑", 9), bootstyle="secondary").pack()

        def do_bind():
            if self.ws_client and self.ws_client.ws:
                self.ws_client.ws.send(json.dumps({
                    "action": "bind_client",
                    "username": self.username,
                    "client_id": self.config.get("client", "id")
                }))
                messagebox.showinfo("提示", "绑定请求已发送")
                logger.info(f"请求绑定账号: {self.username} -> {self.config.get('client', 'id')[:8]}...")
                win.destroy()
            else:
                messagebox.showerror("错误", "WebSocket 未连接")

        ttk.Button(win, text="确认绑定", command=do_bind, bootstyle="success").pack(pady=15)

    def run(self):
        self.root.mainloop()
        if self.ws_client:
            self.ws_client.stop()
        logger.info("PRTS 客户端退出")