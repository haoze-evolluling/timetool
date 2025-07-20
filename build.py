#!/usr/bin/env python3
"""
构建脚本
用于打包 Windows 系统时间修改工具为独立可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def check_dependencies():
    """检查构建依赖"""
    try:
        import PyInstaller
    except ImportError:
        print("✗ PyInstaller 未安装")
        print("请运行: pip install pyinstaller")
        return False

    try:
        import PyQt5
    except ImportError:
        print("✗ PyQt5 未安装")
        print("请运行: pip install PyQt5")
        return False

    return True


def clean_build_dirs():
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist', '__pycache__']

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)

    # 清理 .spec 文件
    for spec_file in Path('.').glob('*.spec'):
        spec_file.unlink()


def create_icon():
    """创建应用程序图标（如果不存在）"""
    icon_path = "icon.ico"

    if not os.path.exists(icon_path):
        return None

    return icon_path


def build_executable():
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    # 构建参数
    build_args = [
        'pyinstaller',
        '--onefile',           # 打包为单个文件
        '--windowed',          # Windows 应用程序（无控制台窗口）
        '--name=TimeToolGUI',  # 可执行文件名称
        '--clean',             # 清理临时文件
        '--noconfirm',         # 不询问确认
    ]
    
    # 添加图标
    icon_path = create_icon()
    if icon_path:
        build_args.extend(['--icon', icon_path])
    
    # 添加隐藏导入（解决一些 PyQt5 模块可能的导入问题）
    hidden_imports = [
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'win32api',
        'win32con',
        'win32security',
        'ntplib'
    ]
    
    for module in hidden_imports:
        build_args.extend(['--hidden-import', module])
    
    # 添加数据文件（如果有）
    # build_args.extend(['--add-data', 'config.ini;.'])
    
    # 主程序文件
    build_args.append('main.py')
    
    try:
        # 执行构建
        result = subprocess.run(build_args, check=True, capture_output=True, text=True)
        print("✓ 构建成功！")
        return True
        
    except subprocess.CalledProcessError as e:
        print("✗ 构建失败！")
        print(f"错误代码: {e.returncode}")
        print(f"错误输出: {e.stderr}")
        return False


def create_installer_script():
    """创建安装脚本"""
    installer_script = """@echo off
echo Windows 系统时间修改工具 - 安装脚本
echo =====================================

set INSTALL_DIR=%PROGRAMFILES%\\TimeToolGUI
set DESKTOP_LINK=%USERPROFILE%\\Desktop\\时间修改工具.lnk

echo 正在安装到: %INSTALL_DIR%

:: 创建安装目录
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

:: 复制文件
copy "TimeToolGUI.exe" "%INSTALL_DIR%\\" >nul
if errorlevel 1 (
    echo 错误: 无法复制文件到安装目录
    echo 请确保以管理员身份运行此脚本
    pause
    exit /b 1
)

:: 创建桌面快捷方式
echo 正在创建桌面快捷方式...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP_LINK%'); $Shortcut.TargetPath = '%INSTALL_DIR%\\TimeToolGUI.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'Windows 系统时间修改工具'; $Shortcut.Save()"

echo.
echo 安装完成！
echo 可执行文件位置: %INSTALL_DIR%\\TimeToolGUI.exe
echo 桌面快捷方式: %DESKTOP_LINK%
echo.
echo 注意: 运行程序时需要管理员权限
pause
"""
    
    with open('install.bat', 'w', encoding='gbk') as f:
        f.write(installer_script)


def create_uninstaller_script():
    """创建卸载脚本"""
    uninstaller_script = """@echo off
echo Windows 系统时间修改工具 - 卸载脚本
echo =====================================

set INSTALL_DIR=%PROGRAMFILES%\\TimeToolGUI
set DESKTOP_LINK=%USERPROFILE%\\Desktop\\时间修改工具.lnk

echo 正在卸载...

:: 删除桌面快捷方式
if exist "%DESKTOP_LINK%" (
    del "%DESKTOP_LINK%"
    echo 已删除桌面快捷方式
)

:: 删除安装目录
if exist "%INSTALL_DIR%" (
    rmdir /s /q "%INSTALL_DIR%"
    echo 已删除安装目录
)

echo.
echo 卸载完成！
pause
"""
    
    with open('uninstall.bat', 'w', encoding='gbk') as f:
        f.write(uninstaller_script)


def post_build_tasks():
    """构建后任务"""
    # 检查生成的文件
    exe_path = os.path.join('dist', 'TimeToolGUI.exe')
    if os.path.exists(exe_path):
        # 创建安装和卸载脚本
        create_installer_script()
        create_uninstaller_script()

        # 复制到 dist 目录
        shutil.copy('install.bat', 'dist/')
        shutil.copy('uninstall.bat', 'dist/')

        print("✓ 构建完成！")
        return True
    else:
        print("✗ 未找到生成的可执行文件")
        return False


def main():
    """主函数"""
    print("Windows 系统时间修改工具 - 构建脚本")
    print("=" * 50)

    # 检查依赖
    if not check_dependencies():
        return 1

    # 清理构建目录
    clean_build_dirs()

    # 构建可执行文件
    if not build_executable():
        return 1

    # 构建后任务
    if not post_build_tasks():
        return 1

    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        sys.exit(1)
