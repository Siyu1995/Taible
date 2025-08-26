"""共享数据模式

定义通用的API响应格式和数据验证模式
"""

from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field


T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    """统一API响应格式
    
    提供标准化的API响应结构，包含成功状态、数据、消息和状态码
    """
    success: bool = Field(description="操作是否成功")
    data: Optional[T] = Field(default=None, description="响应数据")
    message: str = Field(description="响应消息")
    code: int = Field(description="HTTP状态码")
    error_type: Optional[str] = Field(default=None, description="错误类型")
    
    class Config:
        """Pydantic配置"""
        json_encoders = {
            # 处理特殊类型的JSON序列化
        }


class PaginationParams(BaseModel):
    """分页参数
    
    用于列表查询的分页控制
    """
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页数量")
    
    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.size


class PaginationResponse(BaseModel, Generic[T]):
    """分页响应格式
    
    包含分页数据和元信息
    """
    items: list[T] = Field(description="数据列表")
    total: int = Field(description="总数量")
    page: int = Field(description="当前页码")
    size: int = Field(description="每页数量")
    pages: int = Field(description="总页数")
    
    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        size: int
    ) -> "PaginationResponse[T]":
        """创建分页响应
        
        Args:
            items: 数据列表
            total: 总数量
            page: 当前页码
            size: 每页数量
            
        Returns:
            PaginationResponse[T]: 分页响应对象
        """
        pages = (total + size - 1) // size  # 向上取整
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )


class HealthCheckResponse(BaseModel):
    """健康检查响应
    
    用于系统健康状态检查
    """
    status: str = Field(description="服务状态")
    timestamp: str = Field(description="检查时间")
    version: str = Field(description="应用版本")
    database: bool = Field(description="数据库连接状态")
    redis: bool = Field(description="Redis连接状态")
    storage: bool = Field(description="存储服务状态")