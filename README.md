# Auto Content Scraper - Windows 版

自动抓取「网上优质内容 / 资源站 / 下载站」的程序。
通过 **Bing 搜索** 或 **手动输入网址** 发现/抓取内容，结合 **信誉站白名单库** 与启发式打分做可信度评估，
并支持 **aria2 多线程下载** 页面中的文件链接。结果导出为 JSON / CSV / HTML 报告。

## ⚠️ 重要免责声明

> **⚠️ 重要法律声明：**
>
> 本工具仅供**技术研究、学习交流、个人合法内容归档**使用。
>
> **严禁**使用本工具下载、传播、传播任何：
> - 受版权保护且未获授权的内容（影视、音乐、软件、游戏、电子书等）
> - 违反网站服务条款（ToS）的内容
> - 网站明确禁止爬取/下载的内容（robots.txt 禁止、登录墙后内容、付费内容等）
> - 违反《中华人民共和国著作权法》及相关法律法规的内容
> - 任何违反网站服务条款、违反法律法规的内容
>
> **使用者承诺：**
> - 仅对合法授权、公共领域、CC 协议开放内容、或已获得授权的内容进行抓取/下载
> - 遵守目标网站的 `robots.txt`、服务条款、使用条款
> - 遵守《中华人民共和国著作权法》、《计算机软件保护条例》、《网络安全法》等相关法律法规
> - 不将获取的内容用于商业用途、二次分发、非法传播
>
> **违规责任自负：** 因违规使用本工具导致的任何法律后果、民事赔偿、刑事责任，**完全由使用者自行承担**，开发者不承担任何连带责任。
>
> **技术中立原则：** 本工具仅提供技术手段，**不提供、不传播、不存储任何违规内容**。技术本身中立，用途由使用者决定，后果由使用者自负。

---

## 功能

- 🔍 **Bing 搜索**：多关键字批量搜索，自动解析自然结果（标题、URL、摘要），支持翻页。
- 🔗 **手动网址抓取**：直接输入一个或多个网址抓取，无需搜索。
- 🏅 **信誉评估**：内置 90+ 个信誉较好的下载/资源/官方站白名单；站外站点按域名 + 页面内容启发式打分（自动识别盗版/破解/广告站降分）。
- 📦 **内容抓取**：抽取正文、标题、meta、链接与下载链接；遵循限速、超时重试；robots.txt 默认关闭以增强可用性（可 `--respect-robots` 开启）。
- ⚡ **aria2 多线程下载**：把页面/结果里识别到的文件链接交给 aria2c，用 `-x/-s` 指定分段线程数高速下载，支持 yt-dlp 视频下载。
- 📄 **导出**：JSON 全量 + CSV 摘要 + 自包含 HTML 可视化报告。

## 核心工作流：搜索 → 抓取 → 评分 → 下载 → 导出（一条龙）

```bash
# 一条命令完成：搜索 → 抓取 → 评分 → 多线程下载 → 保存报告
python -m scraper.main \
  -q "软件下载站 推荐" \
  -q "linux 发行版 iso" \
  -m 20 \
  -r 10 \
  --download \
  --threads 16 \
  --ytdlp \
  -f
```

## 目录结构

```
auto-content-scraper-win/
├── scraper/
│   ├── __init__.py
│   ├── main.py          # 命令行入口
│   ├── bing_search.py   # Bing 搜索结果解析
│   ├── sites.py         # 信誉白名单库 + 域名/类型判定
│   ├── fetch.py         # HTTP 抓取（robots、限速、UA、重试）
│   ├── reputation.py    # 信誉打分与过滤
│   ├── content.py       # 正文/链接/元信息/下载链接抽取
│   ├── aria2.py         # aria2 多线程下载 + 兜底下载
│   ├── github_tools.py  # GitHub 克隆/发行版/搜索
│   └── win_utils.py     # Windows 专用工具（工具探测、安装引导、兼容层）
├── scripts/
│   └── install-windows.ps1  # Windows 一键安装脚本
├── requirements.txt
├── setup.py
└── README.md
```

## 安装

```bash
cd auto-content-scraper-win
pip install requests beautifulsoup4 lxml
# aria2 下载（按系统）：
#   Windows: 请参考下方 Windows 专用安装指南
#   Linux:  apt/brew install aria2
#   macOS:  brew install aria2
```

## Windows 专用安装指南

### 系统要求
- Windows 10 1809+ (内置 curl.exe) 或 Windows 11
- Python 3.10+

### 一键安装依赖（推荐，需管理员权限）

```powershell
# 右键“以管理员身份运行” PowerShell，执行：
irm https://raw.githubusercontent.com/qiuqiu-dot/auto-content-scraper-win/main/scripts/install-windows-generic.ps1 | iex
```

或手动运行脚本：
```powershell
# 右键“以管理员身份运行” PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\scripts\install-windows.ps1
```

### 手动安装依赖（可选）

```powershell
# 1. 安装 aria2 (下载工具核心)
winget install aria2.aria2

# 2. 安装 GitHub CLI (GitHub 专区功能需要)
winget install GitHub.cli

# 3. 确保 Python 3.10+
winget install Python.Python.3.11

# 4. 可选：yt-dlp (视频下载)
pip install yt-dlp
# 或
winget install yt-dlp

# 4. 验证
aria2c --version
curl --version
gh --version
python --version
```

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| `aria2c: command not found` | 运行 `winget install aria2.aria2` 或 `scoop install aria2` |
| `curl` 版本太旧 | Win10 1803+ 自带 `curl.exe`，若版本太旧请更新 Windows 或 `winget install curl` |
| `gh` 认证失败 | 运行 `gh auth login` 按提示完成 |
| 权限错误 | 右键“以管理员身份运行” PowerShell |

## 使用方法

### 核心工作流：搜索 → 抓取 → 评分 → 下载 → 导出（一条龙）

```bash
# 一条命令完成：搜索 → 抓取 → 评分 → 多线程下载 → 保存报告
python -m scraper.main \
  -q "软件下载站 推荐" \
  -q "linux 发行版 iso" \
  -m 20 \
  -r 10 \
  --download \
  --threads 16 \
  --ytdlp \
  -f
```

### 1) Bing 搜索抓取资源站
```bash
python -m scraper.main                                             # 默认关键字
python -m scraper.main --interactive                               # 交互输入关键字
python -m scraper.main -q "下载站 推荐" -q "linux 发行版 iso" -m 20  # 多关键字
```

### 2) 手动输入网址抓取
```bash
python -m scraper.main --url https://example.com/download          # 抓单个网址
python -m scraper.main --url https://a.com/ --url https://b.com/   # 多个网址
python -m scraper.main --url-file urls.txt                         # 每行一个网址
```

### 3) aria2 多线程下载
```bash
# 抓取下载页并自动把页内文件链接交给 aria2，16 线程分段下载
python -m scraper.main --url https://example.com/downloadpage --download --threads 16

# 从之前生成的 scrape.json 提取下载链接批量下载
python -m scraper.main --download-json results/20260817_xxx/scrape.json --threads 16
```

### 组合参数速查表

| 阶段 | 参数 | 说明 | 示例 |
|------|------|------|------|
| **搜索** | `-q`, `--query` | 搜索关键字（可多次） | `-q "下载站" -q "iso 镜像"` |
| | `-r`, `--results` | 每关键字 Bing 结果条数 | `-r 10` |
| | `--interactive` | 交互式输入关键字 | `--interactive` |
| **抓取** | `-m`, `--max-sites` | 最大抓取评估站点数 | `-m 20` |
| | `--reputable-only` | yes/no/judge 过滤模式 | `--reputable-only judge` |
| | `--min-score` | 最低信用分 (0-100) | `--min-score 40` |
| | `--delay` / `-d` | 抓取间隔秒（限速） | `-d 1.5` |
| | `--timeout` | 每页超时秒 | `--timeout 12` |
| | `--respect-robots` | 遵守 robots.txt | `--respect-robots` |
| **下载** | `--download` | 启用下载 | `--download` |
| | `--threads` / `-t` | aria2 线程数 (-x/-s) | `-t 16` |
| | `--ytdlp` | 启用 yt-dlp 视频下载 | `--ytdlp` |
| | `--ytdlp-format` | yt-dlp 格式 | `--ytdlp-format "bestvideo+bestaudio/best"` |
| | `--dl-out` | 下载输出目录 | `--dl-out ./downloads` |
| **离线下载** | `--download-json` | 从已有 scrape.json 下载 | `--download-json results/xxx/scrape.json` |
| **导出** | `-f`, `--save` | 保存到文件（JSON/CSV/HTML） | `-f` |
| | `--output`, `-o` | 输出根目录 | `-o ./output` |

### 常用组合示例

```bash
# 1) 搜索 + 下载 + 保存报告（最常用）
python -m scraper.main -q "软件下载站 推荐" -q "linux 发行版 iso" -m 20 -r 10 --download --threads 16 --ytdlp -f

# 2) 仅搜索 + 保存报告（不下载）
python -m scraper.main -q "下载站 推荐" -f

# 3) 手动 URL + 下载
python -m scraper.main --url "https://example.com/download" --download --threads 16

# 4) 批量 URL 文件 + 下载
python -m scraper.main --url-file urls.txt --download --threads 16

# 4) 离线下载（从已有结果 JSON 下载）
python -m scraper.main --download-json results/20260817_xxx/scrape.json --threads 16 --ytdlp

# 5) 交互模式（菜单选择）
python -m scraper.main --interactive
```

### 交互模式菜单
```
==== 交互模式 ====
  1) 搜索并抓取资源站 (Bing)
  2) GitHub 专区 (克隆/发行版/搜索)
  3) 手动输入网址抓取
  请选择模式 [1-3]:
```

### 输出

- `results/<时间戳>/scrape.json` — 全量结构化数据
- `results/<时间戳>/scrape.csv` — 站点摘要（Excel 友好）
- `results/<时间戳>/report.html` — 自包含可视化报告（双击打开）
- `downloads/` — aria2 下载的文件（可用 `--dl-out` 改目录）

## 说明与合规

- 下载由 aria2c 执行：`-xN` 每服务器并发连接、`-sN` 分段数，二者通常都设为 `--threads N`。
  aria2c 未安装时自动退化为 Python 内置单线程下载（会明确提示）。
- 请遵守目标网站 robots.txt 与使用条款，控制速率；本程序仅用于个人学习/研究。
- Bing 可能对高频请求返回验证码，遇到请降低频率或稍后再试。

---

## ⚠️ 再次强调免责声明

**本工具仅供技术研究、学习交流、个人合法内容归档使用。**

**严禁使用本工具下载、传播任何：**
- 受版权保护且未获授权的内容
- 违反网站服务条款的内容
- 网站明确禁止爬取/下载的内容
- 违反《中华人民共和国著作权法》及相关法律法规的内容

**违规责任完全由使用者自行承担，开发者不承担任何连带责任。**

**技术中立，用途自负。请合法合规使用。**
