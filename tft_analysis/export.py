"""导出包含数据、设置和计算结果的分析包，便于复核；原始数据目录保持不变。"""

import csv
from datetime import datetime, timezone
import json
from pathlib import Path

from matplotlib.figure import Figure

from . import __version__
from .models import AnalysisResult, Curve
from .plotting import draw_curve


def export_bundle(directory: str | Path, curve: Curve, result: AnalysisResult) -> Path:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "参数结果.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["参数", "数值", "单位或说明"])
        writer.writerows([
            ["阈值电压", result.threshold_v, "V；模型拟合估计"],
            ["扫描电流比", result.on_off_ratio, "当前扫描段内正电流最大值与最小值之比；无量纲"],
            ["场效应迁移率", result.mobility_cm2_vs, "cm²/(V·s)；空值表示条件不满足"],
            ["R²", result.r_squared, "所选变换空间"],
            ["拟合点数", result.fitted_points, ""],
            ["拟合斜率", result.slope, "A½/V（饱和）或 A/V（线性）"],
            ["拟合截距", result.intercept, "A½（饱和）或 A（线性）"],
            ["拟合RMSE", result.rmse, "A½（饱和）或 A（线性）"],
        ])
    record = {"application_version": __version__, "exported_at_utc": datetime.now(timezone.utc).isoformat(),
              "source_path": curve.source, "source_sha256": curve.sha256, "curve_label": curve.label,
              "provenance": curve.provenance, "result": result.summary()}
    (directory / "分析记录.json").write_text(json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    with (directory / "当前扫描数据.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["gate_voltage_V", "original_drain_current_A", "corrected_drain_current_A"])
        writer.writerows(zip(curve.voltage, curve.current, curve.current * result.settings.current_sign))
    with (directory / "拟合数据.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["gate_voltage_V", "transformed_observed", "transformed_predicted", "residual"])
        writer.writerows(zip(result.fit_voltage, result.fit_observed, result.fit_predicted,
                             result.fit_observed - result.fit_predicted))
    for mode, name in [("linear", "转移特性"), ("log", "半对数曲线"), ("fit", "拟合曲线")]:
        figure = Figure(figsize=(8, 5.2), dpi=150)
        draw_curve(figure, curve, result, mode, result.settings.current_sign)
        figure.savefig(directory / f"{name}.png", dpi=240, facecolor="white")
        figure.clear()
    return directory
