"""自定义异常类定义

定义应用中使用的各种自定义异常
提供统一的错误处理机制
"""

from fastapi import HTTPException
from typing import Any, Optional


class BaseAPIException(HTTPException):
    """API异常基类
    
    所有自定义API异常都应该继承这个类
    提供统一的异常处理接口
    """
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_type: str = "APIError",
        headers: Optional[dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_type = error_type


class ValidationError(BaseAPIException):
    """数据验证异常
    
    当请求数据验证失败时抛出
    """
    
    def __init__(self, detail: str = "数据验证失败"):
        super().__init__(
            status_code=422,
            detail=detail,
            error_type="ValidationError"
        )


class NotFoundError(BaseAPIException):
    """资源不存在异常
    
    当请求的资源不存在时抛出
    """
    
    def __init__(self, detail: str = "资源不存在"):
        super().__init__(
            status_code=404,
            detail=detail,
            error_type="NotFoundError"
        )


class UnauthorizedError(BaseAPIException):
    """未授权异常
    
    当用户未登录或token无效时抛出
    """
    
    def __init__(self, detail: str = "未授权访问"):
        super().__init__(
            status_code=401,
            detail=detail,
            error_type="UnauthorizedError"
        )


class ForbiddenError(BaseAPIException):
    """禁止访问异常
    
    当用户权限不足时抛出
    """
    
    def __init__(self, detail: str = "权限不足"):
        super().__init__(
            status_code=403,
            detail=detail,
            error_type="ForbiddenError"
        )


class ConflictError(BaseAPIException):
    """资源冲突异常
    
    当资源已存在或发生冲突时抛出
    """
    
    def __init__(self, detail: str = "资源冲突"):
        super().__init__(
            status_code=409,
            detail=detail,
            error_type="ConflictError"
        )


class InternalServerError(BaseAPIException):
    """服务器内部错误异常
    
    当服务器发生内部错误时抛出
    """
    
    def __init__(self, detail: str = "服务器内部错误"):
        super().__init__(
            status_code=500,
            detail=detail,
            error_type="InternalServerError"
        )