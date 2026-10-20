from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import numpy as np


@dataclass
class Curve:
    voltage: np.ndarray
    current: np.ndarray
    source: str
    sha256: str
    label: str
    notes: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass
class FitSettings:
    method: str = "saturation"
    start: float = 0.0
    end: float = 10.0
    current_sign: int = 1
    width_um: float | None = None
    length_um: float | None = None
    capacitance_nf_cm2: float | None = None
    drain_voltage: float | None = None
    region_confirmed: bool = False


@dataclass
class AnalysisResult:
    threshold_v: float
    slope: float
    intercept: float
    r_squared: float
    rmse: float
    fitted_points: int
    excluded_points: int
    on_off_ratio: float | None
    mobility_cm2_vs: float | None
    settings: FitSettings
    fit_voltage: np.ndarray
    fit_observed: np.ndarray
    fit_predicted: np.ndarray
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> dict:
        return {
            "threshold_v": self.threshold_v,
            "slope": self.slope,
            "intercept": self.intercept,
            "r_squared": self.r_squared,
            "rmse": self.rmse,
            "fitted_points": self.fitted_points,
            "excluded_points": self.excluded_points,
            "on_off_ratio": self.on_off_ratio,
            "mobility_cm2_vs": self.mobility_cm2_vs,
            "settings": asdict(self.settings),
            "warnings": self.warnings,
        }
