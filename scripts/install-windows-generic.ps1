<#
.SYNOPSIS
    auto-content-scraper-win 一键安装脚本
    用 curl -o 下载 aria2，用 pip 安装 yt-dlp
.NOTES
    需以管理员身份运行 PowerShell
#>

# ===== 关键：强制 UTF-8 编码，防止中文乱码 =====
chcp 65001 >$null
$OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'utf-8'

param([string]$Proxy = "")

$ErrorActionPreference = "Stop"

function Write-OK   { param([string]$msg) Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Info { param([string]$msg) Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Err  { param([string]$msg) Write-Host "[ERROR] $msg" -ForegroundColor Red }

# 代理
if ($Proxy -ne "") {
    $env:HTTP_PROXY = $Proxy
    $env:HTTPS_PROXY = $Proxy
    Write-Host "[INFO] Using proxy: $Proxy" -ForegroundColor Cyan
}

# ========== 1. curl (Win10 1803+ 自带) ==========
Write-Host "[INFO] Checking curl..." -ForegroundColor Cyan
$curl = Get-Command curl -ErrorAction SilentlyContinue
if ($curl) {
    Write-Host "[OK] curl OK: $($curl.Source)" -ForegroundColor Green
} else {
    Write-Err "curl not found. Windows 10 1803+ required."
    exit 1
}

# ========== 2. Python ==========
Write-Host "[INFO] Checking Python..." -ForegroundColor Cyan
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-OK "Python OK"
} else {
    Write-Err "Python not found. Please install: https://python.org"
    Write-Info "Or: winget install Python.Python.3.11"
    exit 1
}

# ========== 2. aria2 ==========
Write-Info "Checking aria2c..."
if (Get-Command aria2c -ErrorAction SilentlyContinue) {
    Write-OK "aria2c OK"
} else {
    Write-Info "Downloading aria2 via curl..."
    $url = "https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip"
    $zip = "$env:TEMP\aria2.zip"
    $dest = "$env:LOCALAPPDATA\aria2"
    
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

# ========== 4. yt-dlp ==========
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

# ========== 5. gh (可选) ==========
Write-Info "Checking gh..."
if (Get-Command gh -ErrorAction SilentlyContinue) {
    Write-OK "gh OK"
} else {
    Write-Info "gh not found (optional, for GitHub features)"
    Write-Info "Install: winget install GitHub.cli"
}

# ========== 6. Python 依赖 ==========
Write-Info "Installing Python dependencies..."
& python -m pip install requests beautifulsoup4 lxml
if ($LASTEXITCODE -eq 0) {
    Write-OK "Python dependencies OK"
} else {
    Write-Err "Failed to install Python dependencies"
}

# ========== Summary ==========
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
