"""用户服务层

实现用户相关的业务逻辑
提供数据访问和业务处理功能
"""

from typing import List, Optional
from datetime import datetime
from loguru import logger

from app.shared.schemas import UserCreate, UserResponse


class UserService:
    """用户服务类
    
    处理用户相关的业务逻辑
    在实际项目中这里会连接数据库进行CRUD操作
    为了简化测试，这里使用内存存储
    """
    
    def __init__(self):
        """初始化用户服务
        
        创建内存存储和示例数据
        在生产环境中应该连接真实数据库
        """
        # 模拟数据库存储（内存中的用户列表）
        self._users: List[dict] = [
            {
                "id": 1,
                "name": "张三",
                "email": "zhangsan@example.com",
                "age": 25,
                "created_at": datetime.now()
            },
            {
                "id": 2,
                "name": "李四",
                "email": "lisi@example.com",
                "age": 30,
                "created_at": datetime.now()
            }
        ]
        self._next_id = 3  # 下一个用户ID
        
        logger.info("用户服务初始化完成，加载了示例数据")
    
    async def get_all_users(self) -> List[UserResponse]:
        """获取所有用户
        
        Returns:
            用户响应列表
        """
        logger.debug(f"获取所有用户，当前用户数量: {len(self._users)}")
        
        # 将字典数据转换为Pydantic模型
        return [UserResponse(**user) for user in self._users]
    
    async def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        """根据ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户响应对象，如果不存在则返回None
        """
        logger.debug(f"查找用户ID: {user_id}")
        
        for user in self._users:
            if user["id"] == user_id:
                return UserResponse(**user)
        
        logger.debug(f"用户ID {user_id} 不存在")
        return None
    
    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """根据邮箱获取用户
        
        Args:
            email: 用户邮箱
            
        Returns:
            用户响应对象，如果不存在则返回None
        """
        logger.debug(f"查找用户邮箱: {email}")
        
        for user in self._users:
            if user["email"] == email:
                return UserResponse(**user)
        
        logger.debug(f"用户邮箱 {email} 不存在")
        return None
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """创建新用户
        
        Args:
            user_data: 用户创建数据
            
        Returns:
            创建的用户响应对象
        """
        logger.debug(f"创建用户: {user_data.name} ({user_data.email})")
        
        # 创建新用户字典
        new_user = {
            "id": self._next_id,
            "name": user_data.name,
            "email": user_data.email,
            "age": user_data.age,
            "created_at": datetime.now()
        }
        
        # 添加到用户列表
        self._users.append(new_user)
        self._next_id += 1
        
        logger.info(f"用户创建成功: {new_user['name']} (ID: {new_user['id']})")
        
        return UserResponse(**new_user)
    
    async def delete_user(self, user_id: int) -> bool:
        """删除用户
        
        Args:
            user_id: 要删除的用户ID
            
        Returns:
            删除是否成功
        """
        logger.debug(f"删除用户ID: {user_id}")
        
        for i, user in enumerate(self._users):
            if user["id"] == user_id:
                deleted_user = self._users.pop(i)
                logger.info(f"用户删除成功: {deleted_user['name']} (ID: {user_id})")
                return True
        
        logger.warning(f"尝试删除不存在的用户ID: {user_id}")
        return False
    
    async def get_user_count(self) -> int:
        """获取用户总数
        
        Returns:
            用户总数
        """
        count = len(self._users)
        logger.debug(f"当前用户总数: {count}")
        return count