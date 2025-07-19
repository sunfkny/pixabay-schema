import pathlib
import subprocess
import tomllib

with open("pyproject.toml", "rb") as f:
    project_name = tomllib.load(f)["project"]["name"]

print(f"Building {project_name}...")

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
        "UV_PYTHON_INSTALL_MIRROR=https://gh-proxy.com/github.com/astral-sh/python-build-standalone/releases/download",
        "--env",
        "UV_DEFAULT_INDEX=https://mirrors.aliyun.com/pypi/simple",
        "--env",
        "UV_INSTALLER_GITHUB_BASE_URL=https://gh-proxy.com/github.com",
        "--env",
        "UV_PYTHON_INSTALL_BIN=0",
        "--uv-install-script-windows",
        "https://gh-proxy.com/github.com/astral-sh/uv/releases/latest/download/uv-installer.ps1",
        "--uv-install-script-unix",
        "https://gh-proxy.com/github.com/astral-sh/uv/releases/latest/download/uv-installer.sh",
    ],
    check=True,
)
