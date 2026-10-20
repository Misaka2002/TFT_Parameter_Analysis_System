"""GitHub Primer 深色主题和无需额外资源的线框图标。"""

from pathlib import Path
import tempfile

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtSvg import QSvgRenderer

COLORS = {
    "text": "#e6edf3", "muted": "#8b949e", "border": "#30363d",
    "background": "#0d1117", "subtle": "#161b22", "green": "#238636",
    "blue": "#58a6ff", "disabled": "#6e7681",
}

# 统一绘制应用控件，避免不同操作系统的窗口和原生控件外观不一致。
STYLESHEET = """
QWidget { color: #e6edf3; background-color: #0d1117; selection-background-color: #1f3a5f; selection-color: #e6edf3; }
QWidget:disabled { color: #6e7681; }
QMainWindow, QWidget#appRoot { background: #0d1117; }
QWidget#appHeader { background: #010409; border-bottom: 1px solid #30363d; }
QWidget#workspaceBar { background: #0d1117; border-bottom: 1px solid #30363d; }
QWidget#analysisControls { background: transparent; }
QLabel#brandTitle { font-size: 17px; font-weight: 600; }
QLabel#fieldLabel { font-size: 12px; color: #c9d1d9; }
QLabel#fileName { color: #c9d1d9; font-size: 12px; }
QFrame#separator { background: #30363d; border: none; }
QFrame#emptyState { background: #0d1117; border: 1px solid #30363d; border-radius: 6px; }
QWidget#settingsPanel, QScrollArea#settingsPanel, QScrollArea#settingsPanel > QWidget > QWidget { background: #161b22; }
QLabel { background: transparent; border: none; }
QLabel#pageTitle { font-size: 21px; font-weight: 700; }
QLabel#breadcrumb { color: #8b949e; font-size: 12px; }
QLabel#sectionTitle, QLabel#sectionHeader { font-weight: 600; font-size: 13px; }
QLabel#sectionDescription, QLabel#muted { color: #8b949e; font-size: 12px; }
QLabel#badge, QLabel#statusBadge { color: #8b949e; background: #0d1117; border: 1px solid #30363d; border-radius: 10px; padding: 3px 8px; font-size: 11px; }
QLabel#statusBadge { color: #8b949e; background: #161b22; border-color: #30363d; }
QLabel#statusBadge[state="ready"] { color: #58a6ff; background: #101e32; border-color: #1f6feb; }
QLabel#statusBadge[state="complete"] { color: #3fb950; background: #12261e; border-color: #238636; }
QLabel#statusBadge[state="dirty"] { color: #d29922; background: #272115; border-color: #9e6a03; }
QLabel#statusBadge[state="error"] { color: #f85149; background: #2c1518; border-color: #da3633; }
QFrame#resultCard { background: #161b22; border: 1px solid #30363d; border-radius: 6px; }
QLabel#resultValue { color: #e6edf3; font-size: 22px; font-weight: 600; }
QLabel#resultLabel { color: #8b949e; font-size: 12px; }
QLabel#emptyTitle { color: #e6edf3; font-size: 20px; font-weight: 600; }
QLabel#emptyDescription { color: #8b949e; font-size: 13px; }
QLabel#emptyIcon { color: #8b949e; }
QPushButton { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 7px 12px; font-weight: 500; }
QPushButton:hover { background: #21262d; border-color: #484f58; }
QPushButton:pressed { background: #30363d; }
QPushButton:focus { border-color: #58a6ff; }
QPushButton:disabled { background: #161b22; color: #6e7681; border-color: #21262d; }
QPushButton#primary { color: #ffffff; background: #238636; border-color: #2ea043; font-weight: 600; }
QPushButton#primary:hover { background: #2ea043; }
QPushButton#primary:pressed { background: #196c2e; }
QPushButton#primary:disabled { color: #8b949e; background: #1b4721; border-color: #1b4721; }
QPushButton#secondary { background: #0d1117; }
QPushButton#secondary:hover { background: #161b22; }
QLineEdit, QAbstractSpinBox, QComboBox { background: #010409; color: #e6edf3; border: 1px solid #30363d; border-radius: 5px; padding: 6px 8px; selection-background-color: #1f3a5f; }
QLineEdit:focus, QAbstractSpinBox:focus, QComboBox:focus { border: 1px solid #58a6ff; }
QLineEdit:disabled, QAbstractSpinBox:disabled, QComboBox:disabled { color: #6e7681; background: #21262d; }
QLineEdit { placeholder-text-color: #6e7681; }
QAbstractSpinBox QLineEdit { border: none; background: transparent; padding: 0; }
QComboBox { padding-right: 26px; }
QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 24px; border: none; }
QComboBox QAbstractItemView { background: #0d1117; color: #e6edf3; border: 1px solid #30363d; selection-background-color: #1f3a5f; selection-color: #e6edf3; outline: 0; }
QAbstractSpinBox { padding-right: 23px; }
QAbstractSpinBox::up-button, QAbstractSpinBox::down-button { background: #161b22; border: none; border-left: 1px solid #30363d; width: 19px; }
QAbstractSpinBox::up-button { subcontrol-origin: border; subcontrol-position: top right; border-top-right-radius: 5px; }
QAbstractSpinBox::down-button { subcontrol-origin: border; subcontrol-position: bottom right; border-bottom-right-radius: 5px; }
QAbstractSpinBox::up-button:hover, QAbstractSpinBox::down-button:hover { background: #1f3a5f; }
QCheckBox { background: transparent; spacing: 7px; }
QCheckBox::indicator { width: 15px; height: 15px; background: #0d1117; border: 1px solid #6e7681; border-radius: 3px; }
QCheckBox::indicator:hover { border-color: #58a6ff; }
QCheckBox::indicator:checked { background: #238636; border-color: #2ea043; }
QCheckBox::indicator:disabled { background: #21262d; border-color: #30363d; }
QRadioButton { background: transparent; spacing: 7px; }
QRadioButton::indicator { width: 14px; height: 14px; background: #0d1117; border: 1px solid #6e7681; border-radius: 8px; }
QRadioButton::indicator:checked { background: #58a6ff; border: 4px solid #1f3a5f; }
QGroupBox { background: #0d1117; border: 1px solid #30363d; border-radius: 6px; margin-top: 13px; padding-top: 13px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #e6edf3; background: #0d1117; font-weight: 600; }
QScrollArea { background: #0d1117; border: none; }
QScrollArea > QWidget > QWidget { background: #0d1117; }
QScrollBar:vertical { background: #161b22; width: 10px; margin: 0; border: none; }
QScrollBar:horizontal { background: #161b22; height: 10px; margin: 0; border: none; }
QScrollBar::handle { background: #484f58; border-radius: 4px; min-height: 25px; min-width: 25px; }
QScrollBar::handle:hover { background: #6e7681; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; border: none; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
QTabWidget::pane { background: #0d1117; border: 1px solid #30363d; border-top: none; }
QTabBar { background: #0d1117; }
QTabBar::tab { background: #0d1117; color: #8b949e; border: none; border-bottom: 2px solid transparent; padding: 10px 15px; }
QTabBar::tab:selected { color: #e6edf3; font-weight: 600; border-bottom: 2px solid #f78166; }
QTabBar::tab:hover:!selected { background: #161b22; border-bottom: 2px solid #30363d; }
QTableView, QTableWidget { background: #0d1117; alternate-background-color: #161b22; color: #e6edf3; gridline-color: #21262d; border: 1px solid #30363d; border-radius: 5px; selection-background-color: #1f3a5f; selection-color: #e6edf3; }
QTableView::item { padding: 5px; border: none; }
QHeaderView { background: #161b22; }
QHeaderView::section { background: #161b22; color: #8b949e; border: none; border-bottom: 1px solid #30363d; border-right: 1px solid #21262d; padding: 7px; font-weight: 600; }
QTableCornerButton::section { background: #161b22; border: none; }
QTextEdit, QPlainTextEdit, QTextBrowser { background: #0d1117; color: #e6edf3; border: 1px solid #30363d; border-radius: 5px; padding: 7px; selection-background-color: #1f3a5f; }
QToolBar, QToolBar#plotToolbar { background: #0d1117; border: none; border-bottom: 1px solid #30363d; spacing: 3px; padding: 3px; }
QToolButton { background: transparent; color: #8b949e; border: 1px solid transparent; border-radius: 5px; padding: 5px; }
QToolButton:hover { background: #21262d; border-color: #30363d; }
QToolButton:checked, QToolButton:pressed { background: #1f3a5f; border-color: #388bfd; }
QToolButton:disabled { color: #6e7681; }
QToolTip { color: #e6edf3; background: #161b22; border: 1px solid #30363d; padding: 5px; }
QMenuBar { background: #161b22; color: #e6edf3; border-bottom: 1px solid #30363d; }
QMenuBar::item { background: transparent; padding: 5px 10px; }
QMenuBar::item:selected { background: #30363d; }
QMenu { background: #0d1117; color: #e6edf3; border: 1px solid #30363d; padding: 5px; }
QMenu::item { padding: 6px 25px 6px 20px; border-radius: 4px; }
QMenu::item:selected { background: #1f3a5f; color: #e6edf3; }
QMenu::item:disabled { color: #6e7681; }
QMenu::separator { height: 1px; background: #30363d; margin: 4px; }
QDialog, QMessageBox, QFileDialog { background: #0d1117; color: #e6edf3; }
QListView, QTreeView { background: #0d1117; alternate-background-color: #161b22; color: #e6edf3; border: 1px solid #30363d; selection-background-color: #1f3a5f; selection-color: #e6edf3; }
QStatusBar { background: #161b22; color: #8b949e; border-top: 1px solid #30363d; }
QStatusBar::item { border: none; }
QSplitter::handle { background: #21262d; }
QSplitter::handle:hover { background: #1f3a5f; }
QProgressBar { background: #21262d; border: 1px solid #30363d; border-radius: 4px; text-align: center; }
QProgressBar::chunk { background: #238636; border-radius: 3px; }
"""

_PATHS = {
    "file": '<path d="M14 2H6v20h12V6zM14 2v5h5M9 12h6M9 16h6"/>',
    "chart": '<path d="M4 3v17h17M7 15l4-5 4 2 5-7"/>',
    "download": '<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
    "camera": '<path d="M3 7h5l2-3h4l2 3h5v14H3z"/><circle cx="12" cy="14" r="4"/>',
    "help": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 4 2c-1 .7-1.5 1-1.5 2.5M12 17h.01"/>',
    "folder": '<path d="M3 6h7l2 3h9v11H3z"/>',
    "home": '<path d="m3 11 9-8 9 8M5 10v11h5v-7h4v7h5V10"/>',
    "back": '<path d="m10 5-7 7 7 7M3 12h18"/>',
    "forward": '<path d="m14 5 7 7-7 7M3 12h18"/>',
    "pan": '<path d="M12 2v20M2 12h20M9 5l3-3 3 3M9 19l3 3 3-3M5 9l-3 3 3 3M19 9l3 3-3 3"/>',
    "zoom": '<circle cx="10" cy="10" r="6"/><path d="m15 15 6 6M7 10h6M10 7v6"/>',
    "save": '<path d="M4 3h13l4 4v14H3V3zM7 3v6h9V3M7 21v-7h10v7"/>',
    "settings": '<path d="M4 6h16M4 12h16M4 18h16"/><circle cx="8" cy="6" r="2" fill="#0d1117"/><circle cx="16" cy="12" r="2" fill="#0d1117"/><circle cx="10" cy="18" r="2" fill="#0d1117"/>',
    "table": '<rect x="3" y="4" width="18" height="16" rx="1"/><path d="M3 9h18M3 14h18M9 4v16M15 4v16"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>',
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
    "check": '<path d="m5 12 4 4L19 6"/>',
    "reset": '<path d="M4 9a8 8 0 1 1 0 6M4 3v6h6"/>',
}
_ASSET_DIRECTORY = None


def _svg(name, color):
    if name not in _PATHS:
        raise ValueError(f"未知主题图标: {name}")
    safe_color = QColor(color).name()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
            f'fill="none" stroke="{safe_color}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'
            f'{_PATHS[name]}</svg>')


def icon(name, color=None, size=16):
    """生成透明背景的线框图标，并适配深色主题下的禁用状态。调用前需要先创建 QApplication。"""
    size = max(1, int(size))
    result = QIcon()
    for mode, stroke in ((QIcon.Mode.Normal, color or COLORS["muted"]),
                         (QIcon.Mode.Disabled, COLORS["disabled"]),
                         (QIcon.Mode.Active, color or COLORS["text"]),
                         (QIcon.Mode.Selected, color or COLORS["blue"])):
        # 同时生成 1 倍和 2 倍尺寸的图标，保证高 DPI 屏幕上的显示清晰。
        for ratio in (1, 2):
            pixmap = QPixmap(size * ratio, size * ratio)
            pixmap.fill(Qt.GlobalColor.transparent)
            renderer = QSvgRenderer(QByteArray(_svg(name, stroke).encode("utf-8")))
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            pixmap.setDevicePixelRatio(ratio)
            result.addPixmap(pixmap, mode)
    return result


def apply_theme(application):
    """设置应用自身的配色，不更改 Windows 主题或注册表。"""
    global _ASSET_DIRECTORY
    application.setStyle("Fusion")
    application.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)
    application.styleHints().setColorScheme(Qt.ColorScheme.Dark)
    palette = QPalette()
    roles = {
        QPalette.ColorRole.Window: "#0d1117", QPalette.ColorRole.WindowText: "#e6edf3",
        QPalette.ColorRole.Base: "#010409", QPalette.ColorRole.AlternateBase: "#161b22",
        QPalette.ColorRole.Text: "#e6edf3", QPalette.ColorRole.Button: "#161b22",
        QPalette.ColorRole.ButtonText: "#e6edf3", QPalette.ColorRole.BrightText: "#ffffff",
        QPalette.ColorRole.Highlight: "#1f3a5f", QPalette.ColorRole.HighlightedText: "#e6edf3",
        QPalette.ColorRole.ToolTipBase: "#161b22", QPalette.ColorRole.ToolTipText: "#e6edf3",
        QPalette.ColorRole.Link: "#58a6ff", QPalette.ColorRole.LinkVisited: "#bc8cff",
        QPalette.ColorRole.PlaceholderText: "#6e7681", QPalette.ColorRole.Light: "#0d1117",
        QPalette.ColorRole.Midlight: "#161b22", QPalette.ColorRole.Mid: "#30363d",
        QPalette.ColorRole.Dark: "#6e7681", QPalette.ColorRole.Shadow: "#8b949e",
        QPalette.ColorRole.Accent: "#58a6ff",
    }
    for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive, QPalette.ColorGroup.Disabled):
        for role, value in roles.items():
            palette.setColor(group, role, QColor(value))
    for role in (QPalette.ColorRole.Text, QPalette.ColorRole.WindowText, QPalette.ColorRole.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor("#6e7681"))
    for role in (QPalette.ColorRole.Base, QPalette.ColorRole.Button):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor("#21262d"))
    application.setPalette(palette)
    # Qt 样式表通过本机临时 SVG 加载图标。SVG 由程序生成，并在应用退出时清理。
    if _ASSET_DIRECTORY is None:
        _ASSET_DIRECTORY = tempfile.TemporaryDirectory(prefix="tft_theme_")
    directory = Path(_ASSET_DIRECTORY.name)
    for filename, name, color in (("down.svg", "chevron-down", "#8b949e"),
                                  ("check.svg", "check", "#ffffff")):
        (directory / filename).write_text(_svg(name, color), encoding="utf-8")
    (directory / "up.svg").write_text(_svg("chevron-down", "#8b949e").replace('<path ', '<g transform="rotate(180 12 12)"><path ').replace('/></svg>', '/></g></svg>'), encoding="utf-8")
    url = directory.as_posix()
    application.setStyleSheet(STYLESHEET + f'''
QComboBox::down-arrow {{ image: url("{url}/down.svg"); width: 13px; height: 13px; }}
QAbstractSpinBox::up-arrow {{ image: url("{url}/up.svg"); width: 10px; height: 10px; }}
QAbstractSpinBox::down-arrow {{ image: url("{url}/down.svg"); width: 10px; height: 10px; }}
QCheckBox::indicator:checked {{ image: url("{url}/check.svg"); }}
QCheckBox::indicator:checked:disabled {{ background: #6e7681; }}
''')
