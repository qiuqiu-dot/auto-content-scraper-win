# -*- coding: utf-8 -*-
"""Bing 搜索结果解析模块 (Windows 兼容版)。

通过 requests 抓取 Bing 的 HTML 搜索结果页，用 BeautifulSoup 解析自然结果
（标题、URL、摘要）。支持翻页（first=N）和多关键字批量搜索。

说明：Bing 可能对高频请求返回验证码或改变 DOM 结构，本模块尽量稳健地解析，
并对失败情况给出清晰提示。
"""
from __future__ import annotations

import re
import time
import urllib.parse
from dataclasses import dataclass, field
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

BING = "https://www.bing.com/search"


@dataclass
class BingResult:
    """一条 Bing 自然搜索结果。"""
    title: str
    url: str
    snippet: str = ""
    position: int = 0
    source: str = "bing"
    extra: dict = field(default_factory=dict)


def build_url(query: str, page: int = 1, lang: str = "zh-CN") -> str:
    """构造 Bing 搜索 URL。page 从 1 开始。"""
    first = (page - 1) * 10 + 1
    params = {
        "q": query,
        "first": first,
        "setlang": "zh-hans",
        "mkt": lang,
    }
    return BING + "?" + urllib.parse.urlencode(params)


def _is_nav_or_ads(href: str) -> bool:
    """过滤掉导航/广告/以及明显的 BING 内跳转链接。"""
    if not href:
        return True
    low = href.lower()
    if low.startswith("javascript:"):
        return True
    if href == "#" or href == "":
        return True
    # Bing 内部链接（搜索、登录、设置等）
    if "bing.com" in low and ("search" in low or "signin" in low or "preferences" in low or "maps" in low):
        return True
    if "microsoft.com" in low and ("account" in low or "login" in low):
        return True
    return False


_BING_REDIR = re.compile(r"bing\.com/ck/a\?.*?[&?]u=([^&]+)", re.I)


def _decode_bing_redirect(url: str) -> str:
    """解码 Bing 的 /ck/a 跳转链接中真实 URL。"""
    m = _BING_REDIR.search(url)
    if m:
        encoded = m.group(1) or ""
        try:
            import base64
            pad = encoded + "=" * (-len(encoded) % 4)
            decoded = base64.b64decode(pad).decode("utf-8", errors="ignore")
            decoded = urllib.parse.unquote(decoded)
            decoded = urllib.parse.unquote(decoded)
            if decoded.startswith("http"):
                return decoded
        except Exception:
            pass
    return url


def parse_html(html: str) -> List[BingResult]:
    """从 Bing 搜索结果 HTML 中解析出自然结果列表。"""
    soup = BeautifulSoup(html, "lxml")
    results: List[BingResult] = []
    # Bing 结果项常见的定位方式：<li class="b_algo">
    for li in soup.select("li.b_algo"):
        h2 = li.find("h2")
        if not h2:
            continue
        a = h2.find("a", href=True)
        if not a:
            continue
        raw_href = a.get("href", "")
        if _is_nav_or_ads(raw_href):
            continue
        url = _decode_bing_redirect(raw_href)
        title = " ".join(a.get_text(" ", strip=True).split())
        # 摘要
        cap = li.select_one("p") or li.select_one("div.b_caption p")
        snippet = ""
        if cap:
            snippet = " ".join(cap.get_text(" ", strip=True).split())
        results.append(
            BingResult(title=title, url=url, snippet=snippet, position=len(results) + 1)
        )
    if not results:
        # 兜底：某些布局下用 .b_results > li
        for li in soup.select(".b_results > li"):
            a = li.find("a", href=True)
            if not a:
                continue
            raw_href = a.get("href", "")
            if _is_nav_or_ads(raw_href):
                continue
            url = _decode_bing_redirect(raw_href)
            title = " ".join(a.get_text(" ", strip=True).split())
            cap = li.select_one("p")
            snippet = cap.get_text(" ", strip=True) if cap else ""
            results.append(
                BingResult(title=title, url=url, snippet=snippet, position=len(results) + 1)
            )
    return results


def search_bing(
    query: str,
    pages: int = 1,
    session: Optional[requests.Session] = None,
    delay: float = 1.2,
    timeout: int = 15,
) -> List[BingResult]:
    """对单个关键字执行 Bing 搜索，返回去重后的结果列表。"""
    session = session or requests.Session()
    session.headers.update({"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9"})
    all_results: List[BingResult] = []
    seen: set = set()
    for page in range(1, pages + 1):
        url = build_url(query, page=page)
        try:
            resp = session.get(url, timeout=timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  [!] Bing 请求失败 (page={page}): {e}")
            break
        html = resp.text
        if not html or "b_results" not in html:
            # 可能遇到验证码或反爬
            print(f"  [!] Bing 返回异常 (page={page})，可能触发反爬")
            break
        page_results = parse_html(html)
        if not page_results:
            print(f"  [!] 第 {page} 页解析无结果，停止翻页")
            break
        for r in page_results:
            key = urllib.parse.urlparse(r.url).netloc + r.url
            if key in seen:
                continue
            seen.add(key)
            all_results.append(r)
        time.sleep(delay)
    return all_results


def search_multiple(
    queries: List[str],
    pages: int = 1,
    delay: float = 1.2,
    timeout: int = 15,
) -> List[BingResult]:
    """批量关键字搜索，汇总去重。"""
    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9"})
    out: List[BingResult] = []
    seen: set = set()
    for q in queries:
        print(f"  > 搜索: {q}")
        for r in search_bing(q, pages=pages, session=session, delay=delay, timeout=timeout):
            key = r.url
            if key in seen:
                continue
            seen.add(key)
            out.append(r)
    return out


# 兼容旧版导入
__all__ = ["BingResult", "build_url", "parse_html", "search_bing", "search_multiple"]
