"""
主窗口 GUI 模块
基于 PyQt5 的系统时间修改工具界面
"""

import sys
import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGroupBox, QMessageBox, QTextEdit,
    QProgressBar, QStatusBar, QGridLayout, QFrame
)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPalette

from time_manager import TimeManager
from ntp_client import NTPClient
from error_handler import (
    ErrorHandler, ConfirmationDialog, OperationHistory,
    setup_global_error_handler, safe_execute
)


class NTPSyncThread(QThread):
    """NTP 同步线程，避免阻塞 UI"""
    finished = pyqtSignal(bool, str)
    
    def __init__(self, time_manager):
        super().__init__()
        self.time_manager = time_manager
        self.ntp_client = NTPClient()
    
    def run(self):
        success, message = self.ntp_client.sync_system_time(self.time_manager)
        self.finished.emit(success, message)


class TimeToolMainWindow(QMainWindow):
    """系统时间修改工具主窗口"""
    
    def __init__(self):
        super().__init__()
        self.time_manager = TimeManager()
        self.ntp_thread = None

        # 设置错误处理器
        self.error_handler = setup_global_error_handler(self)
        self.operation_history = OperationHistory()

        # 检查管理员权限
        if not self.time_manager.is_admin():
            self.show_admin_warning()

        self.init_ui()
        self.setup_timer()

        # 记录启动日志
        self.log_message("应用程序启动成功")
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("Windows 系统时间修改工具")
        self.setFixedSize(500, 800)
        self.setStyleSheet(self.get_stylesheet())
        
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("系统时间修改工具")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin: 10px;")
        main_layout.addWidget(title_label)
        
        # 当前时间显示
        self.create_time_display(main_layout)
        
        # 快速调整按钮
        self.create_quick_adjust_buttons(main_layout)
        
        # NTP 同步按钮
        self.create_ntp_sync_button(main_layout)
        
        # 撤销按钮
        self.create_undo_button(main_layout)
        
        # 日志显示
        self.create_log_display(main_layout)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
        
    def create_time_display(self, layout):
        """创建时间显示区域"""
        time_group = QGroupBox("当前系统时间")
        time_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        time_layout = QVBoxLayout(time_group)
        
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            color: #27ae60; 
            background-color: #ecf0f1; 
            padding: 15px; 
            border-radius: 8px;
            border: 2px solid #bdc3c7;
        """)
        time_layout.addWidget(self.time_label)
        
        layout.addWidget(time_group)
        
    def create_quick_adjust_buttons(self, layout):
        """创建快速调整按钮"""
        adjust_group = QGroupBox("快速时间调整")
        adjust_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        adjust_layout = QGridLayout(adjust_group)
        
        # 按钮配置：(文本, 天数, 行, 列)
        buttons_config = [
            ("向后 7 天", -7, 0, 0),
            ("向后 3 天", -3, 0, 1),
            ("向前 3 天", 3, 1, 0),
            ("向前 7 天", 7, 1, 1),
        ]
        
        for text, days, row, col in buttons_config:
            btn = QPushButton(text)
            btn.setStyleSheet(self.get_button_style())
            btn.clicked.connect(lambda checked, d=days: self.adjust_time(d))
            adjust_layout.addWidget(btn, row, col)
        
        layout.addWidget(adjust_group)
        
    def create_ntp_sync_button(self, layout):
        """创建 NTP 同步按钮"""
        ntp_group = QGroupBox("网络时间同步")
        ntp_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        ntp_layout = QVBoxLayout(ntp_group)
        
        self.ntp_button = QPushButton("同步网络时间 (NTP)")
        self.ntp_button.setStyleSheet(self.get_button_style("#3498db"))
        self.ntp_button.clicked.connect(self.sync_ntp_time)
        ntp_layout.addWidget(self.ntp_button)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        ntp_layout.addWidget(self.progress_bar)
        
        layout.addWidget(ntp_group)
        
    def create_undo_button(self, layout):
        """创建撤销按钮"""
        undo_group = QGroupBox("撤销操作")
        undo_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        undo_layout = QVBoxLayout(undo_group)
        
        self.undo_button = QPushButton("撤销上次时间更改")
        self.undo_button.setStyleSheet(self.get_button_style("#e74c3c"))
        self.undo_button.clicked.connect(self.undo_last_change)
        self.undo_button.setEnabled(False)
        undo_layout.addWidget(self.undo_button)
        
        layout.addWidget(undo_group)
        
    def create_log_display(self, layout):
        """创建日志显示区域"""
        log_group = QGroupBox("操作日志")
        log_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(120)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            background-color: #2c3e50; 
            color: #ecf0f1; 
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 10px;
            border: 1px solid #34495e;
            border-radius: 4px;
        """)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
    def setup_timer(self):
        """设置定时器更新时间显示"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time_display)
        self.timer.start(1000)  # 每秒更新一次
        self.update_time_display()
        
    def update_time_display(self):
        """更新时间显示"""
        current_time = self.time_manager.get_local_time()
        time_str = current_time.strftime("%Y-%m-%d %H:%M:%S %A")
        self.time_label.setText(time_str)
        
        # 更新撤销按钮状态
        self.undo_button.setEnabled(self.time_manager.can_undo())
        
    def adjust_time(self, days):
        """调整系统时间"""
        if not self.time_manager.is_admin():
            self.show_admin_warning()
            return

        def _perform_adjustment():
            current_time = self.time_manager.get_local_time()
            new_time = current_time + datetime.timedelta(days=days)

            # 使用新的确认对话框
            if ConfirmationDialog.confirm_time_change(
                self,
                current_time.strftime('%Y-%m-%d %H:%M:%S'),
                new_time.strftime('%Y-%m-%d %H:%M:%S'),
                f"将系统时间调整 {'+' if days > 0 else ''}{days} 天"
            ):
                success, message = self.time_manager.adjust_time(days=days)

                # 记录操作历史
                self.operation_history.add_operation(
                    "时间调整",
                    f"调整 {'+' if days > 0 else ''}{days} 天",
                    current_time,
                    new_time if success else None
                )

                self.log_message(f"时间调整 ({'+' if days > 0 else ''}{days} 天): {message}")

                if success:
                    self.statusBar().showMessage("时间调整成功", 3000)
                else:
                    self.error_handler.handle_error("时间调整失败", message)

                return success
            return False

        # 安全执行调整操作
        safe_execute(_perform_adjustment, self.error_handler)
                
    def sync_ntp_time(self):
        """同步 NTP 时间"""
        if not self.time_manager.is_admin():
            self.show_admin_warning()
            return

        def _perform_ntp_sync():
            # 使用新的确认对话框
            if ConfirmationDialog.confirm_ntp_sync(self):
                current_time = self.time_manager.get_local_time()

                self.ntp_button.setEnabled(False)
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 0)  # 无限进度条
                self.statusBar().showMessage("正在同步网络时间...")

                # 记录操作开始
                self.log_message("开始 NTP 时间同步...")

                # 启动 NTP 同步线程
                self.ntp_thread = NTPSyncThread(self.time_manager)
                self.ntp_thread.finished.connect(
                    lambda success, message: self.on_ntp_sync_finished(success, message, current_time)
                )
                self.ntp_thread.start()

                return True
            return False

        # 安全执行 NTP 同步
        safe_execute(_perform_ntp_sync, self.error_handler)
            
    def on_ntp_sync_finished(self, success, message, old_time=None):
        """NTP 同步完成回调"""
        self.ntp_button.setEnabled(True)
        self.progress_bar.setVisible(False)

        # 记录操作历史
        if old_time:
            new_time = self.time_manager.get_local_time() if success else None
            self.operation_history.add_operation(
                "NTP 同步",
                "网络时间同步",
                old_time,
                new_time
            )

        self.log_message(f"NTP 同步: {message}")

        if success:
            self.statusBar().showMessage("NTP 同步成功", 3000)
            self.error_handler.show_info_dialog("同步成功", message)
        else:
            self.statusBar().showMessage("NTP 同步失败", 3000)
            self.error_handler.handle_error("NTP 同步失败", message)
            
    def undo_last_change(self):
        """撤销上次时间更改"""
        if not self.time_manager.can_undo():
            QMessageBox.information(self, "无法撤销", "没有可撤销的时间更改")
            return
            
        reply = QMessageBox.question(
            self,
            "确认撤销",
            "确定要撤销上次的时间更改吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = self.time_manager.undo_last_change()
            self.log_message(f"撤销操作: {message}")
            
            if success:
                self.statusBar().showMessage("撤销成功", 3000)
            else:
                QMessageBox.warning(self, "撤销失败", message)
                
    def show_admin_warning(self):
        """显示管理员权限警告"""
        QMessageBox.warning(
            self,
            "需要管理员权限",
            "修改系统时间需要管理员权限。\n\n"
            "请以管理员身份运行此程序，或者程序将尝试请求权限。"
        )
        
    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_text.append(log_entry)
        
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def get_stylesheet(self):
        """获取应用程序样式表"""
        return """
            QMainWindow {
                background-color: #f8f9fa;
            }
            QGroupBox {
                font-size: 12px;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: #f8f9fa;
            }
        """
        
    def get_button_style(self, color="#2ecc71"):
        """获取按钮样式"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 12px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(color, 0.8)};
            }}
            QPushButton:disabled {{
                background-color: #bdc3c7;
                color: #7f8c8d;
            }}
        """
        
    def darken_color(self, color, factor=0.9):
        """使颜色变暗"""
        # 简单的颜色变暗实现
        color_map = {
            "#2ecc71": "#27ae60",
            "#3498db": "#2980b9",
            "#e74c3c": "#c0392b"
        }
        return color_map.get(color, "#2c3e50")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("Windows 系统时间修改工具")
    app.setApplicationVersion("1.0")
    
    # 设置应用程序图标（如果有的话）
    # app.setWindowIcon(QIcon("icon.ico"))
    
    window = TimeToolMainWindow()
    window.show()
    
    sys.exit(app.exec_())
