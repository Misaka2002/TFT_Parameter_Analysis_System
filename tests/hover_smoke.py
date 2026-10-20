"""通过真实 Qt 鼠标事件验证悬浮，不移动操作系统鼠标或控制其他程序。"""

import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication

from tft_analysis.application import configure_application
from tft_analysis.models import Curve
from tft_analysis.ui import MainWindow


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="work/hover_check")
    args = parser.parse_args()
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    configure_application(app)
    window = MainWindow()
    window.resize(1440, 920)
    window.show()
    window.load_example()
    window.run_analysis()
    app.processEvents()

    def move(mode, x, y):
        index = {"linear": 0, "log": 1, "fit": 2}[mode]
        window.tabs.setCurrentIndex(index)
        app.processEvents()
        figure, canvas = window.plots[mode]
        canvas.draw()
        display = figure.axes[0].transData.transform((x, y))
        ratio = canvas.device_pixel_ratio
        local = QPointF(display[0] / ratio, canvas.height() - display[1] / ratio)
        global_position = canvas.mapToGlobal(local.toPoint())
        event = QMouseEvent(QEvent.Type.MouseMove, local, QPointF(global_position),
                            Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
        app.sendEvent(canvas, event)
        app.processEvents()
        controller = window.hover_controllers[mode]
        if controller.popup.isVisible():
            for key, value in controller.popup.rows:
                if key.isVisible():
                    for widget in (key, value):
                        assert widget.width() >= widget.fontMetrics().horizontalAdvance(widget.text()), widget.text()
        return controller

    curve = window.curve
    # 原始转移曲线：负电流不能被绝对值替代，序号对应实际采样点。
    index = 175
    controller = move("linear", curve.voltage[index], curve.current[index])
    assert controller.popup.isVisible()
    assert controller.last_details["source_index"] == index
    assert controller.last_details["original_current"] == curve.current[index]
    assert window.grab().save(str(output / "01_转移曲线悬浮.png"))
    # 对数轴用屏幕坐标命中，仍显示带符号原始电流。
    index = 15
    controller = move("log", curve.voltage[index], abs(curve.current[index]))
    assert controller.popup.isVisible()
    assert controller.last_details["original_current"] < 0
    assert "图示 |Id|" in dict(controller.last_details["rows"])
    assert window.grab().save(str(output / "02_半对数曲线悬浮.png"))
    result = window.result
    index = 10
    controller = move("fit", result.fit_voltage[index], result.fit_observed[index])
    assert controller.last_details["kind"] == "tft:fit-samples", controller.last_details
    assert "残差（实测−拟合）" in dict(controller.last_details["rows"])
    assert window.grab().save(str(output / "03_拟合点悬浮.png"))
    # 模型线段中间应显示模型预测，并标记为非实测点。
    x = float((result.fit_voltage[10] + result.fit_voltage[11]) / 2)
    y = float(result.slope * x + result.intercept)
    controller = move("fit", x, y)
    assert controller.last_details["kind"] == "tft:fit-model", controller.last_details
    assert abs(controller.last_details["voltage"] - x) < 0.03
    assert window.grab().save(str(output / "04_拟合曲线悬浮.png"))
    # 缩放后重新建立显示坐标缓存，命中值仍对应相同数据点。
    window.tabs.setCurrentIndex(0)
    axes = window.plots["linear"][0].axes[0]
    axes.set_xlim(5, 16)
    axes.set_ylim(1e-5, 5e-5)
    controller = move("linear", curve.voltage[170], curve.current[170])
    assert controller.last_details["source_index"] == 170
    window.plot_toolbars["linear"].home()
    # 直接恢复范围，独立于工具栏的视图历史初始化。
    window.refresh_plots()
    app.processEvents()
    # 边界位置自动翻转/限制在主窗口内部。
    index = 199
    controller = move("linear", curve.voltage[index], curve.current[index])
    assert controller.popup.parentWidget().rect().contains(controller.popup.geometry())
    # 离开、切换标签、启用平移时隐藏，不覆盖操作区域。
    app.sendEvent(controller.canvas, QEvent(QEvent.Type.Leave))
    assert not controller.popup.isVisible()
    controller = move("linear", curve.voltage[170], curve.current[170])
    window.tabs.setCurrentIndex(3)
    app.processEvents()
    assert not controller.popup.isVisible()
    controller = move("linear", curve.voltage[170], curve.current[170])
    window.plot_toolbars["linear"]._actions["pan"].trigger()
    assert not controller.popup.isVisible()
    controller = move("linear", curve.voltage[170], curve.current[170])
    assert not controller.popup.isVisible()
    window.plot_toolbars["linear"]._actions["pan"].trigger()
    # 不断重绘不会累积可命中的曲线或事件回调。
    for _ in range(3):
        window.refresh_plots()
        app.processEvents()
    assert len(window.hover_controllers["linear"].series) == 1
    assert len(window.hover_controllers["linear"].connections) == 7
    controller = move("linear", curve.voltage[170], curve.current[170])
    window.start.setValue(-2.8)
    assert not controller.popup.isVisible()
    # 电流符号修正前后的值同时显示。
    x = np.linspace(0, 10, 51)
    negative_curve = Curve(x, -(x + 1) * 1e-6, "synthetic", "test", "符号验证模拟曲线")
    window.set_curve(negative_curve)
    window.invert.setChecked(True)
    app.processEvents()
    controller = move("linear", 5, 6e-6)
    rows = dict(controller.last_details["rows"])
    assert "修正后电流 Id" in rows and rows["原始电流 Id"].startswith("-6e-06")
    # 连线上没有采样点的位置只报告邻近真实采样点，不生成伪实测值。
    sparse = Curve(np.arange(5, dtype=float), np.arange(1, 6) * 1e-6,
                   "synthetic", "test", "稀疏连线模拟曲线")
    window.set_curve(sparse)
    app.processEvents()
    controller = move("linear", 1.5, 2.5e-6)
    assert controller.last_details["source_index"] in (1, 2)
    assert controller.last_details["voltage"] in (1, 2)
    # 对数图零值缺口两侧不得被错误连接并触发悬浮。
    gaps = Curve(np.arange(5, dtype=float), np.array([1e-3, 0, 1e-5, 1e-4, 1e-2]),
                 "synthetic", "test", "零值缺口模拟曲线")
    window.set_curve(gaps)
    app.processEvents()
    controller = move("log", 1, 1e-4)
    assert not controller.popup.isVisible()
    # 高密度数据命中性能：20 万点，缓存后鼠标移动不重绘整幅图。
    x = np.linspace(-10, 10, 200_000)
    dense_curve = Curve(x, (x + 11) * 1e-6, "synthetic", "test", "性能验证模拟曲线")
    window.set_curve(dense_curve)
    app.processEvents()
    controller = move("linear", x[100_000], dense_curve.current[100_000])
    from matplotlib.backend_bases import MouseEvent
    axes = controller.canvas.figure.axes[0]
    position = axes.transData.transform((x[100_000], dense_curve.current[100_000]))
    event = MouseEvent("motion_notify_event", controller.canvas, *position)
    start = time.perf_counter()
    for _ in range(30):
        controller.on_motion(event)
    average_ms = (time.perf_counter() - start) * 1000 / 30
    assert controller.popup.isVisible()
    assert average_ms < 100, average_ms
    window.close()
    print(json.dumps({"hover": "PASS", "platform": app.platformName(),
                      "device_pixel_ratio": app.devicePixelRatio(), "dense_motion_average_ms": round(average_ms, 2),
                      "checks": ["raw and log sign", "fit residuals", "model interpolation", "boundary placement",
                                 "zoom transform", "leave and tab hide", "pan suppression", "redraw reset",
                                 "sign inversion", "sample-only raw values", "log zero gap", "200k points"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
