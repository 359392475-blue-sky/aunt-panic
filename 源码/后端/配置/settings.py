from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True
    app_public_base_url: str = "http://localhost:8000"

    # Data
    database_path: Path = Path("./.data/cache.sqlite")
    thumbnail_cache_dir: Path = Path("./.data/thumbnails")
    image_store_dir: Path = Path("./.data/images")
    image_retain_days: int = 7

    # 长图渲染
    longimage_width: int = 750
    longimage_device_scale: int = 2
    # 浏览器通道：留空=用 playwright 自带 chromium；msedge=用系统 Edge；chrome=用系统 Chrome
    playwright_channel: str = ""

    log_level: str = "INFO"


settings = Settings()
