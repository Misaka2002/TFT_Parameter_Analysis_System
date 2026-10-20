"""使用固定像素原点的 QtAgg 画布，避免悬浮层在分数缩放下造成局部重绘错位。"""

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PySide6.QtCore import QPoint
from PySide6.QtGui import QImage, QPainter


class StableFigureCanvas(FigureCanvasQTAgg):
    def paintEvent(self, event):
        self._draw_idle()
        if not hasattr(self, "renderer"):
            return
        # 重用已绘制好的 Agg 缓存。鼠标移动悬浮框时，无需重新计算或绘制整张图。
        # 默认后端会先裁剪 event.rect()，再映射到物理像素。缩放比例为 1.5 或 1.875 时，
        # 不同局部矩形可能被舍入到不同像素，留下细线，或让网格偏移一个像素。
        # 使用完整图像并固定 (0, 0) 原点，再由 Qt 按绘制区域裁剪，确保像素映射一致。
        buffer = memoryview(self.buffer_rgba())
        image = QImage(buffer, buffer.shape[1], buffer.shape[0], buffer.strides[0],
                       QImage.Format.Format_RGBA8888)
        image.setDevicePixelRatio(self.device_pixel_ratio)
        painter = QPainter(self)
        try:
            painter.fillRect(self.rect(), self.palette().window())
            painter.drawImage(QPoint(0, 0), image)
            self._draw_rect_callback(painter)
        finally:
            # renderer 持有这块缓存；在 QImage 和 painter 使用期间，必须确保底层 buffer 仍然有效。
            painter.end()
