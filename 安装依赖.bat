@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    py -3.13 -m venv .venv
    if errorlevel 1 (
        echo 请先安装 Python 3.13，并在安装时勾选 Python 启动器。
        pause
        exit /b 1
    )
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo 依赖安装失败，请查看上方提示，检查网络连接和 Python 环境。
) else (
    echo 安装完成。双击“启动程序.bat”即可打开程序。
)
pause
