#!/usr/bin/env python3
"""
应用程序测试脚本
测试所有核心功能的正确性
"""

import sys
import datetime
import unittest
from unittest.mock import Mock, patch, MagicMock

# 导入要测试的模块
from time_manager import TimeManager, SYSTEMTIME
from ntp_client import NTPClient
from error_handler import ErrorHandler, ConfirmationDialog, OperationHistory


class TestTimeManager(unittest.TestCase):
    """测试时间管理器"""
    
    def setUp(self):
        self.time_manager = TimeManager()
    
    def test_get_local_time(self):
        """测试获取本地时间"""
        local_time = self.time_manager.get_local_time()
        self.assertIsInstance(local_time, datetime.datetime)
        print(f"✓ 本地时间获取成功: {local_time}")
    
    def test_get_system_time(self):
        """测试获取系统时间"""
        system_time = self.time_manager.get_system_time()
        self.assertIsInstance(system_time, datetime.datetime)
        print(f"✓ 系统时间获取成功: {system_time}")
    
    def test_is_admin(self):
        """测试管理员权限检查"""
        is_admin = self.time_manager.is_admin()
        self.assertIsInstance(is_admin, bool)
        print(f"✓ 管理员权限检查: {'是' if is_admin else '否'}")
    
    def test_can_undo(self):
        """测试撤销功能检查"""
        can_undo = self.time_manager.can_undo()
        self.assertIsInstance(can_undo, bool)
        print(f"✓ 撤销功能检查: {'可用' if can_undo else '不可用'}")


class TestNTPClient(unittest.TestCase):
    """测试 NTP 客户端"""
    
    def setUp(self):
        self.ntp_client = NTPClient(timeout=3.0)
    
    def test_create_ntp_packet(self):
        """测试 NTP 数据包创建"""
        packet = self.ntp_client._create_ntp_packet()
        self.assertEqual(len(packet), 48)
        self.assertEqual(packet[0], 0x1B)
        print("✓ NTP 数据包创建成功")
    
    def test_get_time_from_server(self):
        """测试从 NTP 服务器获取时间"""
        # 测试一个可靠的 NTP 服务器
        success, ntp_time, message = self.ntp_client.get_time_from_server('pool.ntp.org')
        
        if success:
            self.assertIsInstance(ntp_time, datetime.datetime)
            print(f"✓ NTP 时间获取成功: {ntp_time}")
        else:
            print(f"⚠ NTP 时间获取失败: {message}")
    
    def test_get_accurate_time(self):
        """测试获取准确时间"""
        success, accurate_time, message = self.ntp_client.get_accurate_time()
        
        if success:
            self.assertIsInstance(accurate_time, datetime.datetime)
            print(f"✓ 准确时间获取成功: {accurate_time}")
            print(f"✓ 消息: {message}")
        else:
            print(f"⚠ 准确时间获取失败: {message}")


class TestErrorHandler(unittest.TestCase):
    """测试错误处理器"""
    
    def setUp(self):
        self.error_handler = ErrorHandler()
    
    def test_handle_error(self):
        """测试错误处理"""
        # 模拟错误处理（不显示对话框）
        self.error_handler.handle_error("测试错误", "这是一个测试错误", show_dialog=False)
        print("✓ 错误处理功能正常")
    
    def test_handle_warning(self):
        """测试警告处理"""
        # 模拟警告处理（不显示对话框）
        self.error_handler.handle_warning("测试警告", "这是一个测试警告", show_dialog=False)
        print("✓ 警告处理功能正常")


class TestOperationHistory(unittest.TestCase):
    """测试操作历史"""
    
    def setUp(self):
        self.history = OperationHistory(max_history=5)
    
    def test_add_operation(self):
        """测试添加操作记录"""
        self.history.add_operation("测试操作", "测试描述", "旧值", "新值")
        self.assertEqual(len(self.history.get_history()), 1)
        print("✓ 操作记录添加成功")
    
    def test_get_last_operation(self):
        """测试获取最后操作"""
        self.history.add_operation("测试操作", "测试描述")
        last_op = self.history.get_last_operation()
        self.assertIsNotNone(last_op)
        self.assertEqual(last_op['type'], "测试操作")
        print("✓ 最后操作获取成功")
    
    def test_max_history_limit(self):
        """测试历史记录数量限制"""
        # 添加超过限制的记录
        for i in range(10):
            self.history.add_operation(f"操作{i}", f"描述{i}")
        
        # 应该只保留最后5条记录
        self.assertEqual(len(self.history.get_history()), 5)
        print("✓ 历史记录数量限制正常")


def test_gui_components():
    """测试 GUI 组件（不启动完整 GUI）"""
    print("\n测试 GUI 组件...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        
        # 创建应用程序实例（但不显示窗口）
        app = QApplication([])
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        
        print("✓ PyQt5 应用程序创建成功")
        
        # 测试主窗口类导入
        from main_window import TimeToolMainWindow
        print("✓ 主窗口类导入成功")
        
        app.quit()
        
    except ImportError as e:
        print(f"✗ GUI 组件测试失败: {e}")
        return False
    except Exception as e:
        print(f"✗ GUI 组件测试异常: {e}")
        return False
    
    return True


def test_dependencies():
    """测试依赖包"""
    print("测试依赖包...")
    
    dependencies = [
        ('PyQt5', 'PyQt5'),
        ('pywin32', 'win32api'),
        ('ntplib', 'ntplib'),
    ]
    
    all_ok = True
    
    for package_name, import_name in dependencies:
        try:
            __import__(import_name)
            print(f"✓ {package_name} 导入成功")
        except ImportError:
            print(f"✗ {package_name} 导入失败")
            all_ok = False
    
    return all_ok


def run_integration_test():
    """运行集成测试"""
    print("\n运行集成测试...")
    
    try:
        # 测试时间管理器和 NTP 客户端的集成
        time_manager = TimeManager()
        ntp_client = NTPClient(timeout=2.0)
        
        print(f"当前时间: {time_manager.get_local_time()}")
        print(f"管理员权限: {'是' if time_manager.is_admin() else '否'}")
        
        # 测试 NTP 时间获取（不修改系统时间）
        success, accurate_time, message = ntp_client.get_accurate_time()
        if success:
            print(f"NTP 时间: {accurate_time}")
            
            # 计算时间差
            local_time = time_manager.get_local_time()
            time_diff = abs((accurate_time - local_time).total_seconds())
            print(f"时间差: {time_diff:.2f} 秒")
        else:
            print(f"NTP 时间获取失败: {message}")
        
        print("✓ 集成测试完成")
        return True
        
    except Exception as e:
        print(f"✗ 集成测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("Windows 系统时间修改工具 - 测试脚本")
    print("=" * 50)
    
    # 测试依赖包
    if not test_dependencies():
        print("\n⚠ 部分依赖包缺失，请运行: pip install -r requirements.txt")
        return 1
    
    # 测试 GUI 组件
    if not test_gui_components():
        print("\n✗ GUI 组件测试失败")
        return 1
    
    # 运行单元测试
    print("\n运行单元测试...")

    # 创建测试加载器
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    # 添加测试用例
    test_suite.addTests(loader.loadTestsFromTestCase(TestTimeManager))
    test_suite.addTests(loader.loadTestsFromTestCase(TestNTPClient))
    test_suite.addTests(loader.loadTestsFromTestCase(TestErrorHandler))
    test_suite.addTests(loader.loadTestsFromTestCase(TestOperationHistory))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(test_suite)
    
    # 运行集成测试
    integration_ok = run_integration_test()
    
    # 总结测试结果
    print("\n" + "=" * 50)
    print("测试结果总结:")
    print(f"单元测试: {result.testsRun} 个测试，{len(result.failures)} 个失败，{len(result.errors)} 个错误")
    print(f"集成测试: {'通过' if integration_ok else '失败'}")
    
    if result.wasSuccessful() and integration_ok:
        print("✓ 所有测试通过！应用程序可以正常运行。")
        return 0
    else:
        print("✗ 部分测试失败，请检查相关功能。")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        sys.exit(1)
