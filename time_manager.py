"""
Windows 系统时间管理模块
提供系统时间的读取、修改和权限管理功能
"""

import ctypes
import ctypes.wintypes
import datetime
import sys
import os
from typing import Optional, Tuple


class SYSTEMTIME(ctypes.Structure):
    """Windows SYSTEMTIME 结构体"""
    _fields_ = [
        ('wYear', ctypes.wintypes.WORD),
        ('wMonth', ctypes.wintypes.WORD),
        ('wDayOfWeek', ctypes.wintypes.WORD),
        ('wDay', ctypes.wintypes.WORD),
        ('wHour', ctypes.wintypes.WORD),
        ('wMinute', ctypes.wintypes.WORD),
        ('wSecond', ctypes.wintypes.WORD),
        ('wMilliseconds', ctypes.wintypes.WORD),
    ]


class TimeManager:
    """Windows 系统时间管理器"""
    
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self.advapi32 = ctypes.windll.advapi32
        self._last_time = None  # 用于撤销功能
        
    def is_admin(self) -> bool:
        """检查当前进程是否具有管理员权限"""
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except:
            return False
    
    def request_admin_privileges(self) -> bool:
        """请求管理员权限"""
        if self.is_admin():
            return True
        
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
            return False  # 当前进程将退出
        except Exception as e:
            return False
    
    def get_system_time(self) -> datetime.datetime:
        """获取当前系统时间"""
        st = SYSTEMTIME()
        self.kernel32.GetSystemTime(ctypes.byref(st))
        
        return datetime.datetime(
            st.wYear, st.wMonth, st.wDay,
            st.wHour, st.wMinute, st.wSecond,
            st.wMilliseconds * 1000
        )
    
    def get_local_time(self) -> datetime.datetime:
        """获取当前本地时间"""
        st = SYSTEMTIME()
        self.kernel32.GetLocalTime(ctypes.byref(st))
        
        return datetime.datetime(
            st.wYear, st.wMonth, st.wDay,
            st.wHour, st.wMinute, st.wSecond,
            st.wMilliseconds * 1000
        )
    
    def set_system_time(self, new_time: datetime.datetime) -> Tuple[bool, str]:
        """
        设置系统时间
        
        Args:
            new_time: 要设置的新时间
            
        Returns:
            (成功标志, 错误消息)
        """
        if not self.is_admin():
            return False, "需要管理员权限才能修改系统时间"
        
        # 保存当前时间用于撤销
        self._last_time = self.get_local_time()
        
        # 转换为 UTC 时间
        utc_time = new_time.utctimetuple()
        
        st = SYSTEMTIME()
        st.wYear = utc_time.tm_year
        st.wMonth = utc_time.tm_mon
        st.wDay = utc_time.tm_mday
        st.wHour = utc_time.tm_hour
        st.wMinute = utc_time.tm_min
        st.wSecond = utc_time.tm_sec
        st.wMilliseconds = 0
        
        try:
            result = self.kernel32.SetSystemTime(ctypes.byref(st))
            if result:
                return True, "系统时间修改成功"
            else:
                error_code = ctypes.windll.kernel32.GetLastError()
                return False, f"系统时间修改失败，错误代码: {error_code}"
        except Exception as e:
            return False, f"系统时间修改异常: {str(e)}"
    
    def adjust_time(self, days: int = 0, hours: int = 0, minutes: int = 0) -> Tuple[bool, str]:
        """
        调整系统时间
        
        Args:
            days: 调整的天数
            hours: 调整的小时数
            minutes: 调整的分钟数
            
        Returns:
            (成功标志, 错误消息)
        """
        current_time = self.get_local_time()
        delta = datetime.timedelta(days=days, hours=hours, minutes=minutes)
        new_time = current_time + delta
        
        return self.set_system_time(new_time)
    
    def can_undo(self) -> bool:
        """检查是否可以撤销上次的时间更改"""
        return self._last_time is not None
    
    def undo_last_change(self) -> Tuple[bool, str]:
        """撤销上次的时间更改"""
        if not self.can_undo():
            return False, "没有可撤销的时间更改"
        
        last_time = self._last_time
        self._last_time = None  # 清除撤销记录
        
        return self.set_system_time(last_time)



