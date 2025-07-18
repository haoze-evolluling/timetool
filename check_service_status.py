"""
检查 Windows 时间服务状态（无需管理员权限）
"""

import subprocess
from ntp_client import WindowsTimeSync


def main():
    """检查服务状态"""
    print("=" * 50)
    print("Windows 时间服务状态检查")
    print("=" * 50)
    
    sync_client = WindowsTimeSync()
    
    # 检查服务状态
    print("正在检查 Windows 时间服务状态...")
    is_running, status_msg, start_type = sync_client.check_time_service_status()
    
    print(f"\n服务运行状态: {status_msg}")
    print(f"服务启动类型: {start_type}")
    
    # 根据状态给出建议
    if is_running:
        print("\n✅ 时间服务正常运行")
        print("可以尝试使用时间同步功能")
    else:
        print(f"\n❌ 时间服务未运行")
        if start_type == "已禁用":
            print("🔧 解决方案:")
            print("1. 以管理员身份运行应用程序")
            print("2. 应用程序会自动启用并启动时间服务")
            print("3. 或者手动执行以下命令（需要管理员权限）:")
            print("   sc config w32time start= auto")
            print("   net start w32time")
        else:
            print("🔧 解决方案:")
            print("1. 以管理员身份运行应用程序")
            print("2. 应用程序会自动启动时间服务")
            print("3. 或者手动执行以下命令（需要管理员权限）:")
            print("   net start w32time")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"检查过程中发生错误: {e}")
    
    input("按回车键退出...")
