"""Alembic 环境配置

配置数据库迁移环境，支持异步数据库连接
"""

import asyncio
from logging.config import fileConfig
from typing import Any

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 导入应用配置和模型
from app.core.config import settings
from app.features.storage.models import FileRecord  # 导入所有模型以确保元数据完整

# Alembic Config 对象，提供对 .ini 文件中值的访问
config = context.config

# 解释日志配置文件的配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 添加模型的元数据对象以支持 'autogenerate'
# 从 SQLModel 导入元数据
from sqlmodel import SQLModel
target_metadata = SQLModel.metadata

# 其他从 env.py 需要的值，由需要访问脚本的值定义
# my_important_option = config.get_main_option("my_important_option")
# ... 等等


def get_database_url() -> str:
    """获取数据库连接URL
    
    优先使用环境变量中的 DATABASE_URL，
    如果不存在则使用配置文件中的默认值
    
    Returns:
        str: 数据库连接URL
    """
    # 使用应用配置中的异步数据库URL
    return settings.async_database_url


def run_migrations_offline() -> None:
    """在 'offline' 模式下运行迁移
    
    这将配置上下文仅使用 URL
    而不是 Engine，尽管这里也需要 Engine
    通过不创建 Engine 来避免创建 DBAPI 连接
    我们只需要一个 URL
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # 比较类型以检测列类型更改
        compare_type=True,
        # 比较服务器默认值
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """执行实际的迁移操作
    
    Args:
        connection: 数据库连接对象
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # 比较类型以检测列类型更改
        compare_type=True,
        # 比较服务器默认值
        compare_server_default=True,
        # 渲染项目以便在迁移中包含批处理操作
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """在异步模式下运行迁移
    
    创建异步引擎并在同步上下文中运行迁移
    """
    # 配置异步引擎
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在 'online' 模式下运行迁移
    
    在这种情况下，我们需要创建一个 Engine
    并将连接与上下文关联
    """
    # 运行异步迁移
    asyncio.run(run_async_migrations())


# 根据上下文确定运行模式
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()