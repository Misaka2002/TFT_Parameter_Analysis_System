"""读取原始数据并记录清理过程，保留源文件不变。"""

import hashlib
import io
import re
from pathlib import Path

import numpy as np
import pandas as pd

from .models import Curve

VOLTAGE_UNITS = {"V": 1.0, "mV": 1e-3}
CURRENT_UNITS = {"A": 1.0, "mA": 1e-3, "µA": 1e-6, "nA": 1e-9, "pA": 1e-12}


def read_table(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.stat().st_size > 50 * 1024 * 1024:
        raise ValueError("数据文件不能超过 50 MB，请截取所需数据后再导入。")
    if path.suffix.lower() == ".xlsx":
        table = pd.read_excel(path, header=None)
        if table.empty:
            raise ValueError("Excel 第一个工作表为空。")
        numeric_first_row = pd.to_numeric(table.iloc[0], errors="coerce").notna().all()
        if numeric_first_row:
            note = "读取 Excel 第一个工作表；无表头，保留首行数值。"
        else:
            table.columns = table.iloc[0].astype(str).tolist()
            table = table.iloc[1:].reset_index(drop=True)
            note = "读取 Excel 第一个工作表；首行为列名。"
        table.attrs["read_note"] = note
    else:
        raw = path.read_bytes()
        for encoding in ("utf-8-sig", "gb18030"):
            try:
                text = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("无法识别文本编码，请另存为 UTF-8 CSV。")
        lines = [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
        if not lines:
            raise ValueError("文件中没有数据。")
        first = re.split(r"[,;\t\s]+", lines[0].strip())
        try:
            [float(value) for value in first]
            header = None
        except ValueError:
            header = 0
        # 支持逗号、制表符、分号和空格分隔的数据，兼容常见仪器导出格式。
        table = pd.read_csv(io.StringIO("\n".join(lines)), sep=r"[,;\t\s]+", engine="python", header=header)
        table.attrs["read_note"] = f"文本编码 {encoding}；" + ("首行为列名。" if header == 0 else "无表头，保留首行数值。")
    if table.empty or table.shape[1] < 2:
        raise ValueError("至少需要两列数据：栅极电压与漏极电流。")
    if len(table) > 200_000:
        raise ValueError("数据不能超过 20 万行，请截取所需数据后再导入。")
    table.columns = [f"第 {i + 1} 列 · {name}" for i, name in enumerate(table.columns)]
    return table


def make_curve(table: pd.DataFrame, path: str | Path, voltage_column: int = 0,
               current_column: int = 1, voltage_unit: str = "V", current_unit: str = "A") -> Curve:
    if voltage_column == current_column:
        raise ValueError("电压与电流不能选择同一列。")
    x = pd.to_numeric(table.iloc[:, voltage_column], errors="coerce").to_numpy(dtype=float)
    y = pd.to_numeric(table.iloc[:, current_column], errors="coerce").to_numpy(dtype=float)
    valid = np.isfinite(x) & np.isfinite(y)
    dropped = int((~valid).sum())
    if valid.sum() < 5:
        raise ValueError("有效电压、电流数据不足 5 行。请检查列选择与单位。")
    x, y = x[valid] * VOLTAGE_UNITS[voltage_unit], y[valid] * CURRENT_UNITS[current_unit]
    path = Path(path)
    notes = [table.attrs.get("read_note", "")]
    if dropped:
        notes.append(f"已排除 {dropped} 行空值、非数值或非有限值；原文件保持不变。")
    return Curve(x, y, str(path.resolve()), hashlib.sha256(path.read_bytes()).hexdigest(), path.name,
                 notes, {"voltage_column": str(table.columns[voltage_column]),
                         "current_column": str(table.columns[current_column]),
                         "input_voltage_unit": voltage_unit, "input_current_unit": current_unit,
                         "original_rows": len(table), "excluded_rows": dropped})


def split_sweeps(curve: Curve) -> list[Curve]:
    """按采集顺序拆分单调扫描段。转折点会同时保留在相邻两段中，迟滞扫描也会分别保留。"""
    changes = np.sign(np.diff(curve.voltage))
    if not np.any(changes):
        raise ValueError("栅极电压没有变化，无法分析转移特性。")
    boundaries = [0]
    direction = 0
    for index, change in enumerate(changes):
        if change and direction and change != direction:
            boundaries.append(index)
        if change:
            direction = change
    boundaries.append(len(curve.voltage) - 1)
    sweeps = []
    for index, (start, end) in enumerate(zip(boundaries[:-1], boundaries[1:])):
        if end <= start:
            continue
        x, y = curve.voltage[start:end + 1].copy(), curve.current[start:end + 1].copy()
        name = "升压" if x[-1] > x[0] else "降压"
        provenance = dict(curve.provenance, sweep_index=index + 1, row_start=start, row_end=end,
                          sweep_direction=name)
        sweeps.append(Curve(x, y, curve.source, curve.sha256, f"扫描 {index + 1} · {name} · {len(x)} 点",
                            list(curve.notes), provenance))
    if not sweeps:
        raise ValueError("栅极电压没有变化，无法分析转移特性。")
    return sweeps
