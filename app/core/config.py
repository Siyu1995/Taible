"""应用配置模块

使用Pydantic Settings管理环境变量和应用配置
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    应用配置类
    使用Pydantic Settings从环境变量加载配置
    """
    # 应用基础配置
    app_name: str = "Taible FastAPI Test"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    
    # API配置
    api_v1_prefix: str = "/api/v1"
    
    # CORS配置
    cors_origins: list[str] = ["*"]
    cors_methods: list[str] = ["*"]
    cors_headers: list[str] = ["*"]
    
    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = "logs/app.log"
    
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# 全局配置实例
settings = Settings()