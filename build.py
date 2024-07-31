# @Author: Bi Ying
# @Date:   2024-07-31 22:04:47
import os
import shlex
import shutil
import argparse
import platform
import subprocess
from pathlib import Path


def run_cmd(cmd: str, split=False):
    """
    Run command in shell
    """
    if split:
        cmd = shlex.split(cmd)
    return subprocess.run(cmd, shell=True)


def build_production():
    version = os.environ["PDF_VISUALIZE_TRANSLATE_VERSION"]
    run_cmd("pyinstaller main.spec --noconfirm", split=False)
    # Create a version file in ./dist/pdf-visualize-translate/
    version_txt_path = Path("./dist/pdf-visualize-translate/version.txt")
    if not version_txt_path.parent.exists():
        version_txt_path.parent.mkdir(parents=True, exist_ok=True)
    with open("./dist/pdf-visualize-translate/version.txt", "w") as f:
        f.write(version)

    system_name = platform.system().lower()
    if system_name == "darwin":
        platform_name = "mac"
    elif system_name == "windows":
        platform_name = "windows"
    else:
        platform_name = "linux"

    # Create the ZIP file
    zip_filename = f"pdf-visualize-translate-{platform_name}-v{version}.zip"
    zip_filepath = Path(f"./dist/{zip_filename}")

    # Compress the directory
    shutil.make_archive(
        base_name=zip_filepath.with_suffix(""), format="zip", root_dir="./dist", base_dir="pdf-visualize-translate"
    )

    print(f"Created {zip_filename} at {zip_filepath}")


parser = argparse.ArgumentParser(description="Build software.")
parser.add_argument(
    "-t", "--type", default="production", help="build type: development(d) or production(p) or frontend(f)"
)
args = parser.parse_args()
if args.type == "p" or args.type == "production":
    build_production()
