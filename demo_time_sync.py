"""
阿里云时间同步演示脚本
展示重构后的时间同步功能
"""

import datetime
from ntp_client import WindowsTimeSync


def main():
    """主演示函数"""
    print("=" * 60)
    print("阿里云时间同步演示")
    print("=" * 60)
    
    # 创建时间同步器
    sync_client = WindowsTimeSync()
    
    # 显示当前时间
    print(f"当前本地时间: {datetime.datetime.now()}")
    print(f"管理员权限检查: {sync_client.is_admin()}")
    
    if not sync_client.is_admin():
        print("\n⚠️  警告: 需要管理员权限才能执行时间同步操作")
        print("请以管理员身份运行此脚本以体验完整功能")
        print("\n可用的演示功能:")
        print("1. 权限检查 ✓")
        print("2. 获取同步状态")
        print("3. 配置NTP服务器 (需要管理员权限)")
        print("4. 立即同步时间 (需要管理员权限)")
        print("5. 完整同步流程 (需要管理员权限)")
        
        # 尝试获取同步状态（不需要管理员权限）
        print("\n" + "-" * 40)
        print("尝试获取当前同步状态:")
        success, status = sync_client.get_sync_status()
        if success:
            print("✓ 成功获取同步状态:")
            print(status)
        else:
            print(f"✗ 获取同步状态失败: {status}")
        
        return
    
    print("\n✓ 具有管理员权限，可以执行完整演示")

    # 演示1: 检查时间服务状态
    print("\n" + "-" * 40)
    print("1. 检查 Windows 时间服务状态")
    is_running, status_msg, start_type = sync_client.check_time_service_status()
    print(f"服务状态: {status_msg}")
    print(f"启动类型: {start_type}")

    if not is_running:
        print("尝试启动时间服务...")
        if start_type == "已禁用":
            print("检测到服务被禁用，将自动启用...")
        success, start_msg = sync_client.start_time_service()
        if success:
            print(f"✓ {start_msg}")
        else:
            print(f"✗ {start_msg}")
            print("无法启动时间服务，演示终止")
            return

    # 演示2: 获取当前同步状态
    print("\n" + "-" * 40)
    print("2. 获取当前同步状态")
    success, status = sync_client.get_sync_status()
    if success:
        print("✓ 当前同步状态:")
        print(status)
    else:
        print(f"✗ 获取状态失败: {status}")
    
    # 演示3: 显示阿里云NTP服务器列表
    print("\n" + "-" * 40)
    print("3. 阿里云NTP服务器列表")
    for i, server in enumerate(sync_client.ALIYUN_NTP_SERVERS, 1):
        print(f"   {i}. {server}")

    # 演示4: 配置阿里云NTP服务器
    print("\n" + "-" * 40)
    print("4. 配置阿里云NTP服务器")
    print("正在配置前3个阿里云NTP服务器...")

    success, message = sync_client.configure_ntp_server()
    if success:
        print(f"✓ 配置成功: {message}")
    else:
        print(f"✗ 配置失败: {message}")
        return

    # 等待服务重启
    print("等待Windows时间服务重启...")
    import time
    time.sleep(3)

    # 演示5: 立即同步时间
    print("\n" + "-" * 40)
    print("5. 立即同步时间")
    print("正在执行立即同步...")

    success, message = sync_client.sync_time_immediately()
    if success:
        print(f"✓ 同步成功: {message}")
    else:
        print(f"✗ 同步失败: {message}")

    # 演示6: 获取同步后状态
    print("\n" + "-" * 40)
    print("6. 获取同步后状态")
    success, status = sync_client.get_sync_status()
    if success:
        print("✓ 同步后状态:")
        print(status)
    else:
        print(f"✗ 获取状态失败: {status}")

    # 演示7: 完整同步流程
    print("\n" + "-" * 40)
    print("7. 完整同步流程演示")
    print("正在执行完整的配置和同步流程...")

    success, message = sync_client.sync_system_time()
    if success:
        print(f"✓ 完整同步成功: {message}")
    else:
        print(f"✗ 完整同步失败: {message}")
    
    print("\n" + "=" * 60)
    print("演示完成!")
    print(f"最终本地时间: {datetime.datetime.now()}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n演示被用户中断")
    except Exception as e:
        print(f"\n演示过程中发生错误: {e}")
    
    input("\n按回车键退出...")
