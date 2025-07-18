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

作者：AI Assistant
版本：1.0
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
        print(f"请求管理员权限失败: {e}")
        return False


def show_startup_message():
    """显示启动消息"""
    app = QApplication(sys.argv)

    msg = QMessageBox()
    msg.setWindowTitle("Windows 系统时间修改工具")
    msg.setIcon(QMessageBox.Information)

    # 设置消息框图标
    icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
    if os.path.exists(icon_path):
        from PyQt5.QtGui import QIcon
        msg.setWindowIcon(QIcon(icon_path))
    msg.setText("欢迎使用 Windows 系统时间修改工具！")
    msg.setInformativeText(
        "此工具可以帮助您快速修改系统时间。\n\n"
        "功能包括：\n"
        "• 快速时间调整（±3天、±7天）\n"
        "• NTP 网络时间同步\n"
        "• 操作撤销功能\n"
        "• 详细的操作日志\n\n"
        "注意：修改系统时间需要管理员权限。"
    )
    msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    msg.setDefaultButton(QMessageBox.Ok)
    
    result = msg.exec_()
    app.quit()
    
    return result == QMessageBox.Ok


def main():
    """主函数"""
    print("Windows 系统时间修改工具 v1.0")
    print("=" * 40)
    
    # 检查管理员权限
    if not check_admin_privileges():
        print("警告：当前没有管理员权限")
        print("修改系统时间需要管理员权限")
        
        # 显示启动消息
        if not show_startup_message():
            print("用户取消启动")
            return
        
        print("尝试请求管理员权限...")
        if request_admin_privileges():
            print("已请求管理员权限，程序将重新启动")
            return
        else:
            print("无法获取管理员权限，程序将以受限模式运行")
    else:
        print("✓ 已获得管理员权限")

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
        
        print("应用程序已启动")
        print("GUI 界面已打开")
        
        # 运行应用程序
        exit_code = app.exec_()
        print(f"应用程序退出，退出代码: {exit_code}")
        
        return exit_code
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保已安装所有必要的依赖包：")
        print("pip install -r requirements.txt")
        return 1
        
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n用户中断程序")
        sys.exit(0)
    except Exception as e:
        print(f"程序异常退出: {e}")
        sys.exit(1)
