"""Redis连接模块

提供Redis异步连接池和缓存操作
"""

import json
from datetime import datetime
from typing import Any, Optional, Union

import redis.asyncio as redis
from loguru import logger

from .config import settings


class RedisManager:
    """Redis管理器
    
    管理Redis连接池和提供缓存操作方法
    """
    
    def __init__(self) -> None:
        """初始化Redis管理器
        
        创建Redis连接池，配置连接参数
        如果Redis URL未配置，则跳过初始化
        """
        self.redis_pool = None
        self.redis_client = None
        
        if not settings.async_redis_url:
            logger.warning("Redis URL未配置，跳过Redis初始化")
            return
        
        self.redis_pool = redis.ConnectionPool.from_url(
            settings.async_redis_url,
            max_connections=20,  # 最大连接数
            retry_on_timeout=True,  # 超时重试
            socket_keepalive=True,  # 保持连接
            socket_keepalive_options={},
            health_check_interval=30,  # 健康检查间隔（秒）
        )
        
        self.redis_client = redis.Redis(
            connection_pool=self.redis_pool,
            decode_responses=True,  # 自动解码响应
        )
        
        logger.info("Redis连接池已初始化")
    
    async def ping(self) -> bool:
        """检查Redis连接状态
        
        Returns:
            bool: 连接是否正常
        """
        if not self.redis_client:
            logger.warning("Redis未初始化，无法检查连接")
            return False
        
        try:
            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis连接检查失败: {e}")
            return False
    
    async def close(self) -> None:
        """关闭Redis连接
        
        在应用关闭时调用，清理资源
        """
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis连接已关闭")
        else:
            logger.info("Redis未初始化，无需关闭")
    
    def _serialize_value(self, value: Any) -> str:
        """序列化值为JSON字符串
        
        处理datetime等特殊类型的序列化
        
        Args:
            value: 要序列化的值
            
        Returns:
            str: JSON字符串
        """
        def json_serializer(obj: Any) -> str:
            """JSON序列化器，处理特殊类型"""
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        return json.dumps(value, default=json_serializer, ensure_ascii=False)
    
    def _deserialize_value(self, value: str) -> Any:
        """反序列化JSON字符串为Python对象
        
        Args:
            value: JSON字符串
            
        Returns:
            Any: Python对象
        """
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    
    def _build_key(self, module: str, function: str, *args: Any) -> str:
        """构建缓存键名
        
        格式: taible:module:function:参数哈希
        
        Args:
            module: 模块名
            function: 函数名
            *args: 参数列表
            
        Returns:
            str: 缓存键名
        """
        import hashlib
        
        # 创建参数哈希
        args_str = ":".join(str(arg) for arg in args)
        args_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]
        
        return f"taible:{module}:{function}:{args_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Any]: 缓存值，不存在返回None
        """
        if not self.redis_client:
            logger.debug(f"Redis未初始化，跳过获取缓存: {key}")
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value is None:
                return None
            return self._deserialize_value(value)
        except Exception as e:
            logger.error(f"Redis获取缓存失败 {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None表示不过期
            
        Returns:
            bool: 是否设置成功
        """
        if not self.redis_client:
            logger.debug(f"Redis未初始化，跳过设置缓存: {key}")
            return False
        
        try:
            serialized_value = self._serialize_value(value)
            if ttl:
                await self.redis_client.setex(key, ttl, serialized_value)
            else:
                await self.redis_client.set(key, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Redis设置缓存失败 {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否删除成功
        """
        if not self.redis_client:
            logger.debug(f"Redis未初始化，跳过删除缓存: {key}")
            return False
        
        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis删除缓存失败 {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否存在
        """
        if not self.redis_client:
            logger.debug(f"Redis未初始化，跳过检查缓存: {key}")
            return False
        
        try:
            result = await self.redis_client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis检查缓存存在失败 {key}: {e}")
            return False
    
    async def cache_function_result(
        self,
        module: str,
        function: str,
        result: Any,
        ttl: int = None,
        *args: Any
    ) -> bool:
        """缓存函数结果
        
        Args:
            module: 模块名
            function: 函数名
            result: 函数结果
            ttl: 过期时间（秒）
            *args: 函数参数
            
        Returns:
            bool: 是否缓存成功
        """
        key = self._build_key(module, function, *args)
        cache_ttl = ttl or settings.cache_ttl_default
        return await self.set(key, result, cache_ttl)
    
    async def get_cached_function_result(
        self,
        module: str,
        function: str,
        *args: Any
    ) -> Optional[Any]:
        """获取缓存的函数结果
        
        Args:
            module: 模块名
            function: 函数名
            *args: 函数参数
            
        Returns:
            Optional[Any]: 缓存的结果，不存在返回None
        """
        key = self._build_key(module, function, *args)
        return await self.get(key)


# 全局Redis管理器实例
redis_manager = RedisManager()


# 缓存装饰器
def cache_result(module: str, ttl: Optional[int] = None):
    """缓存函数结果的装饰器
    
    Args:
        module: 模块名
        ttl: 过期时间（秒）
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 检查缓存
            cached_result = await redis_manager.get_cached_function_result(
                module, func.__name__, *args, *kwargs.values()
            )
            
            if cached_result is not None:
                logger.debug(f"缓存命中: {module}.{func.__name__}")
                return cached_result
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            await redis_manager.cache_function_result(
                module, func.__name__, result, ttl, *args, *kwargs.values()
            )
            
            logger.debug(f"缓存已更新: {module}.{func.__name__}")
            return result
        
        return wrapper
    return decorator