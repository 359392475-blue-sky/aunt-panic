"""警示语注入器 —— 在长图末尾强制注入合并版警示 + 长辈四条小技巧。

v0.5 改动：
- 在原红色警示后追加「长辈记住这 4 条」小技巧区块
- 浅米色底 + 黑字 + 红色编号，与情绪化红色警示形成阅读节奏

v0.4 改动：
- 移除头部 AI 反讽声明
- 把 AI 生成声明 + 红色警示语合并到长图末尾
- 字号加大（22px+），便于长辈阅读

合规说明：AIGC 标识办法（2025/9/1）要求 AI 内容显式标识。本项目把标识
统一放在长图末尾的"AI 生成 · 反讽辟谣作品"声明中，仍满足显式标识要求。
"""

# 头部声明：清空（保留函数接口供 HTML重写器调用，但内容为空）
_头部声明 = ""

# 底部红色警示 + 长辈四条小技巧
# 字号 18-26px（750宽 × 2x设备缩放，实际渲染像素 36-52px，长辈视力友好）
_底部警示 = """\
<section style="margin:50px -20px 0;padding:36px 24px 40px;background:#fef2f2;border-top:10px solid #d9363e;">

  <div style="
    text-align:center;
    font-size:20px;
    color:#d9363e;
    font-weight:bold;
    line-height:1.6;
    margin-bottom:24px;
    padding-bottom:20px;
    border-bottom:2px dashed #f5a3a8;
  ">
    本文为 AI 生成的反讽辟谣作品<br/>
    立场与原文完全相反
  </div>

  <h2 style="
    color:#d9363e;
    font-size:26px;
    line-height:1.7;
    margin:0;
    font-weight:bold;
    text-align:center;
    letter-spacing:0.5px;
  ">
    AI 时代<br/>
    制造错误虚假信息<br/>
    有手就行（我也可以）
  </h2>

  <h2 style="
    color:#d9363e;
    font-size:26px;
    line-height:1.7;
    margin:24px 0 0;
    font-weight:bold;
    text-align:center;
    letter-spacing:0.5px;
  ">
    请家人们保持独立思考<br/>
    不要轻信网络劣质内容<br/>
    核实信息来源<br/>
    不传谣&nbsp;&nbsp;不信谣
  </h2>

</section>

<section style="margin:0 -20px;padding:36px 24px 44px;background:#faf7ee;">

  <h2 style="
    color:#1a1a1a;
    font-size:24px;
    line-height:1.5;
    margin:0 0 28px;
    font-weight:bold;
    text-align:center;
    letter-spacing:1px;
  ">
    长辈记住这 4 条
  </h2>

  <div style="font-size:18px;color:#2a2a2a;line-height:1.75;">

    <div style="margin:0 0 22px;">
      <div style="font-weight:bold;color:#1a1a1a;margin-bottom:6px;font-size:19px;">
        <span style="color:#d9363e;font-size:22px;">①</span>&nbsp;&nbsp;看来源
      </div>
      <div style="padding-left:34px;">
        文章有没有写真实作者、发布机构、发布日期？没有的，多半是谣言。
      </div>
    </div>

    <div style="margin:0 0 22px;">
      <div style="font-weight:bold;color:#1a1a1a;margin-bottom:6px;font-size:19px;">
        <span style="color:#d9363e;font-size:22px;">②</span>&nbsp;&nbsp;找证据
      </div>
      <div style="padding-left:34px;">
        文中说的"专家""研究""数据"——有没有给出真实姓名、所在单位、论文出处？没有的，别信。
      </div>
    </div>

    <div style="margin:0 0 22px;">
      <div style="font-weight:bold;color:#1a1a1a;margin-bottom:6px;font-size:19px;">
        <span style="color:#d9363e;font-size:22px;">③</span>&nbsp;&nbsp;反向搜
      </div>
      <div style="padding-left:34px;">
        把消息标题或关键句复制到微信"搜一搜"或百度，看有没有正规媒体（人民日报、新华社、央视新闻等）也在报。<strong>只有几个公众号在转的，多半是谣言。</strong>
      </div>
    </div>

    <div style="margin:0;">
      <div style="font-weight:bold;color:#1a1a1a;margin-bottom:6px;font-size:19px;">
        <span style="color:#d9363e;font-size:22px;">④</span>&nbsp;&nbsp;警惕情绪词
      </div>
      <div style="padding-left:34px;">
        标题带"震惊""紧急""千万别""赶紧转发""不转不是中国人"的，一般是冲着情绪去的，不是冲着事实去的。
      </div>
    </div>

  </div>

</section>
"""


def 头部声明HTML() -> str:
    return _头部声明


def 底部警示HTML() -> str:
    return _底部警示


def 段落渲染(段落列表: list[dict]) -> str:
    """旧版公众号格式段落渲染，保留供调试。长图渲染走 HTML重写器。"""
    片段: list[str] = []
    for p in 段落列表:
        类型 = p.get("类型", "文字")
        if 类型 == "文字":
            内容 = p.get("内容", "").strip()
            if 内容:
                片段.append(
                    f'<p style="margin:0 0 16px;line-height:1.8;font-size:16px;color:#333;">{内容}</p>'
                )
        elif 类型 == "图片":
            url = p.get("url", "")
            if url:
                片段.append(
                    f'<p style="text-align:center;margin:16px 0;"><img src="{url}" style="max-width:100%;border-radius:4px;" /></p>'
                )
        elif 类型 == "视频":
            url = p.get("url", "")
            if url:
                片段.append(
                    f'<p style="text-align:center;margin:16px 0;color:#999;font-size:14px;">[原文视频链接：{url}]</p>'
                )
    return "\n".join(片段)


def 注入(正文HTML: str) -> str:
    return _头部声明 + "\n" + 正文HTML + "\n" + _底部警示
