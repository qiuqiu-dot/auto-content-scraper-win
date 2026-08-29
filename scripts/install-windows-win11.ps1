@echo off
echo 正在安装 auto-content-scraper-win 依赖...
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
EOF
