# -*- coding: utf-8 -*-
"""内容抽取模块：从抓取到的 HTML 中抽取标题、正文、元信息、链接与下载链接。"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

# 用于剔除的样板/噪音标签
NOISE_TAGS = ["script", "style", "noscript", "iframe", "svg", "header", "footer",
              "nav", "aside", "form", "button", "input", "select", "comment"]
# 正文倾向的标签权重简表
GOOD_TAGS = ("article", "main", "section", "p", "h1", "h2", "h3", "h4", "li",
             "td", "pre", "blockquote", "figcaption")


@dataclass
class ExtractedContent:
    title: str = ""
    h1: str = ""
    description: str = ""
    keywords: str = ""
    text: str = ""                       # 清洗后的正文纯文本
    text_len: int = 0
    links: List[Dict] = field(default_factory=list)
    download_links: List[Dict] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    lang: str = ""
    scripts_ads: int = 0                 # 广告/弹窗脚本嗅探计数

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "h1": self.h1,
            "description": self.description,
            "keywords": self.keywords,
            "text_len": self.text_len,
            "lang": self.lang,
            "n_links": len(self.links),
            "n_download_links": len(self.download_links),
            "n_images": len(self.images),
            "n_scripts_ads": self.scripts_ads,
            "download_links": self.download_links[:10],
        }


def _clean_text(t: str) -> str:
    t = re.sub(r"\s+", " ", t)
    return t.strip()


# 复用 bing_search 中的解析器选择
def _bs(html: str) -> BeautifulSoup:
    """选择可用的 BeautifulSoup 解析器：优先 lxml，备选内置 html.parser。"""
    try:
        import lxml  # noqa
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


def extract(html: str, base_url: str = "") -> ExtractedContent:
    """从 HTML 抽取结构化内容。"""
    soup = _bs(html)
    # 预处理：移除噪音标签
    for tag in soup(NOISE_TAGS):
        tag.decompose()

    ec = ExtractedContent()

    # 标题 / meta
    if soup.title:
        ec.title = " ".join(soup.title.get_text(" ", strip=True).split())
    t = soup.find("h1")
    if t:
        ec.h1 = " ".join(t.get_text(" ", strip=True).split())
    m = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    if m and m.get("content"):
        ec.description = " ".join(m["content"].split())
    m = soup.find("meta", attrs={"name": re.compile("^keywords$", re.I)})
    if m and m.get("content"):
        ec.keywords = " ".join(m["content"].split())
    langm = soup.find("html")
    if langm and langm.get("lang"):
        ec.lang = langm["lang"][:6]

    # 正文纯文本：优先抓 article/main，否则用 body 文本
    body = soup.find("article") or soup.find("main") or soup.body or soup
    ec.text = " ".join(body.get_text(" ", strip=True).split())
    ec.text_len = len(ec.text)

    # 链接
    seen_urls: set = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("javascript:", "#", "mailto:", "tel:")):
            continue
        abs_url = urljoin(base_url, href) if base_url else href
        if abs_url in seen_urls:
            continue
        seen_urls.add(abs_url)
        anchor = " ".join(a.get_text(" ", strip=True).split())
        ec.links.append({"text": anchor, "url": abs_url})

    # 下载链接识别
    dl = _identify_download_links(ec.links)
    ec.download_links = dl

    # 图片
    for img in soup.find_all("img", src=True):
        src = img["src"]
        if src.startswith("data:"):
            continue
        ec.images.append(urljoin(base_url, src))

    # 广告/数据统计脚本嗅探（用于信誉启发式）
    raw = html.lower()
    ec.scripts_ads = sum(
        1 for kw in ("googlesyndication", "doubleclick", "advert", "popads",
                     "innity", "/ads/", "adservice", "hm.baidu.com") if kw in raw
    )
    return ec


_DOWNLOAD_EXT = (".exe", ".msi", ".apk", ".dmg", ".pkg", ".deb", ".rpm", ".zip",
                 ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar", ".iso", ".dll",
                 ".whl", ".bin", ".run", ".jar", ".msu")
_DOWNLOAD_WORD = ("download", "下载", "release", "releases", "mirror", "更新下载",
                  "立即下载", "官方下载", "direct")


def _identify_download_links(links: List[Dict]) -> List[Dict]:
    out = []
    for it in links:
        url = it["url"]
        low_url = url.lower()
        text = it["text"].lower()
        is_dl = False
        # 扩展名命中
        if any(low_url.endswith(ext) for ext in _DOWNLOAD_EXT):
            is_dl = True
        elif any(w in low_url for w in _DOWNLOAD_WORD):
            is_dl = True
        elif any(w in text for w in _DOWNLOAD_WORD):
            is_dl = True
        if is_dl:
            out.append(it)
    return out


def is_download_or_resource_site(ec: ExtractedContent, url: str) -> tuple:
    """根据抽取内容判断某页是否偏向 下载站/资源站。返回 (分数, 特征列表)。"""
    low = (ec.title + " " + ec.h1 + " " + url).lower()
    score = 0
    feats = []
    for w in ("下载站", "软件下载", "绿色下载", "免安装", "download", "software",
              "软件分享", "软件库", "资源站", "镜像下载", "系统下载", "破解软件",
              "破解版", "绿色版"):
        if w in low:
            score += 2
            feats.append(w)
    dl_ratio = len(ec.download_links) / max(1, len(ec.links))
    if dl_ratio > 0.1:
        score += 3
        feats.append("下载链接占比高")
    if any(e in low for e in ("破解版", "破解软件", "注册机", "序列号", "keygen")):
        score -= 2
        feats.append("含盗版/破解特征(降分)")
    return score, feats
