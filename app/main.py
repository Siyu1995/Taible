"""FastAPI应用主入口

配置应用实例、中间件、路由和生命周期事件
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.config import settings
from app.core.database import db_manager
from app.core.redis import redis_manager
from app.features.storage.router import router as storage_router
from app.shared.schemas import APIResponse, HealthCheckResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理
    
    在应用启动时初始化数据库和Redis连接，
    在应用关闭时清理资源
    """
    # 启动时初始化
    logger.info("正在启动FastAPI应用...")
    
    try:
        # 数据库和Redis在初始化时已经自动连接
        logger.info("检查数据库连接...")
        if db_manager.engine:
            logger.info("数据库连接已就绪")
        else:
            logger.warning("数据库未配置，跳过数据库相关操作")
        
        logger.info("检查Redis连接...")
        if redis_manager.redis_client:
            logger.info("Redis连接已就绪")
        else:
            logger.warning("Redis未配置，跳过Redis相关操作")
        
        # 运行数据库迁移（仅在数据库已配置时）
        if db_manager.engine:
            try:
                await db_manager.run_migrations()
                logger.info("数据库迁移完成")
            except Exception as migration_error:
                logger.warning(f"数据库迁移失败，尝试使用备用方法: {migration_error}")
                # 如果迁移失败，使用备用方法（仅适用于开发环境）
                if settings.debug:
                    await db_manager.create_tables_fallback()
                    logger.info("使用备用方法完成数据库表创建")
                else:
                    # 生产环境下迁移失败应该停止启动
                    logger.error("生产环境下数据库迁移失败，应用启动终止")
                    raise
        
        logger.info("应用启动完成")
        
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise
    
    yield
    
    # 关闭时清理资源
    logger.info("正在关闭FastAPI应用...")
    
    try:
        await redis_manager.close()
        logger.info("Redis连接已关闭")
        
        await db_manager.close()
        logger.info("数据库连接已关闭")
        
        logger.info("应用关闭完成")
        
    except Exception as e:
        logger.error(f"应用关闭时出错: {e}")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.app_name,
    description="基于FastAPI的文件存储服务，支持Cloudflare R2对象存储",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)


# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP异常处理器
    
    将HTTPException转换为统一的API响应格式
    """
    logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=APIResponse(
            success=False,
            data=None,
            message=exc.detail,
            code=exc.status_code,
            error_type="HTTPException"
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器
    
    处理未捕获的异常，避免暴露内部错误信息
    """
    logger.error(f"未处理的异常: {type(exc).__name__}: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content=APIResponse(
            success=False,
            data=None,
            message="服务器内部错误" if not settings.debug else str(exc),
            code=500,
            error_type=type(exc).__name__
        ).model_dump()
    )


# 健康检查端点
@app.get(
    "/health",
    response_model=APIResponse[HealthCheckResponse],
    summary="健康检查",
    description="检查应用和各个服务的健康状态"
)
async def health_check() -> APIResponse[HealthCheckResponse]:
    """健康检查端点
    
    检查数据库、Redis和存储服务的连接状态
    
    Returns:
        APIResponse[HealthCheckResponse]: 健康检查结果
    """
    # 检查数据库连接
    database_healthy = False
    try:
        if db_manager.async_session:
            from sqlalchemy import text
            async with db_manager.get_session() as session:
                await session.execute(text("SELECT 1"))
            database_healthy = True
        else:
            logger.info("数据库未配置，跳过健康检查")
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
    
    # 检查Redis连接
    redis_healthy = False
    try:
        if redis_manager.redis_client:
            await redis_manager.ping()
            redis_healthy = True
        else:
            logger.info("Redis未配置，跳过健康检查")
    except Exception as e:
        logger.error(f"Redis健康检查失败: {e}")
    
    # 检查存储服务（简单检查配置是否完整）
    r2_config = settings.r2_config
    storage_healthy = bool(r2_config and all([
        r2_config.get('aws_access_key_id'),
        r2_config.get('aws_secret_access_key'),
        settings.r2_bucket_name,
        r2_config.get('endpoint_url')
    ]))
    
    # 整体健康状态
    overall_healthy = database_healthy and redis_healthy and storage_healthy
    
    health_data = HealthCheckResponse(
        status="healthy" if overall_healthy else "unhealthy",
        timestamp=datetime.utcnow().isoformat(),
        version=settings.app_version,
        database=database_healthy,
        redis=redis_healthy,
        storage=storage_healthy
    )
    
    return APIResponse(
        success=overall_healthy,
        data=health_data,
        message="健康检查完成",
        code=200 if overall_healthy else 503
    )


# 根路径端点
@app.get(
    "/",
    response_model=APIResponse[dict],
    summary="API信息",
    description="获取API基本信息"
)
async def root() -> APIResponse[dict]:
    """根路径端点
    
    返回API的基本信息
    
    Returns:
        APIResponse[dict]: API信息
    """
    return APIResponse(
        success=True,
        data={
            "name": settings.app_name,
            "version": settings.app_version,
            "description": "基于FastAPI的文件存储服务",
            "docs_url": "/docs",
            "health_url": "/health"
        },
        message="欢迎使用文件存储API",
        code=200
    )


# 注册路由
app.include_router(
    storage_router,
    prefix="/api/storage",
    tags=["文件存储"]
)


if __name__ == "__main__":
    import uvicorn
    
    # 配置日志
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        serialize=True
    )
    
    logger.info(f"启动开发服务器: {settings.app_name} v{settings.app_version}")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug"
    )