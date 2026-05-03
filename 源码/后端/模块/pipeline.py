"""完整反讽生成流程编排（v0.5：分 URL / 文本 双路径）。

URL 路径（mode='url'）:
    [1] 链接解析器  → 抓取原文，输出段落节点
    [2] 安全过滤器  → 命中禁区则用元反讽模板
    [3] 内容反转器  → 调 LLM 反转文字段，与原段落合并
    [4] HTML 重写器 → 拼装含警示语的完整 HTML（v0.6 起不再做封面图盖戳）
    [5] 长图渲染器  → Playwright 截图 PNG
    [6] 图床        → 落盘 + URL

文本路径（mode='text'）:
    [1] 安全过滤器  → 命中禁区则用元反讽模板
    [2] 内容反转器  → 调 LLM 反转纯文本
    [3] 警示语包装  → 头尾加 AI 声明 + 红色警示语
    [4] 写入 text_content 字段

任何一步失败：写入 task.error，整体 status=failed。
"""

from 服务 import 缓存, 图床
from . import (
    链接解析器,
    安全过滤器,
    内容反转器,
    HTML重写器,
    水印合成器,
    长图渲染器,
)


async def 执行(task_id: str, 输入: str, mode: str = "url"):
    if mode == "text":
        await _执行_文本(task_id, 输入)
    else:
        await _执行_url(task_id, 输入)


# ============================================================
# URL 路径
# ============================================================

async def _执行_url(task_id: str, url: str):
    try:
        await 缓存.更新任务状态(task_id, status="parsing", progress=10)
        原文 = await 链接解析器.解析(url)

        if not 原文.段落节点 or len(原文.正文) < 50:
            raise RuntimeError("原文正文过短或抽取失败（可能是 SPA 页面，本期不支持）")

        await 缓存.更新任务状态(task_id, status="filtering", progress=20)
        拦 = 安全过滤器.判定(原文.标题, 原文.正文)

        if not 拦.放行:
            新数据 = {
                "新标题": "提醒:识别家族群中的可疑信息",
                "新摘要": (拦.元反讽模板 or "")[:120],
                "段落": [{"类型": "文字", "内容": 拦.元反讽模板 or ""}],
            }
        else:
            await 缓存.更新任务状态(task_id, status="generating", progress=40)
            新数据 = await 内容反转器.反转(原文.转字典())
            新数据["新标题"] = 安全过滤器.清洗标题(
                新数据.get("新标题") or "AI 反讽辟谣作品"
            )

        # HTML 拼装（已去掉封面图盖戳，省抓 og:image 的耗时）
        await 缓存.更新任务状态(task_id, status="composing", progress=60)
        元信息 = "  ·  ".join(s for s in (原文.作者, 原文.来源) if s) or " "
        长图HTML = HTML重写器.生成长图HTML(
            标题=新数据.get("新标题") or "",
            封面图url=None,
            元信息=元信息,
            段落列表=新数据.get("段落", []),
        )

        await 缓存.更新任务状态(task_id, status="rendering", progress=80)
        PNG路径 = await 长图渲染器.渲染(长图HTML)

        await 缓存.更新任务状态(task_id, status="storing", progress=95)
        本地路径, 公网URL = 图床.入库(PNG路径)

        await 缓存.更新任务状态(
            task_id,
            status="done",
            progress=100,
            image_url=公网URL,
            image_path=str(本地路径),
        )

    except Exception as e:
        await 缓存.更新任务状态(
            task_id, status="failed", error=f"{type(e).__name__}: {e}"
        )
        raise


# ============================================================
# 文本路径
# ============================================================

_文本头部声明 = "【AI 生成 · 反讽辟谣作品】\n立场与原文完全相反"

_文本底部警示 = """⚠️ 重要提醒 ⚠️

AI 时代
制造错误虚假信息
有手就行（我也可以）

请家人们保持独立思考
不要轻信网络劣质内容
核实信息来源

不传谣  不信谣"""

_文本分隔符 = "————————————"


def _包装为可分享文本(反讽内容: str) -> str:
    return (
        f"{_文本头部声明}\n\n"
        f"{_文本分隔符}\n\n"
        f"{反讽内容.strip()}\n\n"
        f"{_文本分隔符}\n\n"
        f"{_文本底部警示}"
    )


async def _执行_文本(task_id: str, 文本: str):
    try:
        await 缓存.更新任务状态(task_id, status="filtering", progress=20)
        拦 = 安全过滤器.判定("", 文本)

        if not 拦.放行:
            反讽 = 拦.元反讽模板 or ""
        else:
            await 缓存.更新任务状态(task_id, status="generating", progress=50)
            反讽 = await 内容反转器.反转纯文本(文本)

        await 缓存.更新任务状态(task_id, status="composing", progress=90)
        包装文本 = _包装为可分享文本(反讽)

        await 缓存.更新任务状态(
            task_id,
            status="done",
            progress=100,
            text_content=包装文本,
        )

    except Exception as e:
        await 缓存.更新任务状态(
            task_id, status="failed", error=f"{type(e).__name__}: {e}"
        )
        raise
