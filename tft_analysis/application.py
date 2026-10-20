"""初始化应用外观，并兼容 Windows 桌面和离屏截图验证。"""

import os
from pathlib import Path

from PySide6.QtCore import QLibraryInfo, QTranslator
from PySide6.QtGui import QFont, QFontDatabase

from .theme import apply_theme


def configure_application(application):
    application.setApplicationName("TFT参数分析系统")
    application.setOrganizationName("TFTCourseDesign")
    application.setStyle("Fusion")
    # 同时翻译 Qt 自带的按钮、文件选择窗口等界面文字。
    translator = QTranslator(application)
    translations = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if translator.load("qtbase_zh_CN", translations):
        application.installTranslator(translator)
        application._qt_translator = translator
    # Windows 桌面通常能自动找到字体；离屏运行环境可能没有字体数据库。
    if "Microsoft YaHei" not in QFontDatabase.families():
        font_directory = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        for filename in ("msyh.ttc", "msyhbd.ttc", "segoeui.ttf"):
            path = font_directory / filename
            if path.exists():
                QFontDatabase.addApplicationFont(str(path))
    application.setFont(QFont("Microsoft YaHei", 10))
    apply_theme(application)
