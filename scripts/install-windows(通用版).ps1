<# 
.SYNOPSIS
    auto-content-scraper-win 一键安装脚本
    支持：winget → scoop → choco → 手动下载 多级兜底
    兼容：Win10 1809+ / Win11
#>

param(
    [switch]$Force,           # 强制重装
    [switch]$SkipVerify,      # 跳过哈希校验
    [string]$Proxy = ""       # 代理
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# ========== 颜色输出 ==========
function Write-Log { param($msg, $color='Cyan') { Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $msg" -ForegroundColor $color } }
function Write-OK   { param($msg) { Write-Log "✅ $msg" 'Green' } }
function Write-Warn { param($msg) { Write-Log "⚠ $msg"  'Yellow' } }
function Write-Err  { param($msg) { Write-Log "❌ $msg"   'Red' } }
function Write-Info { param($msg) { Write-Log "ℹ $msg"    'Cyan' } }

# ========== 工具函数 ==========
function Test-Command { param($cmd) (Get-Command $_.Name -ErrorAction SilentlyContinue) -ne $null }

function Get-PackageManagers {
    $mgrs = @()
    if (Get-Command winget -ea 0) { $mgrs += 'winget' }
    if (Get-Command scoop -ea 0)  { $mgrs += 'scoop' }
    if (Get-Command choco -ea 0)  { $mgrs += 'choco' }
    return $mgrs
}

function Install-WithFallback {
    param(
        [string]$Name,
        [string]$WingetId,
        [string]$ScoopName,
        [string]$ChocoName,
        [string]$DownloadUrl,
        [string]$ExeName,
        [string[]]$InstallArgs = @(),
        [string]$VerifyCmd
    )

    Write-Info "📦 正在处理: $Name"

    # 1. 已安装？
    if (Get-Command $_.Name -ea 0) { Write-OK "$Name 已安装"; return $true }

    # 2. 尝试各包管理器
    $managers = @('winget', 'scoop', 'choco')
    foreach ($mgr in $managers) {
        if (-not (Get-Command $mgr -ea 0)) { continue }
        try {
            $id = @{
                winget = $WingetId
                scoop  = $ScoopName
                choco  = $ChocoName
            }[$_.Name.ToLower()]

            if ($_) {
                Write-Info "📦 尝试用 $mgr 安装 $Name..."
                $args = @('install', '-e', '--id', $_, '--accept-source-agreements', '--accept-package-agreements')
                if ($_ -eq 'scoop') { $args = 'install', $_, '--accept' }
                if ($_ -eq 'choco') { $args = 'install', $_, '-y', '--no-progress' }

                $proc = Start-Process -FilePath $_ -ArgumentList $args -Wait -PassThru -NoNewWindow
                if ($proc.ExitCode -eq 0 -and (Get-Command $_.Name -ea 0)) {
                    Write-OK "$Name 安装成功 (via $mgr)"
                    return $true
                }
            }
        } catch {
            Write-Warn "$mgr 安装 $Name 失败: $($_.Exception.Message)"
        }
    }

    # 4. 兜底：手动下载
    if ($DownloadUrl) {
        Write-Warn "包管理器均失败，尝试手动下载安装..."
        try {
            $tmp = "$env:TEMP\$ExeName"
            Write-Info "⬇️ 下载: $DownloadUrl"
            Invoke-WebRequest -Uri $DownloadUrl -OutFile $tmp -UseBasicParsing
            $proc = Start-Process -FilePath $tmp -ArgumentList '/S', '/quiet', '/norestart' -Wait -PassThru
            if ($proc.ExitCode -eq 0 -and (Get-Command $ExeName -ea 0)) {
                Write-OK "手动安装成功"
                return $true
            }
        } catch {
            Write-Err "手动安装失败: $($_.Exception.Message)"
        }
    }

    Write-Err "❌ $Name 所有安装方式均失败"
    return $false
}

# ========== 主流程 ==========
Write-Log "🚀 auto-content-scraper-win 依赖安装器"
Write-Info "检测环境: $(Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion)"

# 1. 检测包管理器
$mgrs = Get-PackageManagers
if ($mgrs.Count -eq 0) {
    Write-Warn "⚠️ 未检测到任何包管理器 (winget/scoop/choco)"
    Write-Info "将尝试直接下载安装..."
}

# 2. 安装核心依赖
$tools = @(
    @{ Name='aria2c';      WingetId='aria2.aria2';     ScoopName='aria2';      ChocoName='aria2';      ExeName='aria2c';     VerifyCmd='aria2c --version' },
    @{ Name='curl';        WingetId='curl';            ScoopName='curl';       ChocoName='curl';       ExeName='curl';       VerifyCmd='curl --version' },
    @{ Name='gh';          WingetId='GitHub.cli';      ScoopName='gh';         ChocoName='gh';         ExeName='gh';         VerifyCmd='gh --version' },
    @{ Name='git';         WingetId='Git.Git';         ScoopName='git';        ChocoName='git';        ExeName='git';        VerifyCmd='git --version' },
    @{ Name='yt-dlp';      WingetId='yt-dlp';          ScoopName='yt-dlp';     ChocoName='yt-dlp';     ExeName='yt-dlp';     VerifyCmd='yt-dlp --version' },
    @{ Name='python';      WingetId='Python.Python.3.11'; ScoopName='python'; ChocoName='python311'; ExeName='python';    VerifyCmd='python --version' }
)

$failed = @()
foreach ($tool in $tools) {
    if (-not (Install-WithFallback @tool)) {
        $failed += $tool.Name
    }
}

# 结果汇总
Write-Log "`n========== 安装结果汇总 =========="
$ok = 0; $fail = 0
foreach ($t in $tools) {
    if (Get-Command $t.Name -ea 0) { Write-OK "$($t.Name): OK"; $ok++ }
    else { Write-Err "$($t.Name): 失败"; $fail++ }
}
Write-Log "成功: $ok, 失败: $fail"

if ($fail -gt 0) {
    Write-Warn "部分工具安装失败，请手动处理："
    $failed | ForEach-Object { Write-Info "  - $_: $($TOOL_INSTALL_HINTS[$_])" }
    exit 1
}

Write-OK "🎉 所有依赖安装完成！"
