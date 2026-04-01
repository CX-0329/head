@echo off
REM AI Agent Dashboard 启动脚本

echo ============================================
echo   AI Agent 分析工具 - Dashboard
echo ============================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 切换到 dashboard 目录
cd /d "%~dp0"

echo [1/3] 检查后端依赖...
pip show Flask >nul 2>&1
if errorlevel 1 (
    echo 安装后端依赖...
    pip install -r requirements.txt
) else (
    echo 后端依赖已安装
)

echo.
echo [2/3] 检查 Agent 环境...
cd ..\my-mini-cc-main
if not exist ".venv" (
    echo 创建 Agent 虚拟环境...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    echo Agent 虚拟环境已存在
)

REM 返回 dashboard 目录
cd ..\dashboard

echo.
echo [3/3] 启动服务器...
echo.
echo 服务器地址: http://localhost:5000
echo 按 Ctrl+C 停止服务器
echo ============================================
echo.

python server.py

pause
