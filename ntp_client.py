"""
NTP 客户端模块
提供从网络时间服务器获取准确时间的功能
"""

import socket
import struct
import time
import datetime
from typing import Optional, Tuple, List


class NTPClient:
    """NTP 客户端，用于从时间服务器获取准确时间"""
    
    # 常用的 NTP 服务器列表
    DEFAULT_SERVERS = [
        'time.windows.com',
        'pool.ntp.org',
        'time.nist.gov',
        'time.google.com',
        'ntp.aliyun.com',
        'cn.pool.ntp.org'
    ]
    
    def __init__(self, timeout: float = 5.0):
        """
        初始化 NTP 客户端
        
        Args:
            timeout: 网络请求超时时间（秒）
        """
        self.timeout = timeout
        
    def _create_ntp_packet(self) -> bytes:
        """创建 NTP 请求数据包"""
        # NTP 数据包格式：48 字节
        # 第一个字节：版本号(3位) + 模式(3位) + LI(2位)
        # 版本号 = 3, 模式 = 3 (客户端), LI = 0
        packet = bytearray(48)
        packet[0] = 0x1B  # 00011011: LI=0, VN=3, Mode=3
        return bytes(packet)
    
    def _parse_ntp_response(self, data: bytes) -> datetime.datetime:
        """
        解析 NTP 响应数据包
        
        Args:
            data: NTP 响应数据
            
        Returns:
            解析出的时间
        """
        if len(data) < 48:
            raise ValueError("NTP 响应数据包长度不足")
        
        # 提取传输时间戳（字节 40-47）
        transmit_timestamp = struct.unpack('!Q', data[40:48])[0]
        
        # NTP 时间戳是从 1900-01-01 00:00:00 UTC 开始的秒数
        # Unix 时间戳是从 1970-01-01 00:00:00 UTC 开始的秒数
        # 两者相差 70 年 = 2208988800 秒
        ntp_epoch_offset = 2208988800
        
        # 转换为 Unix 时间戳
        unix_timestamp = (transmit_timestamp >> 32) - ntp_epoch_offset
        
        # 转换为 datetime 对象
        return datetime.datetime.fromtimestamp(unix_timestamp, tz=datetime.timezone.utc)
    
    def get_time_from_server(self, server: str) -> Tuple[bool, Optional[datetime.datetime], str]:
        """
        从指定的 NTP 服务器获取时间
        
        Args:
            server: NTP 服务器地址
            
        Returns:
            (成功标志, 时间对象, 错误消息)
        """
        try:
            # 创建 UDP 套接字
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            
            # 创建并发送 NTP 请求
            packet = self._create_ntp_packet()
            sock.sendto(packet, (server, 123))
            
            # 接收响应
            response, _ = sock.recvfrom(48)
            sock.close()
            
            # 解析响应
            ntp_time = self._parse_ntp_response(response)
            
            return True, ntp_time, f"成功从 {server} 获取时间"
            
        except socket.timeout:
            return False, None, f"连接 {server} 超时"
        except socket.gaierror:
            return False, None, f"无法解析服务器地址 {server}"
        except Exception as e:
            return False, None, f"从 {server} 获取时间失败: {str(e)}"
    
    def get_accurate_time(self, servers: Optional[List[str]] = None) -> Tuple[bool, Optional[datetime.datetime], str]:
        """
        从多个 NTP 服务器获取准确时间
        
        Args:
            servers: NTP 服务器列表，如果为 None 则使用默认服务器
            
        Returns:
            (成功标志, 时间对象, 状态消息)
        """
        if servers is None:
            servers = self.DEFAULT_SERVERS
        
        successful_times = []
        error_messages = []
        
        for server in servers:
            success, ntp_time, message = self.get_time_from_server(server)
            if success and ntp_time:
                successful_times.append((server, ntp_time))
            else:
                error_messages.append(message)
        
        if not successful_times:
            return False, None, "所有 NTP 服务器都无法访问: " + "; ".join(error_messages)
        
        # 如果有多个成功的时间，选择第一个（通常是最快响应的）
        server, accurate_time = successful_times[0]
        
        # 转换为本地时间
        local_time = accurate_time.replace(tzinfo=None) + datetime.timedelta(
            seconds=time.timezone if time.daylight == 0 else time.altzone
        )
        
        return True, local_time, f"成功从 {server} 获取准确时间（共尝试 {len(successful_times)} 个服务器）"
    
    def sync_system_time(self, time_manager) -> Tuple[bool, str]:
        """
        同步系统时间到 NTP 时间
        
        Args:
            time_manager: TimeManager 实例
            
        Returns:
            (成功标志, 状态消息)
        """
        # 获取准确时间
        success, accurate_time, message = self.get_accurate_time()
        
        if not success or not accurate_time:
            return False, f"获取 NTP 时间失败: {message}"
        
        # 设置系统时间
        success, set_message = time_manager.set_system_time(accurate_time)
        
        if success:
            return True, f"NTP 时间同步成功: {message}"
        else:
            return False, f"NTP 时间同步失败: {set_message}"


def test_ntp_client():
    """测试 NTP 客户端功能"""
    client = NTPClient()
    
    print("测试 NTP 客户端...")
    print(f"当前本地时间: {datetime.datetime.now()}")
    
    # 测试单个服务器
    print("\n测试单个服务器:")
    for server in client.DEFAULT_SERVERS[:3]:  # 测试前3个服务器
        success, ntp_time, message = client.get_time_from_server(server)
        print(f"{server}: {success}, {ntp_time}, {message}")
    
    # 测试获取准确时间
    print("\n测试获取准确时间:")
    success, accurate_time, message = client.get_accurate_time()
    print(f"结果: {success}")
    print(f"时间: {accurate_time}")
    print(f"消息: {message}")
    
    if success and accurate_time:
        current_time = datetime.datetime.now()
        time_diff = abs((accurate_time - current_time).total_seconds())
        print(f"与本地时间差异: {time_diff:.2f} 秒")


if __name__ == "__main__":
    test_ntp_client()
