"""使用简化 n/p 型 TFT 场效应模型提取参数；结果是模型估算值，不等同于器件的真实参数。"""

import numpy as np

from .models import AnalysisResult, Curve, FitSettings


def analyze(curve: Curve, settings: FitSettings) -> AnalysisResult:
    if settings.method not in ("saturation", "linear"):
        raise ValueError("未知计算方法。")
    if settings.current_sign not in (-1, 1):
        raise ValueError("电流符号修正必须为 +1 或 -1。")
    sign = settings.polarity_sign
    if not np.isfinite([settings.start, settings.end]).all() or settings.start >= settings.end:
        raise ValueError("拟合下限必须小于上限。")
    # 接线修正保留物理电流符号；仅将符合器件极性的导通电流转成拟合幅值。
    x = curve.voltage
    current = curve.current * settings.current_sign
    y = sign * current
    selected = (x >= settings.start) & (x <= settings.end)
    valid = selected & (y > 0) & np.isfinite(y) & np.isfinite(x)
    excluded = int(selected.sum() - valid.sum())
    xf, yf = x[valid], y[valid]
    if len(xf) < 5 or len(np.unique(xf)) < 5:
        raise ValueError(f"拟合区间需要至少 5 个不同电压点，且接线修正后的电流必须符合 {settings.polarity} 型极性（n 型为正、p 型为负）。")
    if len(np.unique(xf)) != len(xf):
        raise ValueError("拟合区间内存在重复电压点，请选择独立扫描段或调整区间；程序不会自动平均。")
    order = np.argsort(xf)
    xf, yf = xf[order], yf[order]
    observed = np.sqrt(yf) if settings.method == "saturation" else yf
    slope, intercept = np.polyfit(xf, observed, 1)
    if not np.isfinite([slope, intercept]).all() or sign * slope <= 0:
        raise ValueError(f"拟合斜率不符合 {settings.polarity} 型导通方向（n 型应为正、p 型应为负），请检查接线电流符号、拟合区间和器件类型。")
    predicted = slope * xf + intercept
    residual = observed - predicted
    ss_total = float(np.sum((observed - observed.mean()) ** 2))
    if ss_total <= 0:
        raise ValueError("拟合区间的电流没有有效变化。")
    r2 = 1.0 - float(np.sum(residual ** 2)) / ss_total
    threshold = float(-intercept / slope)
    vd = settings.drain_voltage
    bias_ok = vd is not None and np.isfinite(vd) and sign * vd > 0
    if settings.method == "linear" and bias_ok:
        threshold -= vd / 2
    warnings = list(curve.notes)
    warnings.append(f"采用 {settings.polarity} 型简化场效应模型；物理电流 I=原始电流×接线修正系数，拟合电流幅值 J={'I' if sign == 1 else '−I'}，仅使用 J>0 的点。")
    if excluded:
        warnings.append(f"拟合区间中 {excluded} 个电流极性不符、零值或非有限数据点未参与拟合。")
    if r2 < 0.98:
        warnings.append("拟合 R² 低于 0.98，请检查模型与区间；高 R² 也不能单独证明模型适用。")
    overdrive = sign * (xf - threshold)
    region_ok = bool(settings.region_confirmed)
    if not region_ok:
        warnings.append("尚未确认拟合区间的工作区：阈值仅作模型拟合估计，暂不计算迁移率。")
    if np.any(overdrive <= 0):
        region_ok = False
        warnings.append("拟合区间包含导通方向过驱动 u=s(Vg−Vth)≤0 的点，不满足强积累近似，迁移率不予计算（n 型 s=+1，p 型 s=−1）。")
    if not bias_ok:
        region_ok = False
        warnings.append(f"未提供有效的 {settings.polarity} 型漏极偏置（n 型 Vds>0，p 型 Vds<0），无法检查工作区，迁移率不予计算。")
    elif settings.method == "saturation" and np.any(sign * vd < overdrive):
        region_ok = False
        warnings.append("部分拟合点不满足饱和区条件 d≥u，其中 d=sVds、u=s(Vg−Vth)（n 型 s=+1，p 型 s=−1），迁移率不予计算。")
    elif settings.method == "linear" and np.any(sign * vd > 0.1 * overdrive):
        region_ok = False
        warnings.append("部分拟合点不满足小漏压近似 d≤0.1u，其中 d=sVds、u=s(Vg−Vth)（n 型 s=+1，p 型 s=−1），迁移率不予计算。")
    if settings.method == "linear":
        # 在线性区公式中考虑沟道内电压分布后，电压截距为 Vth + Vds/2。
        warnings.append("线性区采用 J=μCi(W/L)(ud−d²/2)；漏压方向有效时，阈值由电压截距扣除有符号 Vds/2。")
        if not bias_ok:
            warnings.append("漏极偏置缺失、无效或方向不符：当前阈值仅为 −b/a 截距近似，尚未进行 Vds/2 修正。")
    positive = y[np.isfinite(y) & (y > 0)]
    ratio = float(positive.max() / positive.min()) if len(positive) >= 2 else None
    warnings.append("扫描电流比为当前扫描段内符合器件极性的电流幅值 J>0 的最大值与最小值之比，仅代表当前电压范围；低电流噪声会影响结果。")
    if (y <= 0).any():
        warnings.append("扫描段包含零电流或极性不符的电流。半对数图显示 |Id|，扫描电流比仅统计 J>0，因此不能直接将它作为已确认的器件开关比。")
    mobility = None
    parameters = [settings.width_um, settings.length_um, settings.capacitance_nf_cm2]
    if any(value is None or not np.isfinite(value) or value <= 0 for value in parameters):
        warnings.append("缺少正值 W、L 或单位面积栅电容 Ci，迁移率不予计算。")
    elif region_ok:
        # 先将栅介质电容从 nF/cm² 换算为 F/m²（1 nF/cm² = 1e-5 F/m²），再把迁移率从 m²/(V·s) 换算为 cm²/(V·s)。
        ci = settings.capacitance_nf_cm2 * 1e-5
        geometry = settings.length_um / settings.width_um
        mobility = float((2 * slope ** 2 if settings.method == "saturation" else abs(slope) / abs(vd)) * geometry / ci * 1e4)
    return AnalysisResult(threshold, float(slope), float(intercept), r2,
                          float(np.sqrt(np.mean(residual ** 2))), len(xf), excluded,
                          ratio, mobility, settings, xf, observed, predicted, warnings)
