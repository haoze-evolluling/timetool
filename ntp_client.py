"""
Windows 时间同步模块
使用 Windows w32tm 命令配置阿里云 NTP 服务器并立即同步时间
"""

import subprocess
import datetime
import time
from typing import Tuple, List


class WindowsTimeSync:
    """Windows 时间同步器，使用 w32tm 命令与阿里云 NTP 服务器同步"""

    # 阿里云 NTP 服务器列表
    ALIYUN_NTP_SERVERS = [
        'ntp.aliyun.com',
        'ntp2.aliyun.com',
        'ntp3.aliyun.com'
    ]

    def __init__(self):
        """初始化 Windows 时间同步器"""
        pass

    def is_admin(self) -> bool:
        """检查当前进程是否具有管理员权限"""
        try:
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except:
            return False

    def _run_command(self, command: str) -> Tuple[bool, str]:
        """
        执行 Windows 命令

        Args:
            command: 要执行的命令

        Returns:
            (成功标志, 输出信息)
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, result.stderr.strip() or result.stdout.strip()

        except subprocess.TimeoutExpired:
            return False, "命令执行超时"
        except Exception as e:
            return False, f"命令执行异常: {str(e)}"

    def check_time_service_status(self) -> Tuple[bool, str, str]:
        """
        检查 Windows 时间服务状态

        Returns:
            (服务是否运行, 状态信息, 启动类型)
        """
        # 检查服务运行状态
        check_command = 'sc query w32time'
        success, output = self._run_command(check_command)

        # 检查服务配置（启动类型）
        config_command = 'sc qc w32time'
        config_success, config_output = self._run_command(config_command)

        start_type = "未知"
        if config_success:
            if "DISABLED" in config_output:
                start_type = "已禁用"
            elif "AUTO_START" in config_output:
                start_type = "自动"
            elif "DEMAND_START" in config_output:
                start_type = "手动"

        if success:
            if "RUNNING" in output:
                return True, "Windows 时间服务正在运行", start_type
            elif "STOPPED" in output:
                return False, "Windows 时间服务已停止", start_type
            else:
                return False, f"Windows 时间服务状态未知: {output}", start_type
        else:
            return False, f"无法检查时间服务状态: {output}", start_type

    def enable_time_service(self) -> Tuple[bool, str]:
        """
        启用 Windows 时间服务（设置为自动启动）

        Returns:
            (成功标志, 状态消息)
        """
        # 检查管理员权限
        if not self.is_admin():
            return False, "需要管理员权限才能启用时间服务"

        # 设置服务为自动启动
        enable_command = "sc config w32time start= auto"
        success, output = self._run_command(enable_command)

        if success:
            return True, "Windows 时间服务已设置为自动启动"
        else:
            return False, f"启用时间服务失败: {output}"

    def start_time_service(self) -> Tuple[bool, str]:
        """
        启动 Windows 时间服务

        Returns:
            (成功标志, 状态消息)
        """
        # 检查管理员权限
        if not self.is_admin():
            return False, "需要管理员权限才能启动时间服务"

        # 先检查服务状态和配置
        is_running, status_msg, start_type = self.check_time_service_status()
        if is_running:
            return True, status_msg

        # 如果服务被禁用，先启用它
        if start_type == "已禁用":
            enable_success, enable_msg = self.enable_time_service()
            if not enable_success:
                return False, f"无法启用时间服务: {enable_msg}"

        # 尝试启动服务
        start_command = "net start w32time"
        success, output = self._run_command(start_command)

        if success:
            return True, "Windows 时间服务启动成功"
        elif "服务已经启动" in output or "service is already running" in output.lower():
            return True, "Windows 时间服务已在运行"
        else:
            # 如果启动失败，尝试重新注册时间服务
            register_command = "w32tm /register"
            reg_success, reg_output = self._run_command(register_command)
            if reg_success:
                # 重新注册后可能需要重新启用
                if start_type == "已禁用":
                    self.enable_time_service()

                # 重新注册后再次尝试启动
                success, output = self._run_command(start_command)
                if success:
                    return True, "重新注册并启动 Windows 时间服务成功"

            return False, f"启动时间服务失败: {output}"

    def configure_ntp_server(self, server_list: List[str] = None) -> Tuple[bool, str]:
        """
        配置 Windows NTP 服务器

        Args:
            server_list: NTP 服务器列表，默认使用阿里云服务器

        Returns:
            (成功标志, 状态消息)
        """
        # 检查管理员权限
        if not self.is_admin():
            return False, "需要管理员权限才能配置 NTP 服务器"

        # 确保时间服务正在运行
        success, message = self.start_time_service()
        if not success:
            return False, f"启动时间服务失败: {message}"

        if server_list is None:
            server_list = self.ALIYUN_NTP_SERVERS[:3]  # 使用前3个阿里云服务器

        # 构建服务器列表字符串
        server_string = ",".join(server_list)

        # 配置 NTP 服务器
        config_command = f'w32tm /config /manualpeerlist:"{server_string}" /syncfromflags:manual /reliable:YES /update'

        success, output = self._run_command(config_command)
        if not success:
            return False, f"配置 NTP 服务器失败: {output}"

        # 重启 Windows Time 服务以应用配置
        restart_command = "net stop w32time && net start w32time"
        success, output = self._run_command(restart_command)
        if not success:
            return False, f"重启时间服务失败: {output}"

        return True, f"成功配置 NTP 服务器: {server_string}"

    def sync_time_immediately(self) -> Tuple[bool, str]:
        """
        立即同步时间

        Returns:
            (成功标志, 状态消息)
        """
        # 检查管理员权限
        if not self.is_admin():
            return False, "需要管理员权限才能同步时间"

        # 确保时间服务正在运行
        success, message = self.start_time_service()
        if not success:
            return False, f"启动时间服务失败: {message}"

        # 强制立即同步时间
        sync_command = "w32tm /resync /force"

        success, output = self._run_command(sync_command)
        if not success:
            return False, f"时间同步失败: {output}"

        return True, f"时间同步成功: {output}"

    def get_sync_status(self) -> Tuple[bool, str]:
        """
        获取时间同步状态

        Returns:
            (成功标志, 状态信息)
        """
        status_command = "w32tm /query /status"

        success, output = self._run_command(status_command)
        if not success:
            return False, f"获取同步状态失败: {output}"

        return True, output

    def sync_system_time(self, time_manager=None) -> Tuple[bool, str]:
        """
        同步系统时间到阿里云 NTP 服务器

        Args:
            time_manager: TimeManager 实例（为了兼容性保留，但不使用）

        Returns:
            (成功标志, 状态消息)
        """
        # 步骤1: 配置阿里云 NTP 服务器
        success, config_message = self.configure_ntp_server()
        if not success:
            return False, f"配置 NTP 服务器失败: {config_message}"

        # 等待服务重启
        time.sleep(2)

        # 步骤2: 立即同步时间
        success, sync_message = self.sync_time_immediately()
        if not success:
            return False, f"时间同步失败: {sync_message}"

        return True, f"阿里云 NTP 时间同步成功: {config_message}; {sync_message}"



