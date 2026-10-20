"""运行真实 Qt 窗口并验证示例、设置失效、导出和截图，不操控其他应用。"""

import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication
from tft_analysis.application import configure_application
from PySide6.QtWidgets import QDialog
from tft_analysis.ui import MainWindow, ImportDialog


def main():
    app = QApplication([])
    configure_application(app)
    window = MainWindow()
    window.show()
    app.processEvents()
    output = ROOT / "work" / "verification"
    output.mkdir(parents=True, exist_ok=True)
    for index in range(3):
        window.example_combo.setCurrentIndex(index)
        window.load_example()
        assert len(window.curve.voltage) == 200
        assert window.drain.text() == "10"
        assert window.capacitance.text() == ""
        window.start.setValue(-3)
        window.end.setValue(1)
        window.analyze_button.click()
        assert window.result is not None
        assert window.export_button.isEnabled()
        assert window.result.mobility_cm2_vs is None
        app.processEvents()
        if index == 0:
            with patch("tft_analysis.ui.QFileDialog.getExistingDirectory", return_value=str(output)), \
                 patch("tft_analysis.ui.QMessageBox.information"):
                window.export_button.click()
            bundles = sorted(output.glob("TFT分析_*"))
            assert bundles
            destination = bundles[-1]
            assert len(list(destination.iterdir())) == 8
            record = json.loads((destination / "分析记录.json").read_text(encoding="utf-8"))
            assert record["result"]["fitted_points"] == 21
            assert window.grab().save(str(output / "主界面_阈值拟合.png"))
            window.tabs.setCurrentIndex(1)
            app.processEvents()
            assert window.grab().save(str(output / "主界面_半对数曲线.png"))
            window.tabs.setCurrentIndex(3)
            app.processEvents()
            assert window.grab().save(str(output / "主界面_数据预览.png"))
        window.start.setValue(-2.8)
        assert window.result is None
        assert not window.export_button.isEnabled()
    # 验证导入按钮所调用的完整逻辑；仅替换系统文件选择和确认交互。
    source = window.curve.source
    with patch("tft_analysis.ui.QFileDialog.getOpenFileName", return_value=(source, "")), \
         patch.object(ImportDialog, "exec", return_value=QDialog.DialogCode.Accepted):
        window.open_file()
    assert len(window.curve.voltage) == 200
    assert window.width.text() == ""
    assert window.result is None
    window.close()
    print(json.dumps({"gui_smoke": "PASS", "examples": 3, "screenshots": 3,
                      "checks": ["example import", "file import dialog", "fit button", "missing-capacitance guard", "stale-result invalidation", "export button and 8 files", "window render"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
