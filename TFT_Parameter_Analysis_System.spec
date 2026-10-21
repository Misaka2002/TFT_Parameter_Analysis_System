# 使用项目目录定位资源，与运行打包命令时的工作目录无关。
from pathlib import Path
import os
import sys

root = Path(SPECPATH)
# 只在 Python 和 Windows 运行目录内查找外部依赖，避免其他工具的同名 DLL 混入程序。
windows = Path(os.environ.get("SystemRoot", "C:/Windows"))
os.environ["PATH"] = os.pathsep.join(str(path) for path in (
    Path(sys.executable).parent, Path(sys.base_prefix), Path(sys.base_prefix) / "DLLs",
    windows / "System32", windows,
))
application = Analysis(
    [str(root / "app.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "data"), "data"),
        (str(root / "assets" / "app.ico"), "assets"),
        (str(root / "docs" / "SOURCE_DATA.md"), "docs"),
        (str(root / "docs" / "P_TYPE_DATA.md"), "docs"),
    ],
    hiddenimports=["openpyxl", "pandas.io.excel._openpyxl"],
    hookspath=[],
    hooksconfig={"matplotlib": {"backends": ["QtAgg", "Agg"]}},
    runtime_hooks=[],
    excludes=["tkinter", "PyQt5", "PyQt6", "PySide2", "IPython", "pytest",
              "matplotlib.tests", "numpy.tests", "pandas.tests", "scipy.tests"],
    noarchive=False,
    optimize=1,
)
archive = PYZ(application.pure)
executable = EXE(
    archive, application.scripts, application.binaries, application.datas, [],
    name="TFT参数分析系统_v0.4.0",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(root / "assets" / "app.ico"),
    version=str(root / "packaging" / "windows_version.txt"),
    uac_admin=False,
)
