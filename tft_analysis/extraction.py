"""使用常规 n 型 TFT 场效应模型提取参数；拟合结果是模型估算值，不等同于器件的真实参数。"""

import numpy as np

from .models import AnalysisResult, Curve, FitSettings


def analyze(curve: Curve, settings: FitSettings) -> AnalysisResult:
    if settings.method not in ("saturation", "linear"):
        raise ValueError("未知计算方法。")
    if settings.current_sign not in (-1, 1):
        raise ValueError("电流符号修正必须为 +1 或 -1。")
    if not np.isfinite([settings.start, settings.end]).all() or settings.start >= settings.end:
        raise ValueError("拟合下限必须小于上限。")
    x, y = curve.voltage, curve.current * settings.current_sign
    selected = (x >= settings.start) & (x <= settings.end)
    valid = selected & (y > 0) & np.isfinite(y) & np.isfinite(x)
    excluded = int(selected.sum() - valid.sum())
    xf, yf = x[valid], y[valid]
    if len(xf) < 5 or len(np.unique(xf)) < 5:
        raise ValueError("拟合区间需要至少 5 个不同电压点，且修正后的电流必须为正。")
    if len(np.unique(xf)) != len(xf):
        raise ValueError("拟合区间内存在重复电压点，请选择独立扫描段或调整区间；程序不会自动平均。")
    order = np.argsort(xf)
    xf, yf = xf[order], yf[order]
    observed = np.sqrt(yf) if settings.method == "saturation" else yf
    slope, intercept = np.polyfit(xf, observed, 1)
    if not np.isfinite([slope, intercept]).all() or slope <= 0:
        raise ValueError("拟合斜率不大于零。当前仅支持 n 型 TFT，请检查电流符号、拟合区间和器件类型。")
    predicted = slope * xf + intercept
    residual = observed - predicted
    ss_total = float(np.sum((observed - observed.mean()) ** 2))
    if ss_total <= 0:
        raise ValueError("拟合区间的电流没有有效变化。")
    r2 = 1.0 - float(np.sum(residual ** 2)) / ss_total
    threshold = float(-intercept / slope)
    vd = settings.drain_voltage
    if settings.method == "linear" and vd is not None and np.isfinite(vd) and vd > 0:
        threshold -= vd / 2
    warnings = list(curve.notes)
    if excluded:
        warnings.append(f"拟合区间中 {excluded} 个非正电流点未参与拟合。")
    if r2 < 0.98:
        warnings.append("拟合 R² 低于 0.98，请检查模型与区间；高 R² 也不能单独证明模型适用。")
    overdrive = xf - threshold
    region_ok = bool(settings.region_confirmed)
    if not region_ok:
        warnings.append("尚未确认拟合区间的工作区：阈值仅作模型拟合估计，暂不计算迁移率。")
    if np.any(overdrive <= 0):
        region_ok = False
        warnings.append("拟合区间包含 Vg ≤ 拟合阈值的点，不满足强积累近似，迁移率不予计算。")
    if vd is None or not np.isfinite(vd) or vd <= 0:
        region_ok = False
        warnings.append("未提供有效正漏极偏置，无法检查工作区，迁移率不予计算。")
    elif settings.method == "saturation" and np.any(vd < overdrive):
        region_ok = False
        warnings.append("部分拟合点不满足 Vds ≥ Vg−Vth 的饱和区条件，迁移率不予计算。")
    elif settings.method == "linear" and np.any(vd > 0.1 * overdrive):
        region_ok = False
        warnings.append("部分拟合点不满足小漏压近似 Vds ≤ 0.1(Vg−Vth)，迁移率不予计算。")
    if settings.method == "linear":
        # 在线性区公式中考虑沟道内电压分布后，电压截距为 Vth + Vds/2。
        warnings.append("线性区采用 Id=μCi(W/L)[(Vg−Vth)Vds−Vds²/2]；已知 Vds 时对截距扣除 Vds/2。")
        if vd is None:
            warnings.append("未提供 Vds：当前阈值仅为 −b/a 截距近似，尚未进行 Vds/2 修正。")
    positive = y[np.isfinite(y) & (y > 0)]
    ratio = float(positive.max() / positive.min()) if len(positive) >= 2 else None
    warnings.append("扫描电流比为当前扫描段内正电流最大值与最小值之比，仅代表当前电压范围；低电流噪声会影响结果。")
    if (y <= 0).any():
        warnings.append("扫描段包含非正电流。半对数图显示 |Id|，扫描电流比只统计正值，因此不能直接将它作为已验证的器件开关比。")
    mobility = None
    parameters = [settings.width_um, settings.length_um, settings.capacitance_nf_cm2]
    if any(value is None or not np.isfinite(value) or value <= 0 for value in parameters):
        warnings.append("缺少正值 W、L 或单位面积栅电容 Ci，迁移率不予计算。")
    elif region_ok:
        # 先将栅介质电容从 nF/cm² 换算为 F/m²（1 nF/cm² = 1e-5 F/m²），再把迁移率从 m²/(V·s) 换算为 cm²/(V·s)。
        ci = settings.capacitance_nf_cm2 * 1e-5
        geometry = settings.length_um / settings.width_um
        mobility = float((2 * slope ** 2 if settings.method == "saturation" else slope / vd) * geometry / ci * 1e4)
    return AnalysisResult(threshold, float(slope), float(intercept), r2,
                          float(np.sqrt(np.mean(residual ** 2))), len(xf), excluded,
                          ratio, mobility, settings, xf, observed, predicted, warnings)
