"""用户功能模块

提供用户管理相关的功能
包括用户CRUD操作和相关业务逻辑
"""

from .router import router
from .service import UserService

__all__ = ["router", "UserService"]