@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo 请先运行“安装依赖.bat”，再打包程序。
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r requirements-build.txt
if errorlevel 1 (
    echo 打包依赖安装失败，请检查上方提示。
    pause
    exit /b 1
)
".venv\Scripts\python.exe" packaging\build_windows.py
if errorlevel 1 (
    echo 打包未完成，请查看上方提示。
) else (
    echo 打包完成，EXE 和分发压缩包保存在 dist 文件夹中。
)
pause
