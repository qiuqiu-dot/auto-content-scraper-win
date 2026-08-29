#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 专用工具模块：工具探测、安装引导、跨平台兼容层
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Dict


# ============================================================
# 核心工具：跨平台工具探测
# ============================================================

def find_tool(name: str, extra_paths: list = None) -> Optional[str]:
    """查找工具路径：PATH > 常见安装目录 > Windows 特有目录"""
    # 1. 标准 PATH 查找
    path = shutil.which(name)
    if path:
        return path

    # 2. 常见安装目录
    search_bases = [
        Path.home() / "scoop" / "apps" / name / "current" / "bin",
        Path.home() / "scoop" / "apps" / name / "current",
        Path(r"C:\Program Files") / name,
        Path(r"C:\Program Files (x86)") / name,
        Path(r"C:\ProgramData") / name,
        Path(os.environ.get("LOCALAPPDATA", "")) / name,
    ]

    if extra_paths:
        search_bases.extend(extra_paths)

    for base in search_bases:
        if not base.exists():
            continue
        for ext in (".exe", ".cmd", ".bat", ""):
            candidate = base / f"{name}{ext}"
            if candidate.exists():
                return str(candidate)

    return None


def find_tool_win(name: str) -> Optional[str]:
    """Windows 专用工具查找（包含 .exe/.cmd/.bat 后缀）"""
    # 优先用 shutil.which (已包含 PATHEXT)
    path = shutil.which(name)
    if path:
        return path

    # Windows 常见安装目录
    bases = [
        Path.home() / "scoop" / "apps",
        Path(r"C:\Program Files"),
        Path(r"C:\Program Files (x86)"),
        Path(os.environ.get("LOCALAPPDATA", "")),
        Path(r"C:\ProgramData"),
        Path(r"C:\Windows\System32"),
    ]

    for base in bases:
        if not base.exists():
            continue
        for ext in (".exe", ".cmd", ".bat", ""):
            candidate = base / f"{name}.exe"
            if candidate.exists():
                return str(candidate)

    return None


def find_tool_smart(name: str) -> Optional[str]:
    """智能查找：先标准 which，再 Windows 特有目录"""
    # 1. 标准 PATH
    path = shutil.which(name)
    if path:
        return path

    # 2. Windows 特有目录
    win_bases = [
        Path.home() / "scoop" / "apps",
        Path(r"C:\Program Files"),
        Path(r"C:\Program Files (x86)"),
        Path(os.environ.get("LOCALAPPDATA", "")),
        Path(r"C:\ProgramData"),
        Path(r"C:\Windows\System32"),
    ]

    for base in win_bases:
        if not base.exists():
            continue
        # 递归查找 (限制深度)
        for exe in base.rglob(f"{name}.exe"):
            if exe.is_file():
                return str(exe)
            # 限制深度避免遍历过深
            try:
                rel = exe.relative_to(base)
                if len(rel.parts) > 3:
                    continue
            except ValueError:
                pass

    return None


def find_tool_smart_cached(name: str, cache: dict = None) -> Optional[str]:
    """带缓存的工具查找"""
    if cache is None:
        cache = {}
    if name in cache:
        return cache[name]
    result = find_tool_smart(name)
    cache[name] = result
    return result


# ============================================================
# Windows 特有工具：注册表、注册表键值、环境变量
# ============================================================

def get_windows_version() -> dict:
    """获取 Windows 版本信息"""
    try:
        import platform
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "build": platform.win32_ver()[1],
            "architecture": platform.machine(),
        }
    except Exception:
        return {"system": "Windows", "release": "unknown"}


def is_windows_10_or_later() -> bool:
    """判断是否 Windows 10+ (内置 curl.exe)"""
    try:
        import platform
        version = platform.version()
        major = int(version.split(".")[0])
        build = int(version.split(".")[2]) if len(version.split(".")) > 2 else 0
        return major >= 10
    except Exception:
        return True  # 默认假设支持


def has_winget() -> bool:
    """检查 winget 是否可用"""
    return shutil.which("winget") is not None


def has_scoop() -> bool:
    return shutil.which("scoop") is not None


def has_choco() -> bool:
    return shutil.which("choco") is not None


def get_package_managers() -> list:
    """获取可用的包管理器"""
    managers = []
    if has_winget():
        managers.append("winget")
    if has_scoop():
        managers.append("scoop")
    if has_choco():
        managers.append("choco")
    return managers


# ============================================================
# 友好的工具安装引导
# ============================================================

TOOL_INSTALL_HINTS = {
    "aria2c": "winget install aria2.aria2  或  scoop install aria2  或  choco install aria2",
    "aria2": "winget install aria2.aria2  或  scoop install aria2",
    "yt-dlp": "pip install yt-dlp  或  winget install yt-dlp  或  scoop install yt-dlp",
    "gh": "winget install GitHub.cli  或  scoop install gh",
    "curl": "Windows 10 1803+ 自带 curl.exe；如版本太旧可 winget install curl",
    "aria2": "winget install aria2.aria2  或  scoop install aria2",
    "gh": "winget install GitHub.cli  或  scoop install gh",
    "yt-dlp": "pip install yt-dlp  或  winget install yt-dlp",
    "aria2c": "winget install aria2.aria2  或  scoop install aria2",
    "git": "winget install Git.Git  或  scoop install git",
    "python": "winget install Python.Python.3.11",
    "python3": "winget install Python.Python.3.11",
    "python3.11": "winget install Python.Python.3.11",
    "python3.12": "winget install Python.Python.3.12",
    "node": "winget install OpenJS.NodeJS  或  scoop install nodejs",
    "npm": "winget install OpenJS.NodeJS  (随 Node.js 安装)",
    "nodejs": "winget install OpenJS.NodeJS  或  scoop install nodejs",
    "python3": "winget install Python.Python.3.11",
    "python3.11": "winget install Python.Python.3.11",
    "python3.12": "winget install Python.Python.3.12",
    "ffmpeg": "winget install Gyan.FFmpeg  或  scoop install ffmpeg",
    "ffprobe": "winget install Gyan.FFmpeg  或  scoop install ffmpeg",
}


def get_install_hint(tool: str) -> str:
    """获取工具安装提示"""
    return TOOL_INSTALL_HINTS.get(tool.lower(), f"winget install {tool}  或  scoop install {tool}  或  choco install {tool}")


def ensure_tool(name: str, install_hint: str = "") -> str:
    """
    确保工具可用，否则抛出友好错误并给出安装建议
    """
    # 标准化工具名 (去掉 .exe 后缀)
    tool_name = name.lower().replace(".exe", "")

    # 查找工具
    path = shutil.which(name)
    if not path:
        path = find_tool_win(name)
    if not path:
        path = shutil.which(name)

    if path:
        return path

    hint = get_install_hint(name)
    raise RuntimeError(
        f"❌ 未找到命令: {name}\n"
        f"请先安装：\n"
        f"  winget install {name}\n"
        f"  scoop install {name}\n"
        f"  choco install {name}\n"
        f"  手动下载: https://github.com/{name}/{name}/releases"
    )


def find_tool(name: str) -> Optional[str]:
    """标准 PATH 查找"""
    return shutil.which(name)


def find_tool_win(name: str) -> Optional[str]:
    """Windows 常见目录查找"""
    name_lower = name.lower()
    if not name.endswith(".exe"):
        name_exe = name + ".exe"
    else:
        name_exe = name

    bases = [
        Path.home() / "scoop" / "apps",
        Path(r"C:\Program Files"),
        Path(r"C:\Program Files (x86)"),
        Path(os.environ.get("LOCALAPPDATA", "")),
        Path(r"C:\ProgramData"),
        Path(r"C:\Windows\System32"),
    ]

    for base in bases:
        if not base.exists():
            continue
        for ext in (".exe", ".cmd", ".bat", ""):
            candidate = base / f"{name}{ext}"
            if candidate.exists():
                return str(candidate)
    return None


def get_install_hint(tool: str) -> str:
    """获取工具安装提示"""
    return TOOL_INSTALL_HINTS.get(tool.lower(), f"winget install {tool}  或  scoop install {tool}  或  choco install {tool}")


# ============================================================
# 启动时自检：自动探测并给出友好提示
# ============================================================

def check_dependencies(required: list = None, optional: list = None) -> dict:
    """
    检查依赖工具是否可用
    返回: {tool: bool}
    """
    required = required or ["aria2c", "curl"]
    optional = optional or ["yt-dlp", "gh", "git"]

    results = {}
    for tool in required + optional:
        path = find_tool_smart(tool)
        results[tool] = path is not None
        if tool in required and not path:
            print(f"❌ 必需工具缺失: {tool}")
            print(f"  安装建议: {get_install_hint(tool)}")
        elif tool in optional and not path:
            print(f"⚠️ 可选工具缺失: {tool}")
            print(f"  安装建议: {get_install_hint(tool)}")
        else:
            print(f"✅ {tool}: OK")

    return results


def check_all_dependencies() -> dict:
    """完整依赖检查"""
    return check_dependencies(
        required=["aria2c", "curl"],
        optional=["yt-dlp", "gh", "git"]
    )


def get_install_script() -> str:
    """生成 Windows 一键安装脚本内容"""
    return '''@echo off
echo 正在安装 auto-content-scraper 依赖...
echo.

:: 检查 winget
where winget >nul 2>nul
if errorlevel 1 (
    echo [ERROR] 未检测到 winget，请升级 Windows 10 到 1809+ 或手动安装
    pause
    exit /b 1
)

echo 正在安装依赖工具...
winget install -e --id aria2.aria2 --accept-source-agreements --accept-package-agreements
winget install --id GitHub.cli -e --accept-source-agreements --accept-package-agreements
winget install --id Python.Python.3.11 -e --accept-source-agreements --accept-package-agreements
winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements

echo.
echo 依赖安装完成！
echo 验证安装：
aria2c --version
curl --version
gh --version
python --version
pause
'''


def get_install_script_path() -> Path:
    """获取安装脚本路径"""
    return Path(__file__).parent / "scripts" / "install-windows.ps1"


def write_install_script(path: Optional[Path] = None) -> Path:
    """写入 Windows 安装脚本"""
    if path is None:
        path = Path(__file__).parent.parent / "scripts" / "install-windows.ps1"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(get_install_script())
    return path


# ============================================================
# 导出
# ============================================================

__all__ = [
    "find_tool",
    "find_tool_win",
    "find_tool_smart",
    "find_tool_smart_cached",
    "ensure_tool",
    "get_install_hint",
    "ensure_tool",
    "check_dependencies",
    "check_all_dependencies",
    "get_install_script",
    "write_install_script",
    "get_install_script_path",
    "is_windows_10_or_later",
    "has_winget",
    "has_scoop",
    "has_choco",
    "get_package_managers",
    "get_windows_version",
]
