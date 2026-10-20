"""读取悬浮层隐藏后的实际 Windows 屏幕像素，避免 QWidget.grab 强制重绘而掩盖残影。"""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
from PIL import Image
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from tft_analysis.application import configure_application
from tft_analysis.ui import MainWindow


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="work/hover_repaint")
    args = parser.parse_args()
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    configure_application(app)
    if app.platformName() != "windows":
        raise RuntimeError("此验证必须使用真实 Windows Qt 平台，不能用离屏抓图替代。")
    window = MainWindow()
    window.resize(1440, 920)
    window.show()
    window.load_example()
    window.run_analysis()
    window.activateWindow()
    window.raise_()
    QTest.qWait(120)
    figure, canvas = window.plots["fit"]
    controller = window.hover_controllers["fit"]
    canvas.draw()
    QTest.qWait(60)
    result = window.result

    def capture(name):
        # 抓取本测试自己创建的顶层窗口；不触发 Qt 重绘，也不读取其他应用。
        pixmap = window.screen().grabWindow(int(window.winId()))
        if pixmap.isNull():
            raise RuntimeError("无法读取测试窗口的屏幕像素。")
        path = output / name
        pixmap.save(str(path))
        image = Image.open(path).convert("RGB")
        sx, sy = image.width / window.rect().width(), image.height / window.rect().height()
        origin = canvas.mapTo(window, QPoint(0, 0))
        crop = image.crop((round(origin.x() * sx), round(origin.y() * sy),
                           round((origin.x() + canvas.width()) * sx),
                           round((origin.y() + canvas.height()) * sy)))
        crop.save(output / ("canvas_" + name))
        return np.asarray(crop)

    baseline = capture("01_显示悬浮前.png")
    draws = []
    canvas.mpl_connect("draw_event", lambda event: draws.append(1))
    reports = []

    def assert_restored(name, reference):
        app.sendEvent(canvas, QEvent(QEvent.Type.Leave))
        QTest.qWait(50)
        assert not controller.popup.isVisible()
        after = capture(name + ".png")
        difference = np.abs(after.astype(int) - reference.astype(int))
        damaged = np.any(difference > 8, axis=2)
        image = np.zeros_like(after)
        image[damaged] = [255, 64, 64]
        Image.fromarray(image).save(output / (name + "_差异.png"))
        report = {"scenario": name, "changed_canvas_pixels": int(damaged.sum()),
                  "max_difference": int(difference.max())}
        reports.append(report)
        assert report["changed_canvas_pixels"] == 0, report

    def move(x):
        y = result.slope * x + result.intercept
        point = figure.axes[0].transData.transform((x, y))
        ratio = canvas.device_pixel_ratio
        local = QPointF(point[0] / ratio, canvas.height() - point[1] / ratio)
        event = QMouseEvent(QEvent.Type.MouseMove, local,
                            QPointF(canvas.mapToGlobal(local.toPoint())), Qt.MouseButton.NoButton,
                            Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
        app.sendEvent(canvas, event)
        QTest.qWait(2)

    # 悬浮框仅出现一次再隐藏，也必须干净恢复，不依赖移动方向。
    move(-1)
    assert controller.popup.isVisible()
    assert_restored("02_单次出现后隐藏", baseline)
    shown = 0
    for coordinates in (np.linspace(0.95, -2.95, 91), np.linspace(-2.95, 0.95, 87),
                        np.array([-1.0, 0.1, -2.0, 0.6, -0.5, 0.3, -1.4])):
        for x in coordinates:
            move(float(x))
            shown += int(controller.popup.isVisible())
    assert shown > 100
    capture("03_连续移动后悬浮中.png")
    assert_restored("04_多方向移动和尺寸切换后隐藏", baseline)
    # 标签隐藏后恢复，底图与原始像素一致。
    move(-1)
    window.tabs.setCurrentIndex(3)
    QTest.qWait(30)
    assert not controller.popup.isVisible()
    window.tabs.setCurrentIndex(2)
    QTest.qWait(50)
    assert_restored("05_切换标签后恢复", baseline)
    motion_draws = len(draws)
    # 窗口改变尺寸会触发必要的 Agg 重绘；以新尺寸建立基线再检查覆盖区域。
    window.resize(1100, 760)
    QTest.qWait(80)
    resized_baseline = capture("06_缩放窗口后基线.png")
    for x in np.linspace(0.9, -2.9, 49):
        move(float(x))
    assert_restored("07_缩放窗口后悬浮恢复", resized_baseline)
    report = {"platform": app.platformName(), "device_pixel_ratio": canvas.device_pixel_ratio,
              "hover_frames": shown, "scenarios": reports,
              "agg_redraws_before_window_resize": motion_draws}
    print(json.dumps(report, ensure_ascii=False), flush=True)
    window.close()
    assert motion_draws == 0, "悬浮移动不应反复进行整图 Agg 计算。"


if __name__ == "__main__":
    main()
