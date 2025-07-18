"""
Windows 时间服务测试脚本
用于测试和修复 Windows 时间服务问题
"""

import subprocess
import sys
from ntp_client import WindowsTimeSync


def run_command(command):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)


def check_admin():
    """检查管理员权限"""
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except:
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("Windows 时间服务诊断和修复工具")
    print("=" * 60)
    
    # 检查权限
    is_admin = check_admin()
    print(f"管理员权限: {'✓' if is_admin else '✗'}")
    
    if not is_admin:
        print("\n⚠️  需要管理员权限才能执行诊断和修复操作")
        print("请以管理员身份运行此脚本")
        input("按回车键退出...")
        return
    
    sync_client = WindowsTimeSync()
    
    print("\n" + "-" * 40)
    print("1. 检查 Windows 时间服务状态")

    # 检查服务状态
    is_running, status_msg, start_type = sync_client.check_time_service_status()
    print(f"服务状态: {status_msg}")
    print(f"启动类型: {start_type}")

    if not is_running:
        print("\n时间服务未运行，尝试修复...")

        # 如果服务被禁用，先提示
        if start_type == "已禁用":
            print("⚠️  检测到时间服务被禁用，将自动启用...")

        # 尝试启动服务（包含自动启用功能）
        success, start_msg = sync_client.start_time_service()
        if success:
            print(f"✓ {start_msg}")
        else:
            print(f"✗ {start_msg}")

            # 如果启动失败，尝试更多修复步骤
            print("\n尝试高级修复步骤...")

            # 步骤1: 手动启用服务
            if start_type == "已禁用":
                print("1. 手动启用时间服务...")
                success, output, error = run_command("sc config w32time start= auto")
                if success:
                    print("✓ 时间服务已启用")
                else:
                    print(f"✗ 启用失败: {error or output}")

            # 步骤2: 重新注册时间服务
            print("2. 重新注册时间服务...")
            success, output, error = run_command("w32tm /register")
            if success:
                print("✓ 时间服务重新注册成功")
            else:
                print(f"✗ 重新注册失败: {error or output}")

            # 步骤3: 再次启用服务（如果之前被禁用）
            if start_type == "已禁用":
                print("3. 再次启用服务...")
                success, output, error = run_command("sc config w32time start= auto")
                if success:
                    print("✓ 服务重新启用成功")
                else:
                    print(f"✗ 重新启用失败: {error or output}")

            # 步骤4: 尝试启动服务
            print("4. 再次尝试启动服务...")
            success, output, error = run_command("net start w32time")
            if success:
                print("✓ 时间服务启动成功")
            else:
                print(f"✗ 启动失败: {error or output}")

                # 步骤5: 检查服务依赖
                print("5. 检查服务依赖...")
                success, output, error = run_command("sc qc w32time")
                if success:
                    print("服务配置信息:")
                    print(output)
                else:
                    print(f"✗ 获取服务配置失败: {error or output}")
    
    print("\n" + "-" * 40)
    print("2. 测试时间同步功能")
    
    # 再次检查服务状态
    is_running, status_msg, start_type = sync_client.check_time_service_status()
    if is_running:
        print("✓ 时间服务正在运行，测试同步功能...")
        
        # 测试获取状态
        success, status = sync_client.get_sync_status()
        if success:
            print("✓ 成功获取同步状态:")
            print(status[:200] + "..." if len(status) > 200 else status)
        else:
            print(f"✗ 获取同步状态失败: {status}")
        
        # 测试配置NTP服务器
        print("\n测试配置阿里云NTP服务器...")
        success, message = sync_client.configure_ntp_server()
        if success:
            print(f"✓ 配置成功: {message}")
            
            # 测试立即同步
            print("\n测试立即同步...")
            success, sync_msg = sync_client.sync_time_immediately()
            if success:
                print(f"✓ 同步成功: {sync_msg}")
            else:
                print(f"✗ 同步失败: {sync_msg}")
        else:
            print(f"✗ 配置失败: {message}")
    else:
        print("✗ 时间服务仍未运行，无法测试同步功能")
    
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n诊断被用户中断")
    except Exception as e:
        print(f"\n诊断过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按回车键退出...")
