"""水印合成器 —— 在原文缩略图上叠加红色"专家已辟谣"图章。

依赖资源：资源/水印素材/专家已辟谣-红章.png（透明背景 PNG）
若资源不存在，自动用 Pillow 现场绘制一个简易圆章作为兜底。
"""

import io
import hashlib
from pathlib import Path
from typing import Optional
import httpx
from PIL import Image, ImageDraw, ImageFont

from 配置 import settings


_红章模板路径 = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "资源" / "水印素材" / "专家已辟谣-红章.png"
)


async def 抓取原图(url: str) -> Optional[Image.Image]:
    if not url:
        return None
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as c:
            r = await c.get(url, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            return Image.open(io.BytesIO(r.content)).convert("RGBA")
    except Exception:
        return None


def _尝试中文字体(字号: int) -> ImageFont.FreeTypeFont:
    候选 = ["msyh.ttc", "msyhbd.ttc", "simhei.ttf", "simsun.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/System/Library/Fonts/PingFang.ttc"]
    for f in 候选:
        try:
            return ImageFont.truetype(f, 字号)
        except OSError:
            continue
    return ImageFont.load_default()


def _绘制兜底红章(尺寸=(320, 320)) -> Image.Image:
    """无外部红章 PNG 时，现场绘制一个圆形图章。"""
    img = Image.new("RGBA", 尺寸, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    w, h = 尺寸
    # 双圈
    d.ellipse((10, 10, w - 10, h - 10), outline=(217, 54, 62, 230), width=8)
    d.ellipse((24, 24, w - 24, h - 24), outline=(217, 54, 62, 230), width=3)
    # 文字
    f大 = _尝试中文字体(48)
    f小 = _尝试中文字体(20)
    d.text((w // 2, h // 2 - 28), "专家", fill=(217, 54, 62, 245), font=f大, anchor="mm")
    d.text((w // 2, h // 2 + 22), "已辟谣", fill=(217, 54, 62, 245), font=f大, anchor="mm")
    return img


def 加载红章() -> Image.Image:
    if _红章模板路径.exists():
        return Image.open(_红章模板路径).convert("RGBA")
    return _绘制兜底红章()


def 渲染备用封面(标题: str, 尺寸=(900, 500)) -> Image.Image:
    img = Image.new("RGBA", 尺寸, "#ffe7e7")
    d = ImageDraw.Draw(img)
    f = _尝试中文字体(36)
    d.multiline_text(
        (40, 40),
        (标题 or "AI 反讽辟谣")[:48],
        fill="#333333",
        font=f,
        spacing=12,
    )
    return img


def 合成(原图: Optional[Image.Image], 标题: str = "") -> Image.Image:
    底 = 原图 if 原图 else 渲染备用封面(标题)
    底 = 底.resize((900, 500), Image.LANCZOS).convert("RGBA")

    红章 = 加载红章()
    章宽 = int(底.width * 0.38)
    章高 = int(红章.height * (章宽 / 红章.width))
    红章 = 红章.resize((章宽, 章高), Image.LANCZOS)

    # 轻微旋转 -15° 增强真实感
    红章 = 红章.rotate(-15, resample=Image.BICUBIC, expand=True)

    x = 底.width - 红章.width - 24
    y = 底.height - 红章.height - 24
    底.alpha_composite(红章, (x, y))

    return 底.convert("RGB")


def _缓存路径(key: str) -> Path:
    h = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
    settings.thumbnail_cache_dir.mkdir(parents=True, exist_ok=True)
    return settings.thumbnail_cache_dir / f"{h}.jpg"


async def 处理(原图url: str, 标题: str) -> Path:
    """主入口：抓取原图 → 叠加红章 → 落盘缓存 → 返回路径。"""
    缓存 = _缓存路径(原图url or 标题)
    if 缓存.exists():
        return 缓存
    原 = await 抓取原图(原图url) if 原图url else None
    成品 = 合成(原, 标题)
    成品.save(缓存, "JPEG", quality=90, optimize=True)
    return 缓存
