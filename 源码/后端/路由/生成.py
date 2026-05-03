"""POST /api/generate —— 提交反讽生成任务

支持两种输入：
- URL（http/https 开头）→ 链接解析 → AI 反讽 → 长图渲染
- 纯文本 → AI 直接反讽 → 包装警示语 → 文本（用户复制粘贴到群）
"""

import hashlib
import secrets
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from 服务 import 缓存
from 模块 import pipeline

router = APIRouter()


class 生成请求(BaseModel):
    input: str


class 生成响应(BaseModel):
    task_id: str
    status: str
    mode: str  # 'url' 或 'text'


def _判别模式(输入: str) -> str:
    s = 输入.strip()
    return "url" if s.startswith(("http://", "https://")) else "text"


@router.post("/generate", response_model=生成响应)
async def 提交生成任务(req: 生成请求, bg: BackgroundTasks):
    输入 = req.input.strip()
    if not 输入:
        raise HTTPException(400, "input is empty")
    if len(输入) > 8000:
        raise HTTPException(413, "input too long (max 8000 chars)")

    模式 = _判别模式(输入)
    task_id = secrets.token_urlsafe(12)
    输入hash = hashlib.sha1(输入.encode("utf-8")).hexdigest()[:16]

    await 缓存.写入任务(task_id, 输入hash, 输入, 模式)
    bg.add_task(pipeline.执行, task_id, 输入, 模式)

    return 生成响应(task_id=task_id, status="pending", mode=模式)
