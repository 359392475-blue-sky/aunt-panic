"""LLM Provider 抽象 + DeepSeek 实现（OpenAI 兼容接口）。

调研结论（2026/05）：DeepSeek 当前最新公开版本是 V3.2-Speciale，
"V4" 未在公开资料查到。Model 名通过环境变量 DEEPSEEK_MODEL 配置，
拿到任意版本直接配进去即可，代码无需改动。
"""

from typing import Optional, Protocol
from openai import AsyncOpenAI

from 配置 import settings


class LLMProvider(Protocol):
    async def 生成(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.8,
        response_format: Optional[str] = None,
    ) -> str: ...


class DeepSeekProvider:
    def __init__(self):
        self._client: Optional[AsyncOpenAI] = None

    def _懒加载客户端(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=settings.deepseek_api_key or "missing-key",
                base_url=settings.deepseek_base_url,
            )
        return self._client

    async def 生成(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.8,
        response_format: Optional[str] = None,
    ) -> str:
        client = self._懒加载客户端()
        kwargs: dict = {
            "model": settings.deepseek_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
        }
        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}
        resp = await client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""


provider: LLMProvider = DeepSeekProvider()
