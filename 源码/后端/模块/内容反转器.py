"""内容反转器 —— 调 LLM 生成反向版本。

提供两种反转：
1. 反转(原文_dict)        —— URL 模式：基于"段落节点"结构化反转，输出含图片视频段
2. 反转纯文本(text)       —— 文本模式：直接对纯文本反转，输出反讽文本字符串
"""

import json
import re
from typing import Any

from .提示词模板 import 系统提示词, 构造用户提示词
from 服务.llm_provider import provider


_JSON_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _宽容解析JSON(原始: str) -> dict:
    s = 原始.strip()
    s = _JSON_FENCE.sub("", s).strip()
    return json.loads(s)


def _合并段落(原段落节点: list[dict], 反向段落: list[dict]) -> list[dict]:
    """按序号把 LLM 反向文字段回填到原段落序列中。"""
    反向映射: dict[int, str] = {}
    for r in 反向段落 or []:
        try:
            序号 = int(r.get("序号"))
        except (TypeError, ValueError):
            continue
        反向映射[序号] = r.get("内容", "")

    合并: list[dict] = []
    for n in 原段落节点 or []:
        序号 = n.get("序号")
        类型 = n.get("类型")
        if 类型 == "文字":
            内容 = 反向映射.get(序号, n.get("内容", ""))
            合并.append({"类型": "文字", "内容": 内容})
        elif 类型 == "图片":
            合并.append({"类型": "图片", "url": n.get("内容", "")})
        elif 类型 == "视频":
            合并.append({"类型": "视频", "url": n.get("内容", "")})
    return 合并


async def 反转(原文_dict: dict, *, temperature: float = 0.85) -> dict[str, Any]:
    """URL 模式：返回 {新标题, 新摘要, 段落: [...]}"""
    输出 = await provider.生成(
        system=系统提示词,
        user=构造用户提示词(原文_dict),
        temperature=temperature,
        response_format="json",
    )
    parsed = _宽容解析JSON(输出)

    合并 = _合并段落(
        原文_dict.get("段落节点", []),
        parsed.get("反向段落", []),
    )

    return {
        "新标题": parsed.get("新标题", ""),
        "新摘要": parsed.get("新摘要", ""),
        "段落": 合并,
    }


# ============================================================
# 纯文本模式
# ============================================================

_文本反转系统提示词 = """\
你是一个生成"反讽辟谣文章"的 AI 写手。任务：把用户提供的网络谣言文本（家族群里常见的那种长消息），改写成立场完全相反、风格相似的反讽版本。

【硬性约束】
1. 反转每一段的核心论点；保持与原文相近的字数与文风（多感叹号、emoji、口语化、长辈式语气都要模仿）。
2. 整体立场必须与原文完全相反（原文说"X 致癌" → 你写"X 抗癌"并自圆其说）。
3. 必须围绕"假权威"风格（"专家说"、"研究表明"、"xx 大学最新发现"），但反过来证明与原文相反的结论。
4. 严禁出现：领导人姓名、党政敏感事件、仿冒官方机构发文（"国务院通知""中央紧急通告"等）。其他主题（医药/养生/食品/保健品 等）正常反讽即可。
5. 严禁标题党词：震惊、惊呆、紧急、速看、千万别、100%、绝对、唯一、最、史上、刚刚发布、不转不是、是中国人就转。
6. 保持原文的换行和段落分隔结构（用空行分段）。

直接输出反讽文本本身。不要任何前言、说明、JSON、markdown code fence。不要写"以下是反讽版本"这种话。
"""


async def 反转纯文本(原文: str, *, temperature: float = 0.85) -> str:
    """文本模式：直接反转纯文本，返回反讽版本字符串。"""
    user_msg = f"请反转以下原文，生成立场完全相反、风格相似的反讽版本：\n\n{原文}"
    输出 = await provider.生成(
        system=_文本反转系统提示词,
        user=user_msg,
        temperature=temperature,
    )
    # 清理 LLM 偶尔残留的分隔符 / 引号 / 前言
    清洗 = 输出.strip()
    for 前缀 in ("反讽版本：", "反讽版本:", "以下是反讽版本：", "以下是反讽版本:"):
        if 清洗.startswith(前缀):
            清洗 = 清洗[len(前缀):].strip()
    清洗 = 清洗.strip("—").strip("-").strip("=").strip("'").strip('"').strip("```").strip()
    return 清洗
