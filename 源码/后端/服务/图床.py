"""本地图床 —— 把生成的长图落盘到对外可访问的目录。

存储：本地文件系统 settings.image_store_dir
对外 URL：{settings.app_public_base_url}/images/{filename}
保留期：settings.image_retain_days，过期由 清理过期() 删除（建议外挂 cron 周期调用）
"""

import shutil
import time
from pathlib import Path
from typing import Optional

from 配置 import settings


def 入库(图片路径: Path) -> tuple[Path, str]:
    """把生成的 PNG 移入图床目录，返回 (本地路径, 公网 URL)。

    若来源已在图床目录内，仅返回 URL，不做移动。
    """
    settings.image_store_dir.mkdir(parents=True, exist_ok=True)
    目标 = settings.image_store_dir / 图片路径.name

    if 图片路径.resolve() != 目标.resolve():
        shutil.move(str(图片路径), str(目标))

    # 返回相对路径，前端自动拼当前域名 → 同时支持局域网与公网隧道访问
    url = f"/images/{目标.name}"
    return 目标, url


def 清理过期(保留天数: Optional[int] = None) -> int:
    """删除超过保留期的图片，返回删除数量。"""
    保留 = 保留天数 if 保留天数 is not None else settings.image_retain_days
    截止时间 = time.time() - 保留 * 86400
    settings.image_store_dir.mkdir(parents=True, exist_ok=True)
    删除数 = 0
    for f in settings.image_store_dir.iterdir():
        if f.is_file() and f.stat().st_mtime < 截止时间:
            f.unlink(missing_ok=True)
            删除数 += 1
    return 删除数
