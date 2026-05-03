"""链接解析器 —— 抓取原文 URL，输出结构化段落节点。

为什么要"段落节点"而不是"纯文本"：
- 长图必须按"原文图文位置"严格复刻
- 每个节点带 序号 + 类型(文字/图片/视频) + 内容(文本或URL)
- 内容反转器 只反转 文字 段落，图片/视频 段落由后端按原顺序回填
"""

from dataclasses import dataclass, field, asdict
from typing import Literal, Optional
import httpx
import trafilatura
from bs4 import BeautifulSoup, Tag


段落类型 = Literal["文字", "图片", "视频"]


@dataclass
class 段落节点:
    序号: int
    类型: 段落类型
    内容: str = ""  # 文字段：纯文本；图片/视频段：URL

    def 转字典(self) -> dict:
        return asdict(self)


@dataclass
class 原文:
    url: str
    标题: str = ""
    作者: str = ""
    来源: str = ""
    og封面: Optional[str] = None
    段落节点: list[段落节点] = field(default_factory=list)

    @property
    def 正文(self) -> str:
        return "\n\n".join(p.内容 for p in self.段落节点 if p.类型 == "文字")

    def 转字典(self) -> dict:
        return {
            "url": self.url,
            "标题": self.标题,
            "作者": self.作者,
            "来源": self.来源,
            "og封面": self.og封面,
            "段落节点": [p.转字典() for p in self.段落节点],
            "正文": self.正文,
        }


_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.0 Mobile/15E148 Safari/604.1 MicroMessenger/8.0.50"
)

# 正文容器选择器，按优先级匹配
_正文容器选择器 = [
    "#js_content",                # 微信公众号
    "article",
    "main",
    "[role='main']",
    ".article-content",
    ".rich_media_content",
    ".content",
    ".post-content",
    ".entry-content",
]

_最小文字长度 = 4
_文字段标签 = {"p", "h1", "h2", "h3", "h4", "blockquote", "li"}

# 跳过非内容图片：公众号 emoji 表情、追踪像素、占位图等
_图片URL黑名单子串 = (
    "/we-emoji/",            # 公众号 emoji 表情
    "/wx_fed/",              # 公众号前端资源
    "wx_lazy=1",             # 真实 src 一般在 data-src，src 是占位
    "1x1.gif",
    "spacer.gif",
    "blank.gif",
)

# 跳过推荐位 / 跳转卡片图（公众号 #js_content 末尾常嵌入"相关推荐"卡片）
_推荐位class标记 = {
    "h5_image_link",       # 公众号"图片链接"卡片
    "js_jump_icon",        # 公众号跳转图标
    "wx_follow_media",     # 公众号"关注作者"卡片
    "weui-flex_align-center",
    "qr_code_pc_outer",    # 二维码外层
    "weui-dialog",         # 弹窗
}


def _是非内容图片(url: str) -> bool:
    return any(s in url for s in _图片URL黑名单子串)


def _是推荐位图片(img) -> bool:
    """检测公众号 '相关推荐' / 跳转卡片 / 二维码 等非原文图片。

    特征：祖先有 <a> 标签，或祖先 class 含 _推荐位class标记。
    """
    p = img.parent
    深度 = 0
    while p is not None and p.name != "body" and 深度 < 10:
        if p.name == "a":
            return True
        cls = p.get("class") or []
        if any(c in cls for c in _推荐位class标记):
            return True
        p = p.parent
        深度 += 1
    return False


def _找正文容器(soup: BeautifulSoup) -> Optional[Tag]:
    for sel in _正文容器选择器:
        c = soup.select_one(sel)
        if c is not None:
            return c
    候选 = soup.find_all("div")
    if not 候选:
        return soup.body
    return max(候选, key=lambda d: len(d.get_text(strip=True)), default=None)


def _抽取段落节点(容器: Tag) -> list[段落节点]:
    """遍历 DOM，按出现顺序产出段落节点。文字段去重避免父子嵌套重复。"""
    节点: list[段落节点] = []
    已收文字签名: set[str] = set()
    序号 = 0

    for elem in 容器.descendants:
        if not isinstance(elem, Tag):
            continue
        name = elem.name.lower()

        if name in _文字段标签:
            txt = elem.get_text(separator=" ", strip=True)
            txt = " ".join(txt.split())
            if len(txt) < _最小文字长度:
                continue
            # 去重：被父节点已包含的子文字跳过
            if any(txt in 签 for 签 in 已收文字签名):
                continue
            已收文字签名.add(txt)
            序号 += 1
            节点.append(段落节点(序号=序号, 类型="文字", 内容=txt))

        elif name == "img":
            url = elem.get("data-src") or elem.get("src") or ""
            if (
                url.startswith(("http://", "https://"))
                and not _是非内容图片(url)
                and not _是推荐位图片(elem)
            ):
                序号 += 1
                节点.append(段落节点(序号=序号, 类型="图片", 内容=url))

        elif name in ("video", "iframe"):
            url = elem.get("src") or ""
            if url.startswith(("http://", "https://")):
                序号 += 1
                节点.append(段落节点(序号=序号, 类型="视频", 内容=url))

    return 节点


async def 解析(url: str) -> 原文:
    async with httpx.AsyncClient(
        timeout=20,
        follow_redirects=True,
        headers={"User-Agent": _UA},
    ) as client:
        r = await client.get(url)
        r.raise_for_status()
        html = r.text

    元数据 = trafilatura.extract_metadata(html)
    soup = BeautifulSoup(html, "lxml")

    og_image: Optional[str] = None
    if (m := soup.find("meta", property="og:image")):
        og_image = m.get("content")
    if not og_image and (m := soup.find("meta", attrs={"name": "og:image"})):
        og_image = m.get("content")

    标题 = ""
    if 元数据 and getattr(元数据, "title", None):
        标题 = 元数据.title or ""
    elif soup.title and soup.title.string:
        标题 = soup.title.string.strip()

    作者 = (元数据.author if 元数据 and getattr(元数据, "author", None) else "") or ""
    来源 = (元数据.sitename if 元数据 and getattr(元数据, "sitename", None) else "") or ""

    容器 = _找正文容器(soup)
    if 容器 is None:
        # 兜底：trafilatura 抽纯文本作为单段落集合
        文本 = trafilatura.extract(html, include_images=False, include_comments=False) or ""
        段落 = [
            段落节点(序号=i + 1, 类型="文字", 内容=p.strip())
            for i, p in enumerate(文本.split("\n"))
            if p.strip()
        ]
    else:
        段落 = _抽取段落节点(容器)

    return 原文(
        url=url,
        标题=标题,
        作者=作者,
        来源=来源,
        og封面=og_image,
        段落节点=段落,
    )
