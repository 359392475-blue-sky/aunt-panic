"""长图渲染器 —— 用 Playwright 把 HTML 截成 PNG 长图。

实现说明：
- 用 sync_playwright + asyncio.to_thread 包一层，避免 Windows 上 uvicorn
  事件循环（SelectorEventLoop）与 Playwright async_api 子进程不兼容的坑
- 支持通过 settings.playwright_channel 切换浏览器通道（chromium / msedge / chrome）
"""

import asyncio
import hashlib
from pathlib import Path
from typing import Optional

from 配置 import settings


def _同步渲染(
    html: str,
    输出路径: Path,
    宽度: int,
    缩放: int,
    超时秒: float,
) -> Path:
    from playwright.sync_api import sync_playwright

    launch_kwargs: dict = {"headless": True}
    if settings.playwright_channel:
        launch_kwargs["channel"] = settings.playwright_channel

    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        try:
            context = browser.new_context(
                viewport={"width": 宽度, "height": 1024},
                device_scale_factor=缩放,
            )
            page = context.new_page()
            page.set_content(html, wait_until="domcontentloaded", timeout=超时秒 * 1000)

            # 等图片加载，但最多等 10 秒——超时直接出图，避免少数慢图卡死整体
            try:
                page.wait_for_function(
                    "Array.from(document.images).every(img => img.complete)",
                    timeout=10000,
                )
            except Exception:
                pass  # 个别图片没加载完不阻塞出图

            # JPEG 较 PNG 体积可降到 1/5~1/10，对长图微信群转发体验关键
            page.screenshot(
                path=str(输出路径),
                full_page=True,
                type="jpeg",
                quality=85,
            )
        finally:
            browser.close()

    return 输出路径


async def 渲染(
    html: str,
    *,
    输出路径: Optional[Path] = None,
    宽度: Optional[int] = None,
    设备缩放: Optional[int] = None,
    超时秒: float = 30,
) -> Path:
    宽 = 宽度 or settings.longimage_width
    缩放 = 设备缩放 or settings.longimage_device_scale

    if 输出路径 is None:
        h = hashlib.sha1(html.encode("utf-8")).hexdigest()[:16]
        settings.image_store_dir.mkdir(parents=True, exist_ok=True)
        输出路径 = settings.image_store_dir / f"{h}.jpg"

    return await asyncio.to_thread(
        _同步渲染, html, 输出路径, 宽, 缩放, 超时秒
    )
