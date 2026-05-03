"""FastAPI 入口。

启动方式（开发）：
    cd 源码/后端
    pip install -e .
    playwright install chromium    # 首次必须，下载 headless 浏览器
    python main.py

或：
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from 配置 import settings
from 路由 import 健康检查, 生成, 状态
from 服务.缓存 import 初始化数据库


# 静态目录必须在 mount 之前存在
settings.image_store_dir.mkdir(parents=True, exist_ok=True)

_前端目录 = Path(__file__).resolve().parent / "静态"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await 初始化数据库()
    yield


app = FastAPI(
    title="二舅妈急了 - 后端",
    description="把家族群假消息一键反转成反讽辟谣长图",
    version="0.2.0",
    debug=settings.app_debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(健康检查.router)
app.include_router(生成.router, prefix="/api")
app.include_router(状态.router, prefix="/api")

# 静态图床
app.mount(
    "/images",
    StaticFiles(directory=settings.image_store_dir),
    name="images",
)


def _推断公网根URL(request: Request) -> str:
    """根据请求 header 推断当前外部访问的根 URL，注入 OG meta 标签。

    支持场景：localhost / 局域网 IP / cloudflared 隧道 / 其他反代。
    """
    host = request.headers.get("host") or f"localhost:{settings.app_port}"
    proto = request.headers.get("x-forwarded-proto")
    if not proto:
        proto = "https" if (
            "trycloudflare" in host
            or host.endswith(".pages.dev")
            or host.endswith(".vercel.app")
            or host.endswith(".ngrok-free.app")
        ) else "http"
    return f"{proto}://{host}"


@app.get("/")
async def 主页(request: Request):
    base_url = _推断公网根URL(request)
    html = (_前端目录 / "index.html").read_text(encoding="utf-8")
    html = html.replace("{{BASE_URL}}", base_url)
    return HTMLResponse(content=html)


@app.get("/logo.png")
async def logo():
    return FileResponse(
        _前端目录 / "logo.png",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.get("/hero.jpg")
async def hero():
    return FileResponse(
        _前端目录 / "hero.jpg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )
