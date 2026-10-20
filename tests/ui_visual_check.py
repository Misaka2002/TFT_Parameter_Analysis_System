"""Qt 界面的深色主题、布局与高 DPI 验证；仅操作本测试创建的窗口。"""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QMessageBox
from unittest.mock import patch

from tft_analysis.application import configure_application
from tft_analysis.data_io import read_table
from tft_analysis.ui import ImportDialog, MainWindow


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="work/ui_dark_check")
    args = parser.parse_args()
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    # 模拟来自系统的相反初始主题，随后应用必须统一为 GitHub Dark。
    seed = QPalette()
    seed.setColor(QPalette.ColorRole.Window, QColor("white"))
    seed.setColor(QPalette.ColorRole.Text, QColor("black"))
    app.setPalette(seed)
    configure_application(app)
    assert app.palette().color(QPalette.ColorRole.Window).name() == "#0d1117"
    assert app.palette().color(QPalette.ColorRole.Text).name() == "#e6edf3"
    assert app.testAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs)

    window = MainWindow()
    window.resize(1440, 920)
    window.show()
    app.processEvents()

    def capture(widget, name):
        app.processEvents()
        path = output / name
        pixmap = widget.grab()
        assert pixmap.save(str(path)), str(path)
        pixels = np.asarray(Image.open(path).convert("RGB"))[::4, ::4]
        white_fraction = float(np.mean(np.all(pixels > 220, axis=2)))
        assert white_fraction < 0.025, (name, "出现过大浅色区域", white_fraction)

    assert window.content_stack.currentIndex() == 0
    assert not window.analyze_button.isEnabled()
    capture(window, "01_空状态.png")
    window.load_example()
    assert window.sweep_combo.currentIndex() == 0
    assert "升压" in window.sweep_combo.currentText()
    window.analyze_button.click()
    assert window.result is not None
    assert abs(window.result.threshold_v - (-5.86211)) < 1e-4
    assert window.metrics[0].value.text() == "-5.86211"
    assert window.metrics[1].value.text() == "1.49e7"
    assert window.metrics[2].value.text() == "未计算"
    capture(window, "02_阈值拟合.png")
    for index, name in [(0, "03_转移特性.png"), (1, "04_半对数曲线.png"),
                        (3, "05_数据预览.png"), (4, "06_分析记录.png")]:
        window.tabs.setCurrentIndex(index)
        capture(window, name)
    for figure, canvas in window.plots.values():
        assert np.allclose(figure.get_facecolor()[:3], [13 / 255, 17 / 255, 23 / 255])
    for toolbar in window.plot_toolbars.values():
        for name in ("home", "pan", "zoom", "save_figure"):
            assert not toolbar._actions[name].icon().isNull()
    window.tabs.setCurrentIndex(2)
    window.resize(980, 700)
    app.processEvents()
    for metric in window.metrics:
        assert metric.value.fontMetrics().horizontalAdvance(metric.value.text()) <= metric.value.width(), metric.value.text()
    capture(window, "07_紧凑窗口.png")
    source = Path(window.curve.source)
    dialog = ImportDialog(source, read_table(source), window)
    dialog.show()
    capture(dialog, "08_数据导入对话框.png")
    dialog.close()
    # 检查错误/说明弹窗也采用相同暗色调色板。
    message = QMessageBox(QMessageBox.Icon.Information, "使用说明", "选择拟合区间后计算；完整依据见分析记录。", parent=window)
    message.show()
    capture(message, "09_说明弹窗.png")
    message.close()
    # 复选框、数值框与失效结果状态的真实 Qt 交互。
    window.confirm_region.click()
    assert window.confirm_region.isChecked()
    assert window.result is None
    assert not window.export_button.isEnabled()
    window.close()
    print(json.dumps({"result": "PASS", "platform": app.platformName(),
                      "device_pixel_ratio": app.devicePixelRatio(), "screenshots": 9,
                      "checks": ["opposite-palette override", "all-dark surfaces", "empty state", "metrics",
                                 "toolbar icons", "compact numeric labels", "dialogs", "checkbox invalidation"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
