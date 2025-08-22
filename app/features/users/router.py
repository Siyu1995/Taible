"""用户管理路由模块

提供用户相关的API接口
包括用户创建、查询、列表等功能
"""

from fastapi import APIRouter, HTTPException
from typing import List
from loguru import logger

from app.shared.schemas import (
    SuccessResponse, 
    ErrorResponse, 
    UserCreate, 
    UserResponse
)
from app.shared.exceptions import NotFoundError, ValidationError
from .service import UserService

# 创建路由器实例
router = APIRouter()

# 用户服务实例
user_service = UserService()


@router.get("/", response_model=SuccessResponse[List[UserResponse]])
async def get_users():
    """获取用户列表
    
    返回所有用户的列表信息
    用于展示用户管理页面
    """
    try:
        users = await user_service.get_all_users()
        logger.info(f"获取用户列表成功，共{len(users)}个用户")
        
        return SuccessResponse(
            data=users,
            message=f"获取用户列表成功，共{len(users)}个用户"
        )
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户列表失败")


@router.get("/{user_id}", response_model=SuccessResponse[UserResponse])
async def get_user(user_id: int):
    """根据ID获取用户信息
    
    Args:
        user_id: 用户ID
        
    Returns:
        用户详细信息
        
    Raises:
        NotFoundError: 用户不存在时抛出
    """
    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise NotFoundError(f"用户ID {user_id} 不存在")
            
        logger.info(f"获取用户信息成功: {user.name} (ID: {user_id})")
        
        return SuccessResponse(
            data=user,
            message="获取用户信息成功"
        )
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户信息失败")


@router.post("/", response_model=SuccessResponse[UserResponse], status_code=201)
async def create_user(user_data: UserCreate):
    """创建新用户
    
    Args:
        user_data: 用户创建数据
        
    Returns:
        创建的用户信息
        
    Raises:
        ValidationError: 数据验证失败时抛出
    """
    try:
        # 验证邮箱是否已存在
        existing_user = await user_service.get_user_by_email(user_data.email)
        if existing_user:
            raise ValidationError(f"邮箱 {user_data.email} 已被使用")
            
        # 创建用户
        new_user = await user_service.create_user(user_data)
        logger.info(f"创建用户成功: {new_user.name} (ID: {new_user.id})")
        
        return SuccessResponse(
            data=new_user,
            message="创建用户成功",
            code=201
        )
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"创建用户失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建用户失败")


@router.delete("/{user_id}", response_model=SuccessResponse[None])
async def delete_user(user_id: int):
    """删除用户
    
    Args:
        user_id: 要删除的用户ID
        
    Returns:
        删除成功的响应
        
    Raises:
        NotFoundError: 用户不存在时抛出
    """
    try:
        # 检查用户是否存在
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise NotFoundError(f"用户ID {user_id} 不存在")
            
        # 删除用户
        await user_service.delete_user(user_id)
        logger.info(f"删除用户成功: {user.name} (ID: {user_id})")
        
        return SuccessResponse(
            data=None,
            message="删除用户成功"
        )
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"删除用户失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除用户失败")