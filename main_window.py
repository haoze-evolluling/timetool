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
from PyQt5.QtGui import QFont, QIcon, QPalette, QFontMetrics

from time_manager import TimeManager
from ntp_client import WindowsTimeSync
from error_handler import (
    ErrorHandler, ConfirmationDialog, OperationHistory,
    setup_global_error_handler, safe_execute
)


class NTPSyncThread(QThread):
    """Windows 时间同步线程，避免阻塞 UI"""
    finished = pyqtSignal(bool, str)

    def __init__(self, time_manager=None):
        super().__init__()
        self.time_manager = time_manager  # 保留兼容性，但不使用
        self.time_sync = WindowsTimeSync()

    def run(self):
        success, message = self.time_sync.sync_system_time()
        self.finished.emit(success, message)


class TimeToolMainWindow(QMainWindow):
    """系统时间修改工具主窗口"""
    
    def __init__(self):
        super().__init__()
        # 设置窗口图标
        import os
        from PyQt5.QtGui import QIcon
        icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
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

    def setup_fonts(self):
        """设置应用程序字体"""
        # 主字体 - 使用微软雅黑，提高中文显示效果
        self.main_font = QFont("Microsoft YaHei UI", 10)
        self.main_font.setHintingPreference(QFont.PreferFullHinting)

        # 标题字体
        self.title_font = QFont("Microsoft YaHei UI", 18, QFont.Bold)
        self.title_font.setHintingPreference(QFont.PreferFullHinting)

        # 时间显示字体 - 使用等宽字体
        self.time_font = QFont("Consolas", 16, QFont.Bold)
        if not self.time_font.exactMatch():
            self.time_font = QFont("Courier New", 16, QFont.Bold)
        self.time_font.setHintingPreference(QFont.PreferFullHinting)

        # 按钮字体
        self.button_font = QFont("Microsoft YaHei UI", 10, QFont.Medium)
        self.button_font.setHintingPreference(QFont.PreferFullHinting)

        # 日志字体 - 等宽字体
        self.log_font = QFont("Consolas", 9)
        if not self.log_font.exactMatch():
            self.log_font = QFont("Courier New", 9)
        self.log_font.setHintingPreference(QFont.PreferFullHinting)

        # 设置应用程序默认字体
        QApplication.instance().setFont(self.main_font)

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("Windows 系统时间修改工具")
        self.setFixedSize(600, 1000)

        # 设置窗口图标
        import os
        icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 设置应用程序字体
        self.setup_fonts()
        self.setStyleSheet(self.get_stylesheet())

        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)

        # 标题
        title_label = QLabel("系统时间修改工具")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(self.title_font)
        title_label.setStyleSheet("color: #2c3e50; margin: 12px 0px;")
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
        time_group.setFont(self.main_font)
        time_layout = QVBoxLayout(time_group)
        time_layout.setContentsMargins(16, 20, 16, 16)

        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setFont(self.time_font)
        self.time_label.setStyleSheet("""
            QLabel {
                color: #27ae60;
                background-color: #f8f9fa;
                padding: 18px;
                border-radius: 8px;
                border: 2px solid #e9ecef;
                letter-spacing: 1px;
            }
        """)
        time_layout.addWidget(self.time_label)

        layout.addWidget(time_group)
        
    def create_quick_adjust_buttons(self, layout):
        """创建快速调整按钮"""
        adjust_group = QGroupBox("快速时间调整")
        adjust_group.setFont(self.main_font)
        adjust_layout = QGridLayout(adjust_group)
        adjust_layout.setContentsMargins(16, 20, 16, 16)
        adjust_layout.setSpacing(12)

        # 按钮配置：(文本, 天数, 行, 列)
        buttons_config = [
            ("过去 7 天", -7, 0, 0),
            ("过去 3 天", -3, 0, 1),
            ("未来 3 天", 3, 1, 0),
            ("未来 7 天", 7, 1, 1),
        ]

        for text, days, row, col in buttons_config:
            btn = QPushButton(text)
            btn.setFont(self.button_font)
            btn.setMinimumHeight(44)
            btn.setMinimumWidth(120)
            btn.setStyleSheet(self.get_button_style())
            btn.clicked.connect(lambda checked=False, d=days: self.adjust_time(d))
            adjust_layout.addWidget(btn, row, col)

        layout.addWidget(adjust_group)
        
    def create_ntp_sync_button(self, layout):
        """创建阿里云时间同步按钮"""
        ntp_group = QGroupBox("阿里云时间同步")
        ntp_group.setFont(self.main_font)
        ntp_layout = QVBoxLayout(ntp_group)
        ntp_layout.setContentsMargins(16, 20, 16, 16)
        ntp_layout.setSpacing(12)

        self.ntp_button = QPushButton("同步阿里云时间服务器")
        self.ntp_button.setFont(self.button_font)
        self.ntp_button.setMinimumHeight(44)
        self.ntp_button.setStyleSheet(self.get_button_style("#3498db"))
        self.ntp_button.clicked.connect(self.sync_ntp_time)
        ntp_layout.addWidget(self.ntp_button)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        ntp_layout.addWidget(self.progress_bar)

        layout.addWidget(ntp_group)
        
    def create_undo_button(self, layout):
        """创建撤销按钮"""
        undo_group = QGroupBox("撤销操作")
        undo_group.setFont(self.main_font)
        undo_layout = QVBoxLayout(undo_group)
        undo_layout.setContentsMargins(16, 20, 16, 16)

        self.undo_button = QPushButton("撤销上次时间更改")
        self.undo_button.setFont(self.button_font)
        self.undo_button.setMinimumHeight(44)
        self.undo_button.setStyleSheet(self.get_button_style("#e74c3c"))
        self.undo_button.clicked.connect(self.undo_last_change)
        self.undo_button.setEnabled(False)
        undo_layout.addWidget(self.undo_button)

        layout.addWidget(undo_group)
        
    def create_log_display(self, layout):
        """创建日志显示区域"""
        log_group = QGroupBox("操作日志")
        log_group.setFont(self.main_font)
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(16, 20, 16, 16)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(130)
        self.log_text.setMinimumHeight(130)
        self.log_text.setReadOnly(True)
        self.log_text.setFont(self.log_font)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 2px solid #34495e;
                border-radius: 6px;
                padding: 8px;
                selection-background-color: #3498db;
            }
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
        """同步阿里云时间服务器"""
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
                self.statusBar().showMessage("正在配置阿里云时间服务器并同步...")

                # 记录操作开始
                self.log_message("开始配置阿里云 NTP 服务器并同步时间...")

                # 启动时间同步线程
                self.ntp_thread = NTPSyncThread()
                self.ntp_thread.finished.connect(
                    lambda success, message: self.on_ntp_sync_finished(success, message, current_time)
                )
                self.ntp_thread.start()

                return True
            return False

        # 安全执行时间同步
        safe_execute(_perform_ntp_sync, self.error_handler)
            
    def on_ntp_sync_finished(self, success, message, old_time=None):
        """阿里云时间同步完成回调"""
        self.ntp_button.setEnabled(True)
        self.progress_bar.setVisible(False)

        # 记录操作历史
        if old_time:
            new_time = self.time_manager.get_local_time() if success else None
            self.operation_history.add_operation(
                "阿里云时间同步",
                "配置阿里云NTP服务器并同步时间",
                old_time,
                new_time
            )

        self.log_message(f"阿里云时间同步: {message}")

        if success:
            self.statusBar().showMessage("阿里云时间同步成功", 3000)
            self.error_handler.show_info_dialog("同步成功", message)
        else:
            self.statusBar().showMessage("阿里云时间同步失败", 3000)
            self.error_handler.handle_error("阿里云时间同步失败", message)
            
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
                font-weight: 600;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 10px 0 10px;
                background-color: #f8f9fa;
                color: #495057;
            }
            QStatusBar {
                background-color: #e9ecef;
                border-top: 1px solid #dee2e6;
                color: #495057;
            }
        """
        
    def get_button_style(self, color="#2ecc71"):
        """获取按钮样式"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 12px 16px;
                border-radius: 8px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
                transform: translateY(-1px);
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(color, 0.8)};
                transform: translateY(0px);
            }}
            QPushButton:disabled {{
                background-color: #adb5bd;
                color: #6c757d;
            }}
        """
        
    def darken_color(self, color, factor=0.9):
        """使颜色变暗"""
        # 简单的颜色变暗实现
        color_map = {
            "#2ecc71": "#27ae60" if factor > 0.85 else "#1e8449",
            "#3498db": "#2980b9" if factor > 0.85 else "#1f618d",
            "#e74c3c": "#c0392b" if factor > 0.85 else "#922b21"
        }
        return color_map.get(color, "#2c3e50")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("Time Jumping")
    app.setApplicationVersion("2.0.203")
    
    # 设置应用程序图标（如果有的话）
    import os
    icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = TimeToolMainWindow()
    window.show()
    
    sys.exit(app.exec_())
