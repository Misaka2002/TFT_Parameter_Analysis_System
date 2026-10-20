"""界面中可重复使用的组件。"""

from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QSizePolicy

from .theme import icon


class MetricCard(QFrame):
    def __init__(self, label, hint, parent=None):
        super().__init__(parent)
        self.setObjectName("resultCard")
        self.setMinimumWidth(125)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(5)
        title = QLabel(label)
        title.setObjectName("resultLabel")
        title.setFixedHeight(18)
        self.value = QLabel("—")
        self.value.setObjectName("resultValue")
        self.value.setFixedHeight(30)
        self.value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.value.setMinimumWidth(0)
        self.value.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.hint = QLabel(hint)
        self.hint.setObjectName("muted")
        self.hint.setWordWrap(True)
        self.hint.setMinimumHeight(18)
        layout.addWidget(title)
        layout.addWidget(self.value)
        layout.addWidget(self.hint)

    def set_value(self, value, tooltip=""):
        self.value.setText(value)
        self.value.setToolTip(tooltip or value)


class PlotToolbar(NavigationToolbar2QT):
    # 为线框图标指定固定颜色，避免其外观随系统主题改变。
    toolitems = (
        ("复位", "恢复完整视图", "home", "home"),
        ("后退", "返回上一视图", "back", "back"),
        ("前进", "进入下一视图", "forward", "forward"),
        (None, None, None, None),
        ("平移", "拖动平移；再次点击退出", "move", "pan"),
        ("缩放", "拖动框选缩放；再次点击退出", "zoom_to_rect", "zoom"),
        (None, None, None, None),
        ("保存", "保存当前图表", "filesave", "save_figure"),
    )

    def _icon(self, name):
        names = {"home": "home", "back": "back", "forward": "forward", "move": "pan",
                 "zoom_to_rect": "zoom", "filesave": "save"}
        return icon(names.get(name.removesuffix(".png"), "chart"), size=18)

    def __init__(self, canvas, parent=None):
        super().__init__(canvas, parent, coordinates=False)
        self.setObjectName("plotToolbar")
        self.setIconSize(QSize(18, 18))
        self.setMovable(False)
        self.setFloatable(False)
        spacer = QFrame()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.addWidget(spacer)
        hint = QLabel("悬停查看数值 · 平移 / 缩放")
        hint.setObjectName("muted")
        hint.setContentsMargins(0, 0, 12, 0)
        self.addWidget(hint)
