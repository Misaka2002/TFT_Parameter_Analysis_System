"""处理桌面界面的操作，参数计算交给 extraction 模块。"""

from datetime import datetime
import json
from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QFormLayout, QHeaderView, QLabel, QMainWindow, QMessageBox,
    QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from .data_io import CURRENT_UNITS, VOLTAGE_UNITS, make_curve, read_table, split_sweeps
from . import __version__
from .extraction import analyze
from .export import export_bundle
from .models import FitSettings
from .layout import build_window
from .plotting import draw_curve

ROOT = Path(__file__).resolve().parent.parent

class ImportDialog(QDialog):
    def __init__(self, path, table, parent=None):
        super().__init__(parent)
        self.setWindowTitle("确认数据列与单位")
        self.resize(720, 440)
        layout = QVBoxLayout(self)
        label = QLabel(f"文件：{Path(path).name}\n{table.attrs.get('read_note', '')}")
        label.setWordWrap(True)
        layout.addWidget(label)
        form = QFormLayout()
        self.voltage_column, self.current_column = QComboBox(), QComboBox()
        self.voltage_column.addItems(table.columns)
        self.current_column.addItems(table.columns)
        self.current_column.setCurrentIndex(1)
        self.voltage_unit, self.current_unit = QComboBox(), QComboBox()
        self.voltage_unit.addItems(VOLTAGE_UNITS)
        self.current_unit.addItems(CURRENT_UNITS)
        form.addRow("栅极电压列", self.voltage_column)
        form.addRow("漏极电流列", self.current_column)
        form.addRow("原始电压单位", self.voltage_unit)
        form.addRow("原始电流单位", self.current_unit)
        layout.addLayout(form)
        preview = QTableWidget(min(6, len(table)), len(table.columns))
        preview.setHorizontalHeaderLabels(table.columns)
        preview.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        for row in range(preview.rowCount()):
            for col in range(preview.columnCount()):
                preview.setItem(row, col, QTableWidgetItem(str(table.iloc[row, col])))
        preview.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(preview)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("导入数据")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"TFT 参数分析工作台 · {__version__}")
        self.setMinimumSize(980, 650)
        screen = self.screen()
        available = screen.availableGeometry() if screen is not None else None
        self.resize(max(980, min(1440, available.width() - 64)) if available else 1440,
                    max(650, min(920, available.height() - 64)) if available else 920)
        self.curves = []
        self.curve = None
        self.result = None
        self._loading = False
        self.examples = json.loads((ROOT / "data" / "example_catalog.json").read_text(encoding="utf-8"))
        build_window(self)
        self.notes.setPlainText("支持固定漏极偏置下的 n 型和 p 型 TFT 转移特性分析。\n\n请按测量条件选择器件类型，电压以源极为参考。可加载 n/p 型公开实测示例，也可导入自己的数据。")
        self.clear_result()
        self.refresh_plots()
        for control in (self.method, self.start, self.end):
            signal = control.currentIndexChanged if isinstance(control, QComboBox) else control.valueChanged
            signal.connect(self.invalidate_result)
        self.invert.toggled.connect(self.invalidate_result)
        self.confirm_region.toggled.connect(self.invalidate_result)
        self.polarity.currentIndexChanged.connect(self.change_polarity)
        for edit in (self.width, self.length, self.capacitance, self.drain):
            edit.textChanged.connect(self.invalidate_result)

    def show_help(self):
        QMessageBox.information(self, "使用说明与计算方法",
            "1. 导入数据后，确认电压列、电流列及单位，再选择要分析的扫描段。\n"
            "2. 选择 n 型或 p 型，查看曲线后输入拟合区间的下限和上限。\n"
            "3. 饱和区：√|Id|=a·Vg+b，Vth=−b/a。\n"
            "4. 线性区：|Id|=a·Vg+b，已知同极性 Vds 时 Vth=−b/a−Vds/2。\n"
            "5. 计算迁移率前，请填写 W、L、Ci、Vds，并确认器件工作区。\n"
            "6. R² 和 RMSE 用于评价本次拟合，计算空间与所选方法一致。\n\n"
            "电压均以源极为参考。p 型通常输入负 Vds、负 Id；仪器输出正电流幅值时，可勾选反转电流符号。\n"
            "拟合只采用符号符合所选器件类型的非零电流，阈值保留原始电压符号。\n\n"
            "当前版本不处理接触电阻修正或复杂迁移率模型。详细说明见项目 README.md。")

    def change_polarity(self, *_):
        p_type = self.polarity.currentData() == "p"
        self.polarity_hint.setText("以源极为参考，p 型通常使用负 Vds 和负 Id。" if p_type
                                   else "以源极为参考，n 型通常使用正 Vds 和正 Id。")
        self.drain.setToolTip("Vds = Vd − Vs，请保留测量偏置的符号；p 型填负值，n 型填正值。")
        self.invalidate_result()

    def set_analysis_state(self, text, state):
        self.state_badge.setText(text)
        self.state_badge.setProperty("state", state)
        self.state_badge.style().unpolish(self.state_badge)
        self.state_badge.style().polish(self.state_badge)
        self.state_badge.update()

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开转移特性数据", str(ROOT),
                                             "数据文件 (*.txt *.csv *.tsv *.xlsx);;所有文件 (*)")
        if not path:
            return
        try:
            table = read_table(path)
            dialog = ImportDialog(path, table, self)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return
            curve = make_curve(table, path, dialog.voltage_column.currentIndex(),
                               dialog.current_column.currentIndex(), dialog.voltage_unit.currentText(),
                               dialog.current_unit.currentText())
            self.set_curve(curve)
        except Exception as error:
            QMessageBox.warning(self, "无法导入数据", str(error))

    def load_example(self):
        try:
            sample = self.examples[self.example_combo.currentIndex()]
            path = ROOT / sample["path"]
            curve = make_curve(read_table(path), path)
            curve.provenance.update(sample.get("provenance", {}))
            curve.provenance.update(dataset_doi=sample["dataset_doi"],
                                    example_name=sample["name"], polarity=sample["polarity"])
            curve.notes.extend(sample.get("notes", []))
            self._loading = True
            self.polarity.setCurrentIndex(self.polarity.findData(sample["polarity"]))
            self._loading = False
            self.set_curve(curve)
            self._loading = True
            self.method.setCurrentIndex(self.method.findData(sample["method"]))
            device = sample.get("device", {})
            for edit, key in [(self.width, "width_um"), (self.length, "length_um"),
                              (self.capacitance, "capacitance_nf_cm2"), (self.drain, "drain_voltage")]:
                value = device.get(key)
                edit.setText("" if value is None else f"{value:g}")
            self.start.setValue(sample["fit_range_v"][0])
            self.end.setValue(sample["fit_range_v"][1])
            self._loading = False
            self.refresh_plots()
        except Exception as error:
            self._loading = False
            QMessageBox.warning(self, "无法加载示例", str(error))

    def set_curve(self, curve):
        curves = split_sweeps(curve)
        self._loading = True
        self.curves = curves
        self.result = None
        self.file_label.setText(Path(curve.source).name)
        self.file_label.setToolTip(curve.source)
        for edit in (self.width, self.length, self.capacitance, self.drain):
            edit.clear()
        self.confirm_region.setChecked(False)
        self.invert.setChecked(False)
        self.method.setCurrentIndex(0)
        self.sweep_combo.clear()
        self.sweep_combo.addItems([item.label for item in curves])
        self.sweep_combo.setCurrentIndex(0)
        self._loading = False
        self.select_sweep(0)

    def select_sweep(self, index):
        if self._loading or index < 0 or index >= len(self.curves):
            return
        self._loading = True
        self.curve = self.curves[index]
        x = self.curve.voltage
        low, high = float(np.min(x)), float(np.max(x))
        self.start.setRange(low, high)
        self.end.setRange(low, high)
        p_type = self.polarity.currentData() == "p"
        self.start.setValue(low + (0.1 if p_type else 0.65) * (high - low))
        self.end.setValue(low + (0.35 if p_type else 0.9) * (high - low))
        self.confirm_region.setChecked(False)
        self._loading = False
        self.analysis_controls.setEnabled(True)
        self.analyze_button.setEnabled(True)
        self.content_stack.setCurrentIndex(1)
        self.source_badge.setText(f"{Path(self.curve.source).name}  ·  {self.curve.label}")
        self.source_badge.setToolTip(self.curve.source)
        self.set_analysis_state("待计算", "ready")
        self.result_note.setText("选择拟合区间，然后点击左侧的计算按钮。")
        self.result = None
        self.clear_result()
        self.refresh_plots()
        self.preview.setRowCount(min(1000, len(x)))
        self.preview.setColumnCount(2)
        self.preview.setHorizontalHeaderLabels(["栅极电压 Vg / V", "原始漏极电流 Id / A"])
        self.preview.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for row in range(self.preview.rowCount()):
            self.preview.setItem(row, 0, QTableWidgetItem(f"{x[row]:.8g}"))
            self.preview.setItem(row, 1, QTableWidgetItem(f"{self.curve.current[row]:.8g}"))
        self.notes.setPlainText("\n\n".join(self.curve.notes) + "\n\n程序已设置初始拟合区间，请查看曲线后按需要调整。数据预览显示前 1000 行，计算使用完整扫描段。")
        self.statusBar().showMessage(f"{Path(self.curve.source).name}  |  {self.curve.label}  |  Vg: {low:g} 至 {high:g} V")

    def clear_result(self):
        for metric in self.metrics:
            metric.set_value("—")
        self.result_table.clearContents()
        for row, label in enumerate(["阈值电压 / V", "扫描电流比", "迁移率 / cm²/(V·s)", "拟合 R²", "参与拟合的点数", "未参与拟合的点数"]):
            self.result_table.setItem(row, 0, QTableWidgetItem(label))
            self.result_table.setItem(row, 1, QTableWidgetItem("—"))
        self.export_button.setEnabled(False)
        for row in range(self.result_table.rowCount()):
            self.result_table.setRowHeight(row, 32)

    def invalidate_result(self, *_):
        if self._loading:
            return
        self.result = None
        self.clear_result()
        if self.curve is not None:
            self.result_note.setText("设置已修改，请重新计算。")
            self.set_analysis_state("待重新计算", "dirty")
            self.notes.setPlainText("\n\n".join(self.curve.notes) + "\n\n设置已修改。为避免混用结果，程序已清除上一次的拟合结果。")
        self.refresh_plots()

    def refresh_plots(self):
        for mode, (figure, canvas) in self.plots.items():
            self.hover_controllers[mode].configure(self.curve, self.result,
                                                   -1 if self.invert.isChecked() else 1,
                                                   self.method.currentData(), self.polarity.currentData())
            draw_curve(figure, self.curve, self.result, mode, -1 if self.invert.isChecked() else 1,
                       self.method.currentData(), theme="dark", polarity=self.polarity.currentData())
            canvas.draw_idle()

    def settings(self):
        def number(edit, label, signed=False):
            text = edit.text().strip()
            if not text:
                return None
            try:
                value = float(text)
            except ValueError:
                raise ValueError(f"{label} 请输入数值，支持科学计数法。") from None
            if signed and (not np.isfinite(value) or value == 0):
                raise ValueError(f"{label} 请输入非零的有限数值，并保留偏置符号；未知时留空。")
            if not signed and (not np.isfinite(value) or value <= 0):
                raise ValueError(f"{label} 必须为有限正数；未知时留空。")
            return value
        return FitSettings(self.method.currentData(), self.start.value(), self.end.value(),
                           -1 if self.invert.isChecked() else 1,
                           number(self.width, "W"), number(self.length, "L"),
                           number(self.capacitance, "Ci"), number(self.drain, "Vds", signed=True),
                           self.confirm_region.isChecked(), polarity=self.polarity.currentData())

    def run_analysis(self):
        if self.curve is None:
            return
        try:
            self.result = analyze(self.curve, self.settings())
        except Exception as error:
            self.result = None
            self.clear_result()
            self.refresh_plots()
            self.result_note.setText("计算未完成，请检查输入。")
            self.set_analysis_state("请检查输入", "error")
            QMessageBox.warning(self, "无法完成计算", str(error))
            return
        result = self.result
        values = [f"{result.threshold_v:.6g}", f"{result.on_off_ratio:.5g}" if result.on_off_ratio is not None else "不可计算",
                  f"{result.mobility_cm2_vs:.6g}" if result.mobility_cm2_vs is not None else "条件未满足",
                  f"{result.r_squared:.6f}", str(result.fitted_points), str(result.excluded_points)]
        for row, value in enumerate(values):
            self.result_table.setItem(row, 1, QTableWidgetItem(value))
        card_values = list(values[:4])
        if result.on_off_ratio is not None:
            # 结果卡片用简短的科学计数法显示，完整数值可在明细和导出文件中查看。
            card_values[1] = f"{result.on_off_ratio:.3g}"
            if "e" in card_values[1]:
                mantissa, exponent = card_values[1].split("e")
                card_values[1] = f"{mantissa}e{int(exponent)}"
        for metric, value, full_value in zip(self.metrics, card_values, values[:4]):
            metric.set_value("未计算" if value == "条件未满足" else value,
                             "请检查器件参数和工作区条件，具体原因见“分析记录”。" if value == "条件未满足" else full_value)
        self.set_analysis_state("分析完成", "complete")
        method = "√|Id|–Vg" if result.settings.method == "saturation" else "|Id|–Vg"
        self.result_note.setText(f"{result.settings.polarity} 型 · {method} 最小二乘拟合  ·  {result.settings.start:g} 至 {result.settings.end:g} V  ·  {result.fitted_points} 个拟合点  ·  阈值为模型估计")
        self.notes.setPlainText("\n\n".join(result.warnings))
        self.export_button.setEnabled(True)
        self.tabs.setCurrentIndex(2)
        self.refresh_plots()
        self.statusBar().showMessage(f"计算完成 · {result.fitted_points} 个拟合点 · R²={result.r_squared:.6f} · 可导出结果")

    def save_results(self):
        if self.result is None:
            return
        parent = QFileDialog.getExistingDirectory(self, "选择分析结果保存位置", str(ROOT))
        if not parent:
            return
        directory = Path(parent) / ("TFT分析_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
        try:
            self.export_button.setEnabled(False)
            directory.mkdir(parents=True, exist_ok=False)
            export_bundle(directory, self.curve, self.result)
            if not self.grab().save(str(directory / "界面截图.png")):
                raise OSError("曲线和参数已导出，但界面截图未能保存。")
            QMessageBox.information(self, "导出完成", f"分析结果已保存，包含参数表、分析记录、数据文件、三幅曲线图和界面截图。\n\n保存位置：{directory}")
        except Exception as error:
            QMessageBox.warning(self, "导出失败", str(error))
        finally:
            self.export_button.setEnabled(self.result is not None)

    def save_screenshot(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存当前界面截图", str(ROOT / "界面截图.png"), "PNG 图片 (*.png)")
        if path and not self.grab().save(path):
            QMessageBox.warning(self, "保存失败", "无法保存图片，请检查文件夹是否可写。")
