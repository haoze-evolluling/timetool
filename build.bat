@echo off
chcp 65001 >nul
echo Windows 系统时间修改工具 - 快速构建脚本
echo ==========================================

:: 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python
    echo 请确保 Python 已安装并添加到 PATH 环境变量
    pause
    exit /b 1
)

echo ✓ Python 已安装

:: 检查是否在虚拟环境中
if defined VIRTUAL_ENV (
    echo ✓ 检测到虚拟环境: %VIRTUAL_ENV%
) else (
    echo ⚠ 未检测到虚拟环境，建议在虚拟环境中构建
)

:: 安装依赖
echo.
echo 正在安装/更新依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo 错误: 依赖包安装失败
    pause
    exit /b 1
)

echo ✓ 依赖包安装完成

:: 运行构建脚本
echo.
echo 开始构建应用程序...
python build.py
if errorlevel 1 (
    echo 错误: 构建失败
    pause
    exit /b 1
)

echo.
echo ==========================================
echo 构建完成！
echo 可执行文件位于 dist 目录中
echo ==========================================
pause
