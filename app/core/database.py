"""数据库连接模块

提供SQLAlchemy异步数据库连接和会话管理
"""

import asyncio
from typing import AsyncGenerator

from alembic import command
from alembic.config import Config
from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel

from .config import settings


class DatabaseManager:
    """数据库管理器
    
    管理异步数据库引擎和会话工厂
    """
    
    def __init__(self) -> None:
        """初始化数据库管理器
        
        创建异步引擎和会话工厂，配置连接池参数
        """
        self.engine = create_async_engine(
            settings.async_database_url,
            echo=settings.debug,  # 调试模式下打印SQL语句
            pool_size=10,  # 连接池大小
            max_overflow=20,  # 最大溢出连接数
            pool_pre_ping=True,  # 连接前ping检查
            pool_recycle=3600,  # 连接回收时间（秒）
        )
        
        self.async_session = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,  # 提交后不过期对象
            autoflush=True,  # 自动刷新
            autocommit=False,  # 手动提交
        )
        
        logger.info(f"数据库引擎已初始化: {settings.async_database_url.split('@')[1] if '@' in settings.async_database_url else 'localhost'}")
    
    async def run_migrations(self) -> None:
        """运行数据库迁移
        
        使用 Alembic 自动运行数据库迁移到最新版本。
        这比直接 create_all 更安全，支持增量更新而不会丢失数据。
        """
        try:
            # 在单独的线程中运行 Alembic 迁移，因为 Alembic 是同步的
            await asyncio.get_event_loop().run_in_executor(
                None, self._run_alembic_upgrade
            )
            logger.info("数据库迁移完成")
        except Exception as e:
            logger.error(f"数据库迁移失败: {e}")
            raise
    
    def _run_alembic_upgrade(self) -> None:
        """在执行器中运行 Alembic 升级
        
        这个方法在单独的线程中运行，避免阻塞异步事件循环
        """
        try:
            # 创建 Alembic 配置
            alembic_cfg = Config("alembic.ini")
            
            # 运行迁移到最新版本
            command.upgrade(alembic_cfg, "head")
            
        except Exception as e:
            logger.error(f"Alembic 升级失败: {e}")
            raise
    
    async def create_tables_fallback(self) -> None:
        """备用的表创建方法
        
        仅在 Alembic 迁移失败时使用，直接创建所有表。
        注意：这种方法不支持数据迁移，可能会导致数据丢失。
        """
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
            logger.warning("使用备用方法创建数据库表（不推荐用于生产环境）")
        except Exception as e:
            logger.error(f"备用表创建方法失败: {e}")
            raise
    
    async def close(self) -> None:
        """关闭数据库连接
        
        在应用关闭时调用，清理资源
        """
        await self.engine.dispose()
        logger.info("数据库连接已关闭")
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话
        
        用作FastAPI依赖注入，自动管理会话生命周期
        
        Yields:
            AsyncSession: 数据库会话
        """
        async with self.async_session() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"数据库会话错误: {e}")
                raise
            finally:
                await session.close()


# 全局数据库管理器实例
db_manager = DatabaseManager()


# FastAPI依赖注入函数
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的依赖注入函数
    
    在FastAPI路由中使用: db: AsyncSession = Depends(get_db)
    
    Yields:
        AsyncSession: 数据库会话
    """
    async for session in db_manager.get_session():
        yield session