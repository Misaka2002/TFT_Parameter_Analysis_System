"""曲线悬浮信息提示。根据图表显示坐标查找鼠标附近的数据，兼容对数坐标、缩放和平移。"""

from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree
from PySide6.QtCore import QEvent, QObject, QPoint, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget


class HoverPopup(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("curveHoverPopup")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.setStyleSheet("""
            QFrame#curveHoverPopup { background: #161b22; border: 1px solid #58a6ff; border-radius: 7px; }
            QLabel { background: transparent; border: none; font-size: 12px; color: #e6edf3; }
            QLabel#hoverHeading { font-size: 13px; font-weight: 600; color: #58a6ff; }
            QLabel#hoverKey, QLabel#hoverNote { color: #8b949e; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(7)
        self.heading = QLabel()
        self.heading.setObjectName("hoverHeading")
        self.heading.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.heading)
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(4)
        self.rows = []
        for index in range(8):
            key, value = QLabel(), QLabel()
            key.setObjectName("hoverKey")
            key.setTextFormat(Qt.TextFormat.PlainText)
            value.setTextFormat(Qt.TextFormat.PlainText)
            value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            grid.addWidget(key, index, 0)
            grid.addWidget(value, index, 1)
            self.rows.append((key, value))
        layout.addLayout(grid)
        self.note = QLabel()
        self.note.setObjectName("hoverNote")
        self.note.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.note)
        self.hide()

    def present(self, heading, rows, note, cursor):
        self.heading.setText(heading)
        self.heading.setMinimumWidth(self.heading.fontMetrics().horizontalAdvance(heading) + 2)
        for index, (key, value) in enumerate(self.rows):
            visible = index < len(rows)
            key.setVisible(visible)
            value.setVisible(visible)
            if visible:
                key.setText(rows[index][0])
                value.setText(rows[index][1])
                key.setMinimumWidth(key.fontMetrics().horizontalAdvance(rows[index][0]) + 2)
                value.setMinimumWidth(value.fontMetrics().horizontalAdvance(rows[index][1]) + 2)
        self.note.setText(note)
        self.note.setVisible(bool(note))
        if note:
            self.note.setMinimumWidth(self.note.fontMetrics().horizontalAdvance(note) + 2)
        # 切换到信息字段较多的曲线时，先更新布局再调整窗口大小，确保新内容不会被截断。
        self.ensurePolished()
        self.layout().invalidate()
        self.layout().activate()
        self.resize(self.layout().sizeHint().expandedTo(self.layout().minimumSize()))
        bounds = self.parentWidget().rect()
        x, y = cursor.x() + 18, cursor.y() + 18
        if x + self.width() > bounds.right() - 8:
            x = cursor.x() - self.width() - 18
        if y + self.height() > bounds.bottom() - 8:
            y = cursor.y() - self.height() - 18
        self.move(max(8, min(x, bounds.width() - self.width() - 8)),
                  max(8, min(y, bounds.height() - self.height() - 8)))
        self.show()
        self.raise_()


class HoverMarker(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedSize(18, 18)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent; border: none;")
        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#58a6ff"), 2))
        painter.setBrush(QColor("#0d1117"))
        painter.drawEllipse(4, 4, 10, 10)


@dataclass
class DisplaySeries:
    artist: object
    kind: str
    positions: np.ndarray
    valid_indices: np.ndarray
    tree: object
    segments: np.ndarray


class CurveHoverController(QObject):
    """每个画布只绑定一组鼠标事件。重绘后刷新数据缓存，避免重复绑定事件或累积图元。"""

    def __init__(self, canvas, toolbar, popup_parent, mode):
        super().__init__(canvas)
        self.canvas, self.toolbar, self.mode = canvas, toolbar, mode
        self.popup = HoverPopup(popup_parent)
        self.marker = HoverMarker(canvas)
        self.curve = self.result = None
        self.sign = 1
        self.method = "saturation"
        self.polarity = "n"
        self.series = []
        self.last_details = None
        self._watched_window = None
        canvas.setMouseTracking(True)
        canvas.installEventFilter(self)
        self.connections = {
            name: canvas.mpl_connect(name, handler) for name, handler in (
                ("motion_notify_event", self.on_motion), ("draw_event", self.on_draw),
                ("figure_leave_event", self.hide), ("button_press_event", self.hide),
                ("scroll_event", self.hide), ("resize_event", self.on_resize),
                ("close_event", self.hide))
        }
        # 切换到平移或缩放工具时立即隐藏提示框，无需等待下一次鼠标移动。
        for action in toolbar.actions():
            action.triggered.connect(self.hide)

    def configure(self, curve, result, sign=1, method="saturation", polarity="n"):
        self.hide()
        self.curve, self.result, self.sign, self.method = curve, result, sign, method
        self.polarity = result.settings.polarity if result is not None else polarity
        self.series = []
        # 创建组件时，画布可能尚未加入主窗口；等数据加载、窗口层级确定后再绑定顶层窗口。
        top_level = self.canvas.window()
        if top_level is not self._watched_window:
            if self._watched_window is not None:
                self._watched_window.removeEventFilter(self)
            top_level.installEventFilter(self)
            self._watched_window = top_level

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.Leave, QEvent.Type.Hide, QEvent.Type.WindowDeactivate):
            self.hide()
        return False

    def hide(self, *_):
        self.popup.hide()
        self.marker.hide()
        self.last_details = None

    def on_resize(self, *_):
        self.series = []
        self.hide()

    def on_draw(self, *_):
        self.hide()
        self.series = []
        if self.curve is None:
            return
        for axes in self.canvas.figure.axes:
            for artist in axes.lines:
                kind = artist.get_gid()
                if kind not in ("tft:raw", "tft:positive", "tft:fit-samples", "tft:fit-model"):
                    continue
                positions = artist.get_transform().transform(artist.get_xydata())
                valid = np.flatnonzero(np.isfinite(positions).all(axis=1))
                if not len(valid):
                    continue
                # 遇到 NaN 时不连接其两侧的数据点，避免连线跨过对数图中无效数值形成的缺口。
                adjacent = np.flatnonzero(np.isfinite(positions[:-1]).all(axis=1)
                                           & np.isfinite(positions[1:]).all(axis=1))
                if artist.get_linestyle() in ("None", "", " "):
                    adjacent = np.array([], dtype=int)
                self.series.append(DisplaySeries(artist, kind, positions, valid,
                                                  cKDTree(positions[valid]), adjacent))

    def _hit(self, series, cursor, radius):
        distance, index = series.tree.query(cursor, distance_upper_bound=radius)
        point_index = int(series.valid_indices[index]) if np.isfinite(distance) else None
        position = series.positions[point_index] if point_index is not None else None
        projected = False
        segments = series.segments
        if len(segments):
            a, b = series.positions[segments], series.positions[segments + 1]
            nearby = (np.minimum(a[:, 0], b[:, 0]) - radius <= cursor[0]) & (np.maximum(a[:, 0], b[:, 0]) + radius >= cursor[0])
            nearby &= (np.minimum(a[:, 1], b[:, 1]) - radius <= cursor[1]) & (np.maximum(a[:, 1], b[:, 1]) + radius >= cursor[1])
            candidate = segments[nearby]
            if len(candidate):
                a, b = series.positions[candidate], series.positions[candidate + 1]
                ab = b - a
                denominator = np.einsum("ij,ij->i", ab, ab)
                t = np.divide(np.einsum("ij,ij->i", cursor - a, ab), denominator,
                              out=np.zeros(len(a)), where=denominator > 0)
                t = np.clip(t, 0, 1)
                projections = a + t[:, None] * ab
                distances = np.linalg.norm(projections - cursor, axis=1)
                nearest = int(np.argmin(distances))
                if distances[nearest] <= radius and distances[nearest] < distance:
                    distance = float(distances[nearest])
                    segment = int(candidate[nearest])
                    if series.kind == "tft:fit-model":
                        position = projections[nearest]
                        point_index = segment
                        projected = True
                    else:
                        # 实测曲线由采样点连线显示，鼠标命中时仍返回最近采样点的数据，不把线段上的位置误当成实测值。
                        point_index = segment + int(t[nearest] > 0.5)
                        position = series.positions[point_index]
        if position is None or distance > radius:
            return None
        return float(distance), point_index, position, projected

    def on_motion(self, event):
        if (self.curve is None or event.inaxes is None or not self.canvas.isVisible()
                or self.toolbar.mode or getattr(event, "buttons", None)):
            self.hide()
            return
        ratio = float(self.canvas.device_pixel_ratio)
        legend = event.inaxes.get_legend()
        if legend is not None and legend.get_visible() and legend.get_window_extent().contains(event.x, event.y):
            self.hide()
            return
        cursor = np.array([event.x, event.y], dtype=float)
        radius = 9 * ratio
        matches = []
        priorities = {"tft:raw": 0, "tft:positive": 0, "tft:fit-model": 1, "tft:fit-samples": 3}
        for series in self.series:
            if series.artist.axes is not event.inaxes or not series.artist.get_visible():
                continue
            hit = self._hit(series, cursor, radius)
            if hit is not None:
                # 实测点和拟合线重叠时，优先显示参与拟合的实测点；拟合线仍作为独立模型结果提供信息。
                matches.append((hit[0] - priorities[series.kind] * ratio * 0.4, series, hit))
        if not matches:
            self.hide()
            return
        _, series, hit = min(matches, key=lambda item: item[0])
        _, index, position, projected = hit
        details = self.describe(series, index, position, projected)
        self.last_details = details
        local_cursor = QPoint(round(event.x / ratio), round(self.canvas.height() - event.y / ratio))
        root_cursor = self.canvas.mapTo(self.popup.parentWidget(), local_cursor)
        self.popup.present(details["heading"], details["rows"], details["note"], root_cursor)
        self.marker.move(round(position[0] / ratio) - 9,
                         round(self.canvas.height() - position[1] / ratio) - 9)
        self.marker.show()
        self.marker.raise_()

    def describe(self, series, index, position, projected):
        polarity_sign = 1 if self.polarity == "n" else -1
        transformed = series.artist.axes.transData.inverted().transform(position)
        if series.kind == "tft:fit-model":
            voltage = float(transformed[0])
            value = float(self.result.slope * voltage + self.result.intercept)
            saturation = self.result.settings.method == "saturation"
            rows = [("栅极电压 Vg", f"{voltage:.7g} V"),
                    ("拟合 √|Id|" if saturation else "拟合 |Id|", f"{value:.7g} {'A½' if saturation else 'A'}")]
            if not saturation or value >= 0:
                model_current = polarity_sign * (value ** 2 if saturation else value)
                rows.append(("模型电流 Id", f"{model_current:.7g} A"))
            rows.extend([("阈值估计 Vth", f"{self.result.threshold_v:.7g} V"),
                         ("拟合 R²", f"{self.result.r_squared:.7f}")])
            return {"heading": "拟合曲线 · 模型估计", "rows": rows,
                    "note": "当前位置的模型预测，不是实测点。", "kind": series.kind, "voltage": voltage}
        corrected = self.curve.current * self.sign
        magnitude = polarity_sign * corrected
        eligible = (magnitude > 0) & np.isfinite(magnitude) & np.isfinite(self.curve.voltage)
        if series.kind == "tft:fit-samples":
            valid = ((self.curve.voltage >= self.result.settings.start)
                     & (self.curve.voltage <= self.result.settings.end) & eligible)
            indices = np.flatnonzero(valid)
            indices = indices[np.argsort(self.curve.voltage[indices])]
            source_index = int(indices[index])
        elif series.kind == "tft:positive":
            source_index = int(np.flatnonzero(eligible)[index])
        else:
            source_index = int(index)
        voltage = float(self.curve.voltage[source_index])
        original = float(self.curve.current[source_index])
        current = float(corrected[source_index])
        rows = [("扫描内点序号", str(source_index + 1)), ("栅极电压 Vg", f"{voltage:.7g} V"),
                ("原始电流 Id", f"{original:.7g} A")]
        if self.sign == -1:
            rows.append(("修正后电流 Id", f"{current:.7g} A"))
        if self.mode == "log":
            rows.append(("图示 |Id|", f"{abs(current):.7g} A"))
        elif self.mode == "fit":
            saturation = (self.result.settings.method if self.result else self.method) == "saturation"
            value = float(np.sqrt(polarity_sign * current)) if saturation else polarity_sign * current
            unit = "A½" if saturation else "A"
            rows.append(("图示 √|Id|" if saturation else "图示 |Id|", f"{value:.7g} {unit}"))
            if series.kind == "tft:fit-samples":
                predicted = float(self.result.fit_predicted[index])
                rows.extend([("拟合预测", f"{predicted:.7g} {unit}"),
                             ("残差（实测−拟合）", f"{value - predicted:.7g} {unit}")])
        return {"heading": "参与拟合的实测点" if series.kind == "tft:fit-samples" else "实测曲线 · 最近采样点",
                "rows": rows, "note": "对数图显示绝对值，原始符号保留。" if self.mode == "log" else "数值对应当前扫描中的实际采样点。",
                "kind": series.kind, "source_index": source_index, "voltage": voltage, "original_current": original}
