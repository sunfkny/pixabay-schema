import pathlib
import subprocess
import tomllib
import typing


class UvIndex(typing.TypedDict):
    url: str
    default: typing.NotRequired[str]
    name: typing.NotRequired[str]


with open("pyproject.toml", "rb") as f:
    pyproject = tomllib.load(f)

project_name = pyproject["project"]["name"]
print(f"Building {project_name}...")

uv_index: list[UvIndex] = pyproject["tool"]["uv"]["index"]
uv_default_index = next(i for i in uv_index if "default" in i)["url"]

GITHUB_MIRROR = "https://gh-proxy.com//https://github.com"
UV_VERSION = "0.8.4"

subprocess.run(
    [
        "uvx",
        "pyfuze",
        "main.py",
        "--output-name",
        f"{project_name}.exe",
        "--pyproject",
        "pyproject.toml",
        "--uv-lock",
        "uv.lock",
        "--python",
        pathlib.Path(".python-version").read_text().strip(),
        "--mode",
        "online",
        "--unzip-path",
        f"{project_name}-data",
        "--env",
        "UV_PYTHON_INSTALL_BIN=0",
        "--env",
        f"UV_DEFAULT_INDEX={uv_default_index}",
        *(
            [
                "--env",
                f"UV_PYTHON_INSTALL_MIRROR={GITHUB_MIRROR}/astral-sh/python-build-standalone/releases/download",
                "--env",
                f"UV_INSTALLER_GITHUB_BASE_URL={GITHUB_MIRROR}",
                "--uv-install-script-windows",
                # f"{GITHUB_MIRROR}/astral-sh/uv/releases/latest/download/uv-installer.ps1",
                f"{GITHUB_MIRROR}/astral-sh/uv/releases/download/{UV_VERSION}/uv-installer.ps1",
                "--uv-install-script-unix",
                # f"{GITHUB_MIRROR}/astral-sh/uv/releases/latest/download/uv-installer.sh",
                f"{GITHUB_MIRROR}/astral-sh/uv/releases/download/{UV_VERSION}/uv-installer.sh",
            ]
            if GITHUB_MIRROR
            else []
        ),
    ],
    check=True,
)
