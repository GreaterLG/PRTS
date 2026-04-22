<details> <summary>📄 点击此处展开完整 README.md 内容（全选复制即可）</summary>
🔧 PRTS 系统工具箱
<p align="center"> <img src="prtscl.ico" alt="PRTS Icon" width="80"/> </p><p align="center"> <img src="prts.png" alt="PRTS Banner" width="600"/> </p><p align="center"> <img src="https://img.shields.io/badge/Platform-Windows-blue?logo=windows" alt="Platform"> <img src="https://img.shields.io/badge/Python-3.8%2B-brightgreen?logo=python" alt="Python"> <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License"> <img src="https://img.shields.io/badge/PRTS-v2.0.0-orange" alt="Version"> </p><p align="center"> <b>一款集本地系统维护、远程关机控制、账号管理于一体的现代化桌面工具箱</b> </p>
✨ 主要功能
🖥️ 本地系统维护
一键清理临时文件、刷新 DNS 缓存，保持系统清爽流畅。

⏻ 灵活关机控制
支持立即关机、定时关机（分钟级），并提供 30 秒倒计时缓冲，防止误操作。

🌐 远程关机中继
通过阿里云服务器 WebSocket 中继，手机/电脑浏览器访问网页即可远程关闭家中或办公室的电脑。

👤 用户体系
注册 / 登录账号，绑定多台电脑 UID，精准控制不同设备。

🔐 记住密码
登录凭据加密存储在用户目录，安全便捷。

🎨 现代化 UI
基于 PyQt5 精心设计的毛玻璃风格界面，支持自定义背景图片和图标。

📦 单文件便携
使用 PyInstaller 打包为单个 EXE，无需安装 Python 环境即可运行。

📸 界面预览
登录窗口	主界面
https://login.png	https://main.png
注：截图中的背景图 prts.png 可自行替换，程序会自动缩放至 30% 并居中显示。

🚀 快速开始
环境要求
Windows 10 / 11

无 Python 环境也可直接运行打包好的 PRTS.exe

直接使用（推荐）
下载最新版 PRTS.exe（位于 dist 目录）。

确保同级目录下有 prts.png（背景图）和 prtscl.ico（图标）——已包含在发行包中。

双击运行，首次启动会自动生成配置文件 .prts_config.ini（保存在用户目录）。

从源码运行
bash
git clone <your-repo-url>
cd PRTS
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
服务器端部署请参考项目 Wiki 中的 服务端部署指南（需自行配置阿里云 CentOS 宝塔环境及 MySQL 数据库）。

📦 打包为单文件 EXE
项目提供了 build.bat 一键打包脚本，使用前请确保：

虚拟环境 .venv 已创建并安装所有依赖

资源文件 prts.png、prtscl.ico 位于项目根目录

双击 build.bat 即可在 dist 目录生成 PRTS.exe。

手动打包命令
bash
pyinstaller --onefile --windowed --name PRTS --icon=prtscl.ico ^
    --add-data "prts.png;." --add-data "prtscl.ico;." ^
    --add-data ".venv\Lib\site-packages\websocket;websocket" ^
    --hidden-import hmac --hidden-import hashlib --hidden-import socket ^
    --hidden-import ssl --hidden-import http --hidden-import email ^
    --hidden-import PyQt5.sip main.py
🗂️ 项目结构
text
PRTS/
├── main.py                 # 程序入口
├── login_window.py         # 登录/注册界面
├── main_window.py          # 主功能界面
├── websocket_client.py     # WebSocket 长连接客户端
├── system_tools.py         # 系统维护与关机函数
├── utils.py                # 资源路径辅助函数
├── requirements.txt        # Python 依赖清单
├── build.bat               # 自动打包脚本
├── prts.png                # 背景图片（已内置）
├── prtscl.ico              # 程序图标（已内置）
├── login.png               # 登录界面截图
├── main.png                # 主界面截图
└── README.md               # 本文件
🛠️ 技术栈
模块	技术选型
GUI 框架	PyQt5 + QSS 样式表
网络通信	websocket-client (长连接)
数据加密	cryptography (Fernet)
打包工具	PyInstaller
服务端中继	Python websockets + aiomysql + MySQL
📝 更新日志
v2.0.0 (2026-04-22)
新增：用户注册/登录体系，支持多设备绑定

新增：远程关机延迟 30 秒倒计时，可中途取消

优化：UI 全面升级为 PyQt5 毛玻璃风格

优化：配置文件迁移至用户目录，解决权限问题

修复：PyInstaller 打包后标准库缺失问题

v1.0.0 (2026-04-01)
初始版本发布，包含本地维护与基础远程关机

🤝 贡献
欢迎提交 Issue 和 Pull Request！如果您有任何建议或发现了 bug，请随时联系我们。

📄 许可证
本项目基于 MIT License 开源，您可自由使用、修改和分发。

<p align="center">Made with ❤️ by 牧歌</p> </details>
