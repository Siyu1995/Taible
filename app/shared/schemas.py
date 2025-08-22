"""共享的Pydantic模式定义

定义统一的API响应格式和通用数据模型
"""

from pydantic import BaseModel, Field
from typing import Any, Optional, Generic, TypeVar
from datetime import datetime

# 泛型类型变量，用于响应数据
DataType = TypeVar('DataType')


class BaseResponse(BaseModel, Generic[DataType]):
    """统一API响应格式
    
    所有API接口都应该返回这种格式的响应
    确保前端能够统一处理响应数据
    """
    
    success: bool = Field(..., description="请求是否成功")
    data: Optional[DataType] = Field(None, description="响应数据")
    message: str = Field(..., description="响应消息")
    code: int = Field(..., description="响应状态码")
    error_type: Optional[str] = Field(None, description="错误类型")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间戳")


class SuccessResponse(BaseResponse[DataType]):
    """成功响应模式
    
    用于创建标准的成功响应
    """
    
    success: bool = True
    code: int = 200
    message: str = "操作成功"


class ErrorResponse(BaseResponse[None]):
    """错误响应模式
    
    用于创建标准的错误响应
    """
    
    success: bool = False
    data: None = None
    

class HealthCheck(BaseModel):
    """健康检查响应模式
    
    用于系统健康状态检查
    """
    
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="应用版本")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")
    uptime: str = Field(..., description="运行时间")


class UserBase(BaseModel):
    """用户基础模式
    
    定义用户的基本属性
    """
    
    name: str = Field(..., min_length=1, max_length=50, description="用户姓名")
    email: str = Field(..., description="用户邮箱")
    age: Optional[int] = Field(None, ge=0, le=150, description="用户年龄")


class UserCreate(UserBase):
    """创建用户请求模式
    
    用于接收创建用户的请求数据
    """
    pass


class UserResponse(UserBase):
    """用户响应模式
    
    用于返回用户信息
    """
    
    id: int = Field(..., description="用户ID")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        """Pydantic v2配置
        
        from_attributes: 允许从ORM对象创建模式实例
        """
        from_attributes = True