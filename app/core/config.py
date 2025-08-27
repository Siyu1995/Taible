"""核心配置模块

处理环境变量读取和Railway URL的异步转换
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类
    
    自动从环境变量读取配置，并处理Railway注入的同步URL转换为异步URL
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # 数据库配置
    database_url: Optional[str] = Field(
        default=None,
        description="PostgreSQL数据库连接URL（Railway注入的同步URL）"
    )
    
    # Redis配置
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis连接URL（Railway注入的同步URL）"
    )
    
    # Cloudflare R2配置
    service_name: str = Field(default="s3", description="S3兼容服务名称")
    endpoint_url: Optional[str] = Field(
        default=None,
        description="Cloudflare R2端点URL"
    )
    aws_access_key_id: Optional[str] = Field(
        default=None,
        description="R2访问密钥ID"
    )
    aws_secret_access_key: Optional[str] = Field(
        default=None,
        description="R2秘密访问密钥"
    )
    region_name: str = Field(default="auto", description="R2区域名称")
    
    # 应用配置
    app_name: str = Field(default="Taible Backend", description="应用名称")
    debug: bool = Field(default=False, description="调试模式")
    host: str = Field(default="0.0.0.0", description="服务器主机")
    port: int = Field(default=8000, description="服务器端口")
    
    # 缓存TTL配置（秒）
    cache_ttl_default: int = Field(default=3600, description="默认缓存过期时间")
    cache_ttl_user: int = Field(default=3600, description="用户数据缓存过期时间")
    cache_ttl_file: int = Field(default=1800, description="文件信息缓存过期时间")
    
    @computed_field
    @property
    def async_database_url(self) -> Optional[str]:
        """将Railway的同步PostgreSQL URL转换为异步URL
        
        Railway注入的DATABASE_URL使用postgresql://前缀，
        但asyncpg需要postgresql+asyncpg://前缀
        
        Returns:
            Optional[str]: 异步数据库连接URL，如果未配置则返回None
        """
        if not self.database_url:
            return None
        
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        return self.database_url
    
    @computed_field
    @property
    def async_redis_url(self) -> Optional[str]:
        """处理Redis URL确保兼容性
        
        Railway的Redis URL通常已经是正确格式，但确保使用redis://前缀
        
        Returns:
            Optional[str]: Redis连接URL，如果未配置则返回None
        """
        if not self.redis_url:
            return None
        
        if not self.redis_url.startswith(("redis://", "rediss://")):
            return f"redis://{self.redis_url}"
        return self.redis_url
    
    @computed_field
    @property
    def r2_config(self) -> Optional[dict[str, str]]:
        """Cloudflare R2配置字典
        
        Returns:
            Optional[dict]: R2客户端配置参数，如果未完整配置则返回None
        """
        if not all([self.endpoint_url, self.aws_access_key_id, self.aws_secret_access_key]):
            return None
        
        return {
            "service_name": self.service_name,
            "endpoint_url": self.endpoint_url,
            "aws_access_key_id": self.aws_access_key_id,
            "aws_secret_access_key": self.aws_secret_access_key,
            "region_name": self.region_name,
        }


@lru_cache
def get_settings() -> Settings:
    """获取应用配置单例
    
    使用lru_cache确保配置只被加载一次，提高性能
    
    Returns:
        Settings: 应用配置实例
    """
    return Settings()


# 导出配置实例供其他模块使用
settings = get_settings()