import numpy as np
from matplotlib.figure import Figure
from matplotlib import rcParams

from .models import AnalysisResult, Curve

rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
rcParams["axes.unicode_minus"] = False


def draw_curve(figure: Figure, curve: Curve | None, result: AnalysisResult | None, mode: str,
               sign: int = 1, method_hint: str = "saturation", theme: str = "light",
               polarity: str = "n") -> None:
    # 界面图表使用深色背景，单独导出的报告图片使用白底；配色只影响显示，不会改变计算数据。
    dark = theme == "dark"
    background = "#0d1117" if dark else "#ffffff"
    text = "#c9d1d9" if dark else "#1f2328"
    muted = "#8b949e" if dark else "#64748b"
    border = "#30363d" if dark else "#d1d9e0"
    blue = "#58a6ff" if dark else "#0969da"
    orange = "#ffa657" if dark else "#bc4c00"
    green = "#3fb950" if dark else "#1a7f37"
    figure.clear()
    # 窗口尺寸变化时重新安排刻度标签，避免高 DPI 或较小窗口裁掉坐标轴文字。
    figure.set_layout_engine("constrained", w_pad=0.10, h_pad=0.10)
    figure.set_facecolor(background)
    ax = figure.add_subplot(111)
    ax.set_facecolor(background)
    ax.tick_params(colors=muted)
    for spine in ax.spines.values():
        spine.set_color(border)
    ax.xaxis.label.set_color(text)
    ax.yaxis.label.set_color(text)
    ax.title.set_color(text)
    if curve is None:
        ax.text(0.5, 0.5, "加载示例或打开数据文件，开始分析", transform=ax.transAxes,
                ha="center", va="center", color=muted, fontsize=13)
        ax.set_axis_off()
    else:
        if result is not None:
            polarity = result.settings.polarity
        polarity_sign = 1 if polarity == "n" else -1
        x, y = curve.voltage, curve.current * sign
        if mode == "linear":
            ax.plot(x, y, color=blue, marker=".", markersize=3, linewidth=1.4, label="测量数据", gid="tft:raw")
            ax.set_ylabel("修正后漏极电流 Id (A)" if sign == -1 else "漏极电流 Id (A)")
            ax.set_title("转移特性")
        elif mode == "log":
            absolute = np.where(y != 0, np.abs(y), np.nan)
            ax.semilogy(x, absolute, color=blue, marker=".", markersize=3, linewidth=1.4,
                        label="|Id|；零值不显示", gid="tft:raw")
            ax.set_ylabel("漏极电流绝对值 |Id| (A)")
            ax.set_title("半对数转移特性")
        else:
            saturation = (result.settings.method if result is not None else method_hint) == "saturation"
            magnitude = polarity_sign * y
            positive = (magnitude > 0) & np.isfinite(magnitude) & np.isfinite(x)
            ax.plot(x[positive], np.sqrt(magnitude[positive]) if saturation else magnitude[positive],
                    ".", color=muted, markersize=4, label="符合极性的电流幅值", gid="tft:positive")
            ax.set_ylabel("√|Id| (A½)" if saturation else "|Id| (A)")
            region = "饱和区" if saturation else "线性区"
            ax.set_title(f"阈值电压拟合 · {polarity} 型{region}模型")
            if result is not None:
                ax.plot(result.fit_voltage, result.fit_observed, "o", markersize=4,
                        color=blue, label="参与拟合", gid="tft:fit-samples")
                ax.plot(result.fit_voltage, result.fit_predicted, color=orange, linewidth=2,
                        label=f"拟合 R² = {result.r_squared:.5f}", gid="tft:fit-model")
                ax.axvline(result.threshold_v, color=green, linestyle="--",
                           label=f"Vth ≈ {result.threshold_v:.4g} V")
                intercept_voltage = -result.intercept / result.slope
                # 外推到靠近截距的一端；p 型的截距通常位于拟合区间右侧。
                nearest = int(np.argmin(np.abs(result.fit_voltage - intercept_voltage)))
                ax.plot([intercept_voltage, result.fit_voltage[nearest]],
                        [0, result.fit_predicted[nearest]], color=orange, linestyle=":", linewidth=1.4)
                low = min(result.threshold_v, intercept_voltage, result.settings.start)
                high = max(result.threshold_v, intercept_voltage, result.settings.end)
                span = max(high - low, 1e-6)
                ax.set_xlim(low - span * 0.12, high + span * 0.12)
                ax.set_ylim(min(0, float(result.fit_predicted.min())) - float(result.fit_observed.max()) * 0.08,
                            float(result.fit_observed.max()) * 1.22)
                ax.axhline(0, color=muted, linewidth=0.7)
        if result is not None:
            ax.axvspan(result.settings.start, result.settings.end, alpha=0.08, color=blue, label="拟合区间")
        ax.set_xlabel("栅极电压 Vg (V)")
        ax.grid(True, which="major", alpha=0.65 if dark else 0.4, color=border)
        ax.legend(fontsize=9, loc="best", facecolor="#161b22" if dark else "#ffffff",
                  edgecolor=border, framealpha=0.95, labelcolor=text)
        ax.tick_params(labelsize=9)
