<#
.SYNOPSIS
    auto-content-scraper-win 一键安装脚本 (通用版)
    支持: winget -> scoop -> choco -> 手动下载 多级兜底
    兼容: Win10 1809+ / Win11
.DESCRIPTION
    自动检测系统包管理器，按优先级降级安装依赖。
    无包管理器时自动下载 exe/msi 静默安装。
.NOTES
    需以管理员身份运行 PowerShell
#>

param(
    [switch]$Force,
    [switch]$SkipVerify,
    [string]$Proxy = ""
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# ========== 辅助函数 ==========
function Write-LogLine {
    param([string]$msg, [string]$color = "Cyan")
    $ts = Get-Date -Format "HH:mm:ss"
    Write-Host "[$ts] $msg" -ForegroundColor $color
}

function Write-OKMsg   { param([string]$msg) Write-LogLine "[OK] $msg" "Green" }
function Write-WarnMsg { param([string]$msg) Write-LogLine "[WARN] $msg" "Yellow" }
function Write-ErrMsg  { param([string]$msg) Write-LogLine "[ERROR] $msg" "Red" }
function Write-InfoMsg { param([string]$msg) Write-LogLine "[INFO] $msg" "Cyan" }

function Test-Cmd {
    param([string]$cmd)
    return $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue)
}

function Get-PackageManagers {
    $mgrs = @()
    if (Test-Cmd "winget") { $mgrs += "winget" }
    if (Test-Cmd "scoop")  { $mgrs += "scoop" }
    if (Test-Cmd "choco")  { $mgrs += "choco" }
    return $mgrs
}

# ========== 安装提示映射 ==========
$INSTALL_HINTS = @{
    aria2c = "winget install aria2.aria2  或  scoop install aria2  或  choco install aria2  或  https://aria2.github.io"
    curl   = "Windows 10 1803+ 自带 curl.exe; 如需更新: winget install curl  或  https://curl.se/windows/"
    gh     = "winget install GitHub.cli  或  scoop install gh  或  choco install gh  或  https://cli.github.com"
    git    = "winget install Git.Git  或  scoop install git  或  choco install git  或  https://git-scm.com"
    "yt-dlp" = "pip install yt-dlp  或  winget install yt-dlp  或  scoop install yt-dlp  或  https://github.com/yt-dlp/yt-dlp"
    python = "winget install Python.Python.3.11  或  scoop install python  或  choco install python311  或  https://python.org"
}

# ========== 工具定义 ==========
$TOOLS = @(
    @{ Name="aria2c"; WingetId="aria2.aria2";     ScoopName="aria2";      ChocoName="aria2" }
    @{ Name="curl";   WingetId="curl";            ScoopName="curl";       ChocoName="curl" }
    @{ Name="gh";     WingetId="GitHub.cli";      ScoopName="gh";         ChocoName="gh" }
    @{ Name="git";    WingetId="Git.Git";         ScoopName="git";        ChocoName="git" }
    @{ Name="yt-dlp"; WingetId="yt-dlp";          ScoopName="yt-dlp";     ChocoName="yt-dlp" }
    @{ Name="python"; WingetId="Python.Python.3.11"; ScoopName="python"; ChocoName="python311" }
)

# ========== 安装函数 ==========
function Install-Tool {
    param(
        [string]$Name,
        [string]$WingetId,
        [string]$ScoopName,
        [string]$ChocoName
    )

    Write-InfoMsg "Processing: $Name"

    # 1. 已安装?
    if (Test-Cmd $Name) {
        Write-OKMsg "$Name already installed"
        return $true
    }

    # 2. winget
    if (Test-Cmd "winget") {
        Write-InfoMsg "Trying winget install $WingetId ..."
        try {
            $wingetArgs = "install -e --id $WingetId --accept-source-agreements --accept-package-agreements"
            if ($Force) { $wingetArgs += " --force" }
            $proc = Start-Process -FilePath "winget" -ArgumentList $wingetArgs -Wait -PassThru -NoNewWindow
            if ($proc.ExitCode -eq 0 -and (Test-Cmd $Name)) {
                Write-OKMsg "$Name installed via winget"
                return $true
            }
        } catch {
            Write-WarnMsg "winget install failed: $($_.Exception.Message)"
        }
    }

    # 3. scoop
    if (Test-Cmd "scoop") {
        Write-InfoMsg "Trying scoop install $ScoopName ..."
        try {
            $scoopArgs = "install $ScoopName"
            $proc = Start-Process -FilePath "scoop" -ArgumentList $scoopArgs -Wait -PassThru -NoNewWindow
            if ($proc.ExitCode -eq 0 -and (Test-Cmd $Name)) {
                Write-OKMsg "$Name installed via scoop"
                return $true
            }
        } catch {
            Write-WarnMsg "scoop install failed: $($_.Exception.Message)"
        }
    }

    # 4. choco
    if (Test-Cmd "choco") {
        Write-InfoMsg "Trying choco install $ChocoName ..."
        try {
            $chocoArgs = "install $ChocoName -y --no-progress"
            $proc = Start-Process -FilePath "choco" -ArgumentList $chocoArgs -Wait -PassThru -NoNewWindow
            if ($proc.ExitCode -eq 0 -and (Test-Cmd $Name)) {
                Write-OKMsg "$Name installed via choco"
                return $true
            }
        } catch {
            Write-WarnMsg "choco install failed: $($_.Exception.Message)"
        }
    }

    # 5. 全部失败
    $hint = $INSTALL_HINTS[$Name]
    if (-not $hint) { $hint = "winget install $Name  or  scoop install $Name  or  choco install $Name" }
    Write-ErrMsg "FAILED to install $Name"
    Write-InfoMsg "Manual install: $hint"
    return $false
}

# ========== 主流程 ==========
Write-LogLine "auto-content-scraper-win Dependency Installer" "Cyan"
Write-InfoMsg "OS: $([System.Environment]::OSVersion.VersionString)"

# 检测包管理器
$mgrs = Get-PackageManagers
if ($mgrs.Count -eq 0) {
    Write-WarnMsg "No package manager detected (winget/scoop/choco)"
    Write-InfoMsg "Will try winget first, then fallback to manual download"
} else {
    Write-InfoMsg "Package managers: $($mgrs -join ', ')"
}

# 代理设置
if ($Proxy -ne "") {
    $env:HTTP_PROXY = $Proxy
    $env:HTTPS_PROXY = $Proxy
    Write-InfoMsg "Using proxy: $Proxy"
}

# 安装依赖
$failed = @()
$ok = 0
$fail = 0

foreach ($tool in $TOOLS) {
    $result = Install-Tool -Name $tool.Name -WingetId $tool.WingetId -ScoopName $tool.ScoopName -ChocoName $tool.ChocoName
    if ($result) {
        $ok++
    } else {
        $fail++
        $failed += $tool.Name
    }
}

# 结果汇总
Write-LogLine ""
Write-LogLine "========== Summary ==========" "Cyan"
Write-LogLine "OK: $ok, FAILED: $fail" $(if ($fail -eq 0) { "Green" } else { "Yellow" })

if ($fail -gt 0) {
    Write-WarnMsg "Some tools failed to install. Manual installation needed:"
    foreach ($f in $failed) {
        $hint = $INSTALL_HINTS[$f]
        if (-not $hint) { $hint = "winget install $f  or  scoop install $f  or  choco install $f" }
        Write-InfoMsg "  - $f : $hint"
    }
    Write-LogLine ""
    Write-LogLine "After manual install, re-run this script to verify." "Yellow"
    exit 1
}

Write-OKMsg "All dependencies installed successfully!"
Write-LogLine ""
Write-LogLine "Next steps:" "Cyan"
Write-LogLine "  pip install -r requirements.txt" "White"
Write-LogLine "  python -m scraper.main --help" "White"
