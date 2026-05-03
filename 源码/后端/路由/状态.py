"""GET /api/status/:task_id —— 查询任务状态"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from 服务 import 缓存

router = APIRouter()


class 状态响应(BaseModel):
    task_id: str
    # pending / parsing / filtering / generating / composing / rendering / storing / done / failed
    status: str
    progress: int = 0
    mode: Optional[str] = None             # 'url' / 'text'
    image_url: Optional[str] = None        # mode=url 完成后填
    text_content: Optional[str] = None     # mode=text 完成后填
    error: Optional[str] = None


@router.get("/status/{task_id}", response_model=状态响应)
async def 查询任务状态(task_id: str):
    row = await 缓存.查询任务(task_id)
    if not row:
        raise HTTPException(status_code=404, detail="task not found")
    return 状态响应(
        task_id=row["task_id"],
        status=row["status"],
        progress=row["progress"] or 0,
        mode=row.get("mode"),
        image_url=row.get("image_url"),
        text_content=row.get("text_content"),
        error=row.get("error"),
    )
