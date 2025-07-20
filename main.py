#!/usr/bin/env python3
"""
Windows 系统时间修改工具
主程序入口文件

功能：
- 快速调整系统时间（±3天、±7天）
- NTP 网络时间同步
- 管理员权限管理
- 操作日志记录
- 撤销功能
"""

import sys
import os
import ctypes
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

from main_window import TimeToolMainWindow
from time_manager import TimeManager


def check_admin_privileges():
    """检查并请求管理员权限"""
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        return is_admin
    except:
        return False


def request_admin_privileges():
    """请求管理员权限并重新启动程序"""
    try:
        # 重新启动程序并请求管理员权限
        ctypes.windll.shell32.ShellExecuteW(
            None, 
            "runas", 
            sys.executable, 
            " ".join(sys.argv), 
            None, 
            1
        )
        return True
    except Exception as e:
        return False



def main():
    """主函数"""
    # 检查管理员权限
    if not check_admin_privileges():
        # 直接请求管理员权限
        if request_admin_privileges():
            return

    # 创建并运行应用程序
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Windows 系统时间修改工具")
        app.setApplicationVersion("1.0")
        app.setOrganizationName("TimeTools")

        # 设置应用程序图标
        icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
        if os.path.exists(icon_path):
            from PyQt5.QtGui import QIcon
            app.setWindowIcon(QIcon(icon_path))

        # 设置应用程序属性
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # 创建主窗口
        window = TimeToolMainWindow()
        window.show()

        # 运行应用程序
        exit_code = app.exec_()
        return exit_code

    except ImportError as e:
        return 1

    except Exception as e:
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        sys.exit(1)
