"""
错误处理和权限管理模块
提供统一的错误处理、日志记录和权限管理功能
"""

import sys
import os
import traceback
import logging
import datetime
from typing import Optional, Callable, Any
from PyQt5.QtWidgets import QMessageBox, QWidget
from PyQt5.QtCore import QObject, pyqtSignal


class Logger:
    """日志管理器"""
    
    def __init__(self, log_file: str = "time_tool.log"):
        """
        初始化日志管理器
        
        Args:
            log_file: 日志文件路径
        """
        self.log_file = log_file
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志配置"""
        # 创建日志目录
        log_dir = os.path.dirname(self.log_file) if os.path.dirname(self.log_file) else "."
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 配置日志格式
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        
    def info(self, message: str):
        """记录信息日志"""
        self.logger.info(message)
        
    def warning(self, message: str):
        """记录警告日志"""
        self.logger.warning(message)
        
    def error(self, message: str):
        """记录错误日志"""
        self.logger.error(message)
        
    def exception(self, message: str):
        """记录异常日志"""
        self.logger.exception(message)


class ErrorHandler(QObject):
    """错误处理器"""
    
    error_occurred = pyqtSignal(str, str)  # 错误类型, 错误消息
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parent_widget = parent
        self.logger = Logger()
        
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """处理未捕获的异常"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        self.logger.exception(f"未捕获的异常: {error_msg}")
        
        # 发送错误信号
        self.error_occurred.emit("未捕获异常", str(exc_value))
        
        # 显示错误对话框
        self.show_error_dialog("程序异常", f"程序遇到未处理的异常：\n{str(exc_value)}")
        
    def handle_error(self, error_type: str, error_message: str, show_dialog: bool = True):
        """处理一般错误"""
        self.logger.error(f"{error_type}: {error_message}")
        
        if show_dialog:
            self.show_error_dialog(error_type, error_message)
            
        self.error_occurred.emit(error_type, error_message)
        
    def handle_warning(self, warning_type: str, warning_message: str, show_dialog: bool = True):
        """处理警告"""
        self.logger.warning(f"{warning_type}: {warning_message}")
        
        if show_dialog:
            self.show_warning_dialog(warning_type, warning_message)
            
    def show_error_dialog(self, title: str, message: str):
        """显示错误对话框"""
        if self.parent_widget:
            QMessageBox.critical(self.parent_widget, title, message)
        else:
            print(f"错误 - {title}: {message}")
            
    def show_warning_dialog(self, title: str, message: str):
        """显示警告对话框"""
        if self.parent_widget:
            QMessageBox.warning(self.parent_widget, title, message)
        else:
            print(f"警告 - {title}: {message}")
            
    def show_info_dialog(self, title: str, message: str):
        """显示信息对话框"""
        if self.parent_widget:
            QMessageBox.information(self.parent_widget, title, message)
        else:
            print(f"信息 - {title}: {message}")


def safe_execute(func: Callable, error_handler: ErrorHandler, *args, **kwargs) -> Any:
    """
    安全执行函数，捕获并处理异常
    
    Args:
        func: 要执行的函数
        error_handler: 错误处理器
        *args: 函数参数
        **kwargs: 函数关键字参数
        
    Returns:
        函数执行结果，如果出错则返回 None
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler.handle_error("函数执行错误", f"执行 {func.__name__} 时发生错误: {str(e)}")
        return None


class ConfirmationDialog:
    """确认对话框工具类"""
    
    @staticmethod
    def confirm_action(parent: QWidget, title: str, message: str, 
                      details: Optional[str] = None) -> bool:
        """
        显示确认对话框
        
        Args:
            parent: 父窗口
            title: 对话框标题
            message: 主要消息
            details: 详细信息
            
        Returns:
            用户是否确认
        """
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        if details:
            msg_box.setDetailedText(details)
            
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        
        return msg_box.exec_() == QMessageBox.Yes
    
    @staticmethod
    def confirm_time_change(parent: QWidget, current_time: str, new_time: str, 
                           operation: str) -> bool:
        """
        确认时间更改操作
        
        Args:
            parent: 父窗口
            current_time: 当前时间
            new_time: 新时间
            operation: 操作描述
            
        Returns:
            用户是否确认
        """
        message = f"确定要{operation}吗？"
        details = f"当前时间: {current_time}\n新时间: {new_time}\n\n注意：此操作将修改系统时间，可能影响其他程序和系统功能。"
        
        return ConfirmationDialog.confirm_action(
            parent, 
            "确认时间更改", 
            message, 
            details
        )
    
    @staticmethod
    def confirm_ntp_sync(parent: QWidget) -> bool:
        """
        确认阿里云时间同步操作

        Args:
            parent: 父窗口

        Returns:
            用户是否确认
        """
        message = "确定要配置阿里云时间服务器并同步时间吗？"
        details = (
            "此操作将：\n"
            "1. 配置Windows时间服务使用阿里云NTP服务器\n"
            "2. 重启Windows时间服务\n"
            "3. 立即同步系统时间到阿里云时间服务器\n"
            "4. 整个过程可能需要10-30秒时间完成\n\n"
            "这将确保您的系统时间与阿里云标准时间保持同步。"
        )

        return ConfirmationDialog.confirm_action(
            parent,
            "确认阿里云时间同步",
            message,
            details
        )


class OperationHistory:
    """操作历史记录"""
    
    def __init__(self, max_history: int = 10):
        """
        初始化操作历史
        
        Args:
            max_history: 最大历史记录数量
        """
        self.max_history = max_history
        self.history = []
        
    def add_operation(self, operation_type: str, description: str, 
                     old_value: Any = None, new_value: Any = None):
        """
        添加操作记录
        
        Args:
            operation_type: 操作类型
            description: 操作描述
            old_value: 旧值
            new_value: 新值
        """
        record = {
            'timestamp': datetime.datetime.now(),
            'type': operation_type,
            'description': description,
            'old_value': old_value,
            'new_value': new_value
        }
        
        self.history.append(record)
        
        # 保持历史记录数量限制
        if len(self.history) > self.max_history:
            self.history.pop(0)
            
    def get_last_operation(self) -> Optional[dict]:
        """获取最后一次操作"""
        return self.history[-1] if self.history else None
    
    def get_history(self) -> list:
        """获取所有历史记录"""
        return self.history.copy()
    
    def clear_history(self):
        """清空历史记录"""
        self.history.clear()


# 全局错误处理器实例
global_error_handler = None


def setup_global_error_handler(parent_widget: Optional[QWidget] = None):
    """设置全局错误处理器"""
    global global_error_handler
    global_error_handler = ErrorHandler(parent_widget)
    
    # 设置全局异常处理
    sys.excepthook = global_error_handler.handle_exception
    
    return global_error_handler


def get_global_error_handler() -> Optional[ErrorHandler]:
    """获取全局错误处理器"""
    return global_error_handler
