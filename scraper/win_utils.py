#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 专用工具模块：工具探测、安装引导、跨平台兼容层
"""
from __future__ import annotations

import os
import re
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

    # 2. 常见安装目录 (非递归，避免遍历过深)
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

    # Windows 常见安装目录 (仅一级子目录，不递归)
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
        # 只查找已知的包子目录，避免全盘扫描
        for subdir in base.iterdir():
            if not subdir.is_dir():
                continue
            for ext in (".exe", ".cmd", ".bat", ""):
                candidate = subdir / f"{name}{ext}"
                if candidate.exists():
                    return str(candidate)
    return None


def find_tool_smart(name: str) -> Optional[str]:
    """智能查找：先标准 which，再 Windows 特有目录 (非递归)"""
    # 1. 标准 PATH
    path = shutil.which(name)
    if path:
        return path

    # 2. Windows 特有目录 (非递归，仅检查已知包目录)
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
        for subdir in base.iterdir():
            if not subdir.is_dir():
                continue
            for ext in (".exe", ".cmd", ".bat", ""):
                candidate = subdir / f"{name}{ext}"
                if candidate.exists():
                    return str(candidate)
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


def aria2_available() -> bool:
    """检查 aria2c 是否可用"""
    return shutil.which("aria2c") is not None or find_tool_smart("aria2c") is not None


def ytdlp_available() -> bool:
    """检查 yt-dlp 是否可用"""
    return shutil.which("yt-dlp") is not None or find_tool_smart("yt-dlp") is not None


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
# 文件名安全处理
# ============================================================

# Windows 非法文件名字符 (不包括点号，点号单独处理)
INVALID_FILENAME_CHARS = r'[\\/:*?"<>|]'
INVALID_FILENAME_RE = re.compile(INVALID_FILENAME_CHARS)


def sanitize_filename(name: str, max_len: int = 255) -> str:
    """清理文件名中的非法字符，防止路径遍历攻击。"""
    # 替换非法字符 (保留点号)
    name = INVALID_FILENAME_RE.sub('_', name)
    # 去除首尾空格
    name = name.strip(' ')
    # 去除首尾点号 (但保留中间的点号用于扩展名)
    name = name.strip('.')
    # 截断过长文件名
    if len(name) > max_len:
        base, ext = os.path.splitext(name)
        name = base[:max_len - len(ext)] + ext
    # 空文件名兜底
    if not name:
        name = "download"
    return name


# ============================================================
# 友好的工具安装引导
# ============================================================

TOOL_INSTALL_HINTS = {
    "aria2c": "winget install aria2.aria2  或  scoop install aria2  或  choco install aria2",
    "aria2": "winget install aria2.aria2  或  scoop install aria2",
    "yt-dlp": "pip install yt-dlp  或  winget install yt-dlp  或  scoop install yt-dlp",
    "gh": "winget install GitHub.cli  或  scoop install gh",
    "curl": "Windows 10 1803+ 自带 curl.exe；如版本太旧可 winget install curl",
    "git": "winget install Git.Git  或  scoop install git",
    "python": "winget install Python.Python.3.11",
    "python3": "winget install Python.Python.3.11",
    "python3.11": "winget install Python.Python.3.11",
    "python3.12": "winget install Python.Python.3.12",
    "node": "winget install OpenJS.NodeJS  或  scoop install nodejs",
    "npm": "winget install OpenJS.NodeJS  (随 Node.js 安装)",
    "nodejs": "winget install OpenJS.NodeJS  或  scoop install nodejs",
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

    if path:
        return path

    hint = get_install_hint(name)
    raise RuntimeError(
        f"❌ 未找到命令: {name}\n"
        f"请先安装：\n"
        f"  winget install {name}\n"
        f"  scoop install {name}\n"
        f"  choco install {name}\n"
        f"  或访问官方网站下载"
    )


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
    """生成 Windows 一键安装脚本内容 (PowerShell 版)"""
    return '''# auto-content-scraper-win 一键安装脚本
# 需以管理员身份运行 PowerShell

chcp 65001 >$null
$OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

function Write-OK   { param([string]$msg) Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Info { param([string]$msg) Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Err  { param([string]$msg) Write-Host "[ERROR] $msg" -ForegroundColor Red }

# 1. curl (Win10 1803+ 自带)
Write-Info "Checking curl..."
if (Get-Command curl -ErrorAction SilentlyContinue) {
    Write-OK "curl OK"
} else {
    Write-Err "curl not found. Windows 10 1803+ required."
    exit 1
}

# 2. Python
Write-Info "Checking Python..."
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-OK "Python OK"
} else {
    Write-Err "Python not found. Please install: https://python.org"
    Write-Info "Or: winget install Python.Python.3.11"
    exit 1
}

# 3. aria2
Write-Info "Checking aria2c..."
if (Get-Command aria2c -ErrorAction SilentlyContinue) {
    Write-OK "aria2c OK"
} else {
    Write-Info "Downloading aria2 via curl..."
    $url = "https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip"
    $zip = "$env:TEMP\\aria2.zip"
    $dest = "$env:LOCALAPPDATA\\aria2"
    
    & curl -L -o $zip $url
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Failed to download aria2"
        Write-Info "Manual download: $url"
        exit 1
    }
    
    if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
    Expand-Archive -Path $zip -DestinationPath $dest -Force
    Remove-Item $zip -Force
    
    $exe = Get-ChildItem $dest -Recurse -Filter "aria2c.exe" | Select-Object -First 1
    if ($exe) {
        $dir = $exe.DirectoryName
        $userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
        if ($userPath -notlike "*$dir*") {
            [Environment]::SetEnvironmentVariable("PATH", "$userPath;$dir", "User")
            $env:PATH += ";$dir"
        }
        Write-OK "aria2c installed to: $dir"
    } else {
        Write-Err "aria2c.exe not found in archive"
        exit 1
    }
}

# 4. yt-dlp
Write-Info "Checking yt-dlp..."
if (Get-Command yt-dlp -ErrorAction SilentlyContinue) {
    Write-OK "yt-dlp OK"
} else {
    Write-Info "Installing yt-dlp via pip..."
    & python -m pip install yt-dlp
    if ($LASTEXITCODE -eq 0) {
        Write-OK "yt-dlp installed"
    } else {
        Write-Err "pip install yt-dlp failed"
        Write-Info "Try: python -m pip install --user yt-dlp"
    }
}

# 5. gh (可选)
Write-Info "Checking gh..."
if (Get-Command gh -ErrorAction SilentlyContinue) {
    Write-OK "gh OK"
} else {
    Write-Info "gh not found (optional, for GitHub features)"
    Write-Info "Install: winget install GitHub.cli"
}

# 6. Python 依赖
Write-Info "Installing Python dependencies..."
& python -m pip install requests beautifulsoup4 lxml
if ($LASTEXITCODE -eq 0) {
    Write-OK "Python dependencies OK"
} else {
    Write-Err "Failed to install Python dependencies"
}

# Summary
Write-Host ""
Write-Host "========== Summary ==========" -ForegroundColor Cyan
$tools = @("curl", "python", "aria2c", "yt-dlp", "gh")
foreach ($t in $tools) {
    if (Get-Command $t -ErrorAction SilentlyContinue) {
        Write-OK "$t"
    } else {
        Write-Err "$t (missing)"
    }
}
Write-Host ""
Write-OK "Done! Run: python -m scraper.main --help"
'''


def get_install_script_path() -> Path:
    """获取安装脚本路径"""
    return Path(__file__).parent.parent / "scripts" / "install-windows.ps1"


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
    "aria2_available",
    "ytdlp_available",
    "sanitize_filename",
]
