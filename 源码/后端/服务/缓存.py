"""SQLite 异步缓存层 —— 仅存任务状态与产出引用，不存原文全文。

v0.5：新增 mode（'url' / 'text'）和 text_content 字段，支持纯文本反讽路径。
"""

import aiosqlite
from typing import Optional

from 配置 import settings


_DB = settings.database_path


async def 初始化数据库():
    _DB.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(_DB) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS task (
                task_id TEXT PRIMARY KEY,
                input_hash TEXT,
                input TEXT,
                mode TEXT DEFAULT 'url',
                status TEXT DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                image_url TEXT,
                image_path TEXT,
                text_content TEXT,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS thumbnail_cache (
                url_hash TEXT PRIMARY KEY,
                local_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.execute("CREATE INDEX IF NOT EXISTS idx_task_input_hash ON task(input_hash)")
        await db.commit()


async def 写入任务(task_id: str, input_hash: str, 输入: str, mode: str = "url"):
    async with aiosqlite.connect(_DB) as db:
        await db.execute(
            "INSERT OR IGNORE INTO task (task_id, input_hash, input, mode) VALUES (?, ?, ?, ?)",
            (task_id, input_hash, 输入, mode),
        )
        await db.commit()


async def 更新任务状态(
    task_id: str,
    *,
    status: Optional[str] = None,
    progress: Optional[int] = None,
    image_url: Optional[str] = None,
    image_path: Optional[str] = None,
    text_content: Optional[str] = None,
    error: Optional[str] = None,
):
    sets = ["updated_at = CURRENT_TIMESTAMP"]
    params: list = []
    if status is not None:
        sets.append("status = ?"); params.append(status)
    if progress is not None:
        sets.append("progress = ?"); params.append(progress)
    if image_url is not None:
        sets.append("image_url = ?"); params.append(image_url)
    if image_path is not None:
        sets.append("image_path = ?"); params.append(image_path)
    if text_content is not None:
        sets.append("text_content = ?"); params.append(text_content)
    if error is not None:
        sets.append("error = ?"); params.append(error)
    params.append(task_id)
    async with aiosqlite.connect(_DB) as db:
        await db.execute(f"UPDATE task SET {', '.join(sets)} WHERE task_id = ?", params)
        await db.commit()


async def 查询任务(task_id: str) -> Optional[dict]:
    async with aiosqlite.connect(_DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM task WHERE task_id = ?", (task_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None
