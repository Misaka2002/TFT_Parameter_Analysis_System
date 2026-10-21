"""区分程序自带资源和用户选择的文件位置。"""

from pathlib import Path
import sys

from PySide6.QtCore import QStandardPaths


RESOURCE_ROOT = Path(__file__).resolve().parent.parent


def default_directory() -> Path:
    """EXE 从用户文档目录选择文件，避免将结果保存到临时解包目录。"""
    if not getattr(sys, "frozen", False):
        return RESOURCE_ROOT
    documents = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
    return Path(documents) if documents else Path.home()
