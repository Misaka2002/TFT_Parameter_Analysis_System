"""生成 Windows 单文件程序及便于分发的压缩包。"""

import argparse
import hashlib
from importlib import metadata
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tft_analysis import __version__


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-only", action="store_true", help="为已经生成的 EXE 整理分发文件")
    arguments = parser.parse_args()
    if sys.platform != "win32" or struct.calcsize("P") != 8:
        raise SystemExit("请在 Windows 64 位 Python 环境中打包。")
    if not arguments.package_only:
        subprocess.run([
            sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
            "--distpath", str(ROOT / "dist"), "--workpath", str(ROOT / "work" / "pyinstaller"),
            str(ROOT / "TFT_Parameter_Analysis_System.spec"),
        ], cwd=ROOT, check=True)
    name = f"TFT参数分析系统_v{__version__}"
    executable = ROOT / "dist" / f"{name}.exe"
    if not executable.is_file():
        raise SystemExit(f"没有找到打包文件：{executable}")
    with tempfile.TemporaryDirectory(prefix="tft-release-") as staging:
        release = Path(staging) / f"{name}_Windows_x64"
        release.mkdir(parents=True, exist_ok=True)
        shutil.copy2(executable, release / executable.name)
        shutil.copy2(ROOT / "packaging" / "使用说明.txt", release / "使用说明.txt")
        for filename in ("SOURCE_DATA.md", "P_TYPE_DATA.md"):
            (release / "docs").mkdir(exist_ok=True)
            shutil.copy2(ROOT / "docs" / filename, release / "docs" / filename)
        shutil.copytree(ROOT / "data", release / "data", dirs_exist_ok=True)
        # 许可文本随程序分发；这里不会复制开发环境或构建工具的代码。
        license_directory = release / "licenses"
        license_directory.mkdir(exist_ok=True)
        for package in ("PySide6_Essentials", "PySide6_Addons", "shiboken6", "numpy", "scipy", "pandas",
                        "matplotlib", "openpyxl", "pillow", "contourpy", "cycler", "fonttools",
                        "kiwisolver", "packaging", "pyparsing", "python-dateutil", "six", "et_xmlfile", "tzdata"):
            distribution = metadata.distribution(package)
            for item in distribution.files or []:
                parts = item.parts
                if ".dist-info" in str(item) and any("license" in part.lower() or "copying" in part.lower()
                                                    for part in parts[1:]):
                    source = Path(distribution.locate_file(item))
                    if source.is_file():
                        target = license_directory / package / Path(*parts[1:])
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source, target)
        python_license = Path(sys.base_prefix) / "LICENSE.txt"
        if python_license.is_file():
            shutil.copy2(python_license, license_directory / "Python-LICENSE.txt")
        with executable.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        (release / "SHA256SUMS.txt").write_text(f"{digest}  {executable.name}\n", encoding="utf-8")
        archive = ROOT / "dist" / (release.name + ".zip")
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
            for path in sorted(release.rglob("*")):
                if path.is_file():
                    bundle.write(path, Path(release.name) / path.relative_to(release))
    print(f"EXE：{executable}\n分发压缩包：{archive}")


if __name__ == "__main__":
    main()
