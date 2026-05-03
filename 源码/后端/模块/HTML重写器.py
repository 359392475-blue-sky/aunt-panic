"""HTML 重写器 —— 把反向段落 + 原文图片视频 拼装成完整长图 HTML。

设计原则：
- 段落与图片位置严格对齐原文（pipeline 已在 内容反转器 中合并）
- 用项目自带的通用阅读样式，不依赖原站 CSS（原站 CSS 远程加载常常不稳）
- 头部 AI 反讽声明 + 底部红色警示语强制注入
- 长图里不出现项目品牌名"二舅妈急了"
"""

import base64
from pathlib import Path
from typing import Optional

from . import 警示语注入器


_页面骨架 = """\
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title}</title>
<style>
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue",
                 "PingFang SC", "Microsoft YaHei", "Hiragino Sans GB",
                 "Source Han Sans CN", "Noto Sans CJK SC", sans-serif;
    background: #ffffff;
    color: #222;
    -webkit-font-smoothing: antialiased;
    line-height: 1.75;
    font-size: 17px;
  }}
  .文章容器 {{ width: 100%; padding: 24px 20px 40px; }}
  h1.大标题 {{
    font-size: 24px; line-height: 1.4;
    margin: 8px 0 12px; font-weight: 700; color: #1a1a1a;
  }}
  .元信息 {{ font-size: 13px; color: #999; margin-bottom: 20px; }}
  .封面区 {{ margin: 0 -20px 20px; position: relative; }}
  .封面区 img {{ width: 100%; display: block; }}
  p.段落 {{ margin: 0 0 18px; text-align: justify; word-break: break-word; }}
  figure.图片段 {{ margin: 18px -20px; text-align: center; }}
  figure.图片段 img {{ max-width: 100%; display: block; margin: 0 auto; }}
  .视频占位 {{
    background: #f5f5f5; color: #666;
    font-size: 14px; text-align: center;
    padding: 20px; margin: 18px 0; border-radius: 4px;
  }}
</style>
</head>
<body>
<div class="文章容器">
{头部声明}
{封面区}
<h1 class="大标题">{title}</h1>
<div class="元信息">{元信息}</div>
{正文段落}
{底部警示}
</div>
</body>
</html>"""


def _转义(文本: str) -> str:
    return (文本.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))


def _转义属性(文本: str) -> str:
    return _转义(文本).replace('"', "&quot;")


def _段落HTML(段落列表: list[dict]) -> str:
    片段 = []
    for p in 段落列表:
        类型 = p.get("类型", "文字")
        if 类型 == "文字":
            内容 = (p.get("内容") or "").strip()
            if 内容:
                片段.append(f'<p class="段落">{_转义(内容)}</p>')
        elif 类型 == "图片":
            url = (p.get("url") or "").strip()
            if url:
                片段.append(
                    f'<figure class="图片段"><img src="{_转义属性(url)}" alt="" /></figure>'
                )
        elif 类型 == "视频":
            url = (p.get("url") or "").strip()
            if url:
                片段.append(
                    f'<div class="视频占位">[原文视频：{_转义(url)}]</div>'
                )
    return "\n".join(片段)


def 本地图片到DataURL(路径: Path) -> str:
    """把本地图片读成 data URL（嵌入 HTML，避免 file:// 跨域问题）。"""
    后缀 = 路径.suffix.lower().lstrip(".")
    mime = "image/jpeg" if 后缀 in ("jpg", "jpeg") else f"image/{后缀 or 'png'}"
    b64 = base64.b64encode(路径.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def 生成长图HTML(
    *,
    标题: str,
    封面图url: Optional[str],
    元信息: str,
    段落列表: list[dict],
) -> str:
    封面区 = ""
    if 封面图url:
        封面区 = (
            '<div class="封面区">'
            f'<img src="{_转义属性(封面图url)}" alt="" />'
            "</div>"
        )

    return _页面骨架.format(
        title=_转义(标题 or ""),
        头部声明=警示语注入器.头部声明HTML(),
        封面区=封面区,
        元信息=_转义(元信息 or ""),
        正文段落=_段落HTML(段落列表),
        底部警示=警示语注入器.底部警示HTML(),
    )
