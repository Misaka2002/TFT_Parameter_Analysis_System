"""针对公式、扫描分离和文件导入的独立验证。"""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from tft_analysis.data_io import make_curve, read_table, split_sweeps
from tft_analysis.extraction import analyze
from tft_analysis.export import export_bundle
from tft_analysis.models import Curve, FitSettings

ROOT = Path(__file__).resolve().parents[1]


class CoreTests(unittest.TestCase):
    def curve(self, x, y):
        return Curve(np.asarray(x, dtype=float), np.asarray(y, dtype=float), "synthetic", "test", "已知参数模拟曲线")

    def test_saturation_known_parameters_and_units(self):
        # 独立按物理公式生成 μ=12 cm²/Vs、Vth=2 V 的理想曲线。
        x = np.linspace(3, 8, 101)
        mu, ci = 12e-4, 20e-5
        y = 0.5 * mu * ci * (20 / 10) * (x - 2) ** 2
        result = analyze(self.curve(x, y), FitSettings("saturation", 3, 8, 1, 20, 10, 20, 10, True))
        self.assertAlmostEqual(result.threshold_v, 2, places=10)
        self.assertAlmostEqual(result.mobility_cm2_vs, 12, places=9)
        self.assertAlmostEqual(result.r_squared, 1, places=12)

    def test_linear_finite_drain_voltage_correction(self):
        x, vd, vth = np.linspace(3, 8, 101), 0.05, 1.4
        y = 8e-4 * 15e-5 * (30 / 10) * ((x - vth) * vd - vd ** 2 / 2)
        result = analyze(self.curve(x, y), FitSettings("linear", 3, 8, 1, 30, 10, 15, vd, True))
        self.assertAlmostEqual(result.threshold_v, vth, places=10)
        self.assertAlmostEqual(result.mobility_cm2_vs, 8, places=9)

    def test_missing_conditions_suppress_mobility(self):
        x = np.arange(3, 12, dtype=float)
        result = analyze(self.curve(x, (x - 1) ** 2 * 1e-7), FitSettings(start=3, end=11))
        self.assertIsNone(result.mobility_cm2_vs)
        self.assertTrue(result.warnings)

    def test_wrong_region_suppresses_mobility(self):
        x = np.arange(3, 12, dtype=float)
        result = analyze(self.curve(x, (x - 1) ** 2 * 1e-7),
                         FitSettings("saturation", 3, 11, 1, 10, 10, 20, 1, True))
        self.assertIsNone(result.mobility_cm2_vs)

    def test_negative_measurement_sign_is_explicit(self):
        x = np.arange(3, 12, dtype=float)
        curve = self.curve(x, -(x - 1) ** 2 * 1e-7)
        with self.assertRaises(ValueError):
            analyze(curve, FitSettings(start=3, end=11))
        result = analyze(curve, FitSettings(start=3, end=11, current_sign=-1))
        self.assertAlmostEqual(result.threshold_v, 1, places=10)

    def test_reject_invalid_fit_interval_and_duplicate_voltage(self):
        x = np.arange(3, 12, dtype=float)
        curve = self.curve(x, (x - 1) ** 2)
        for settings in (FitSettings(start=10, end=3), FitSettings(start=3, end=3.5)):
            with self.assertRaises(ValueError):
                analyze(curve, settings)
        curve = self.curve([3, 4, 5, 5, 6, 7, 8], np.arange(1, 8) ** 2)
        with self.assertRaisesRegex(ValueError, "重复电压"):
            analyze(curve, FitSettings(start=3, end=8))

    def test_sweeps_never_mix_forward_and_reverse(self):
        curve = self.curve([0, 1, 2, 3, 2, 1, 0], [1, 2, 3, 4, 6, 7, 8])
        sweeps = split_sweeps(curve)
        self.assertEqual(len(sweeps), 2)
        np.testing.assert_array_equal(sweeps[0].voltage, [0, 1, 2, 3])
        np.testing.assert_array_equal(sweeps[1].voltage, [3, 2, 1, 0])
        self.assertEqual(sweeps[1].current[-1], 8)

    def test_import_no_header_preserves_first_row_and_units(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "values.txt"
            path.write_text("\n".join(f"{v * 1000}\t{v * 2}" for v in range(1, 7)), encoding="utf-8")
            curve = make_curve(read_table(path), path, voltage_unit="mV", current_unit="µA")
            self.assertEqual(len(curve.voltage), 6)
            self.assertEqual(curve.voltage[0], 1)
            self.assertAlmostEqual(curve.current[0], 2e-6)

    def test_import_header_nan_and_column_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "values.csv"
            path.write_text("current,voltage\n" + "\n".join(f"{v * 2},{v}" for v in range(1, 7)) + "\nBAD,7\n", encoding="utf-8")
            curve = make_curve(read_table(path), path, 1, 0)
            self.assertEqual(curve.provenance["excluded_rows"], 1)
            self.assertEqual(curve.voltage[0], 1)
            with self.assertRaises(ValueError):
                make_curve(read_table(path), path, 0, 0)

    def test_excel_headerless_and_constant_voltage_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "values.xlsx"
            pd.DataFrame({0: np.arange(6), 1: np.arange(6) * 1e-6}).to_excel(path, header=False, index=False)
            curve = make_curve(read_table(path), path)
            self.assertEqual(len(curve.voltage), 6)
            self.assertEqual(curve.voltage[0], 0)
        with self.assertRaisesRegex(ValueError, "没有变化"):
            split_sweeps(self.curve(np.ones(6), np.arange(6)))

    def test_real_data_hashes_and_complete_analysis_export(self):
        metadata = json.loads((ROOT / "data/example_metadata.json").read_text(encoding="utf-8-sig"))
        for sample in metadata["dataset"]["samples"]:
            path = ROOT / sample["path"]
            self.assertEqual(hashlib.md5(path.read_bytes()).hexdigest(), sample["md5"])
            curve = make_curve(read_table(path), path)
            self.assertEqual(len(curve.voltage), 200)
            sweep = split_sweeps(curve)[0]
            result = analyze(sweep, FitSettings(start=-3, end=1, drain_voltage=10))
            self.assertTrue(np.isfinite(result.threshold_v))
            self.assertIsNone(result.mobility_cm2_vs)
            with tempfile.TemporaryDirectory() as directory:
                export_bundle(directory, sweep, result)
                record = json.loads((Path(directory) / "分析记录.json").read_text(encoding="utf-8"))
                self.assertEqual(record["source_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
                self.assertEqual(len(list(Path(directory).glob("*.png"))), 3)
                self.assertGreater((Path(directory) / "拟合数据.csv").stat().st_size, 100)


if __name__ == "__main__":
    unittest.main()
