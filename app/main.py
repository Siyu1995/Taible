"""FastAPI应用主入口文件

配置和启动FastAPI应用
集成路由、中间件、异常处理等组件
"""

import time
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import sys

from app.core.config import settings
from app.shared.schemas import SuccessResponse, ErrorResponse, HealthCheck
from app.shared.exceptions import BaseAPIException
from app.features.users.router import router as users_router

# 配置loguru日志
logger.remove()  # 移除默认处理器
logger.add(
    sys.stdout,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>"
)
logger.add(
    settings.log_file,
    rotation="1 day",
    retention="30 days",
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    serialize=True  # JSON格式输出到文件
)

# 应用启动时间，用于计算运行时长
app_start_time = datetime.now()

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="一个用于Railway部署测试的简单FastAPI项目",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件
    
    记录每个HTTP请求的详细信息
    包括请求方法、路径、处理时间等
    """
    start_time = time.time()
    
    # 记录请求开始
    logger.info(
        f"请求开始: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": request.client.host if request.client else "unknown"
        }
    )
    
    # 处理请求
    response = await call_next(request)
    
    # 计算处理时间
    process_time = time.time() - start_time
    
    # 记录请求完成
    logger.info(
        f"请求完成: {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time": process_time
        }
    )
    
    # 添加处理时间到响应头
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


@app.exception_handler(BaseAPIException)
async def api_exception_handler(request: Request, exc: BaseAPIException):
    """自定义API异常处理器
    
    统一处理自定义的API异常
    返回标准格式的错误响应
    """
    logger.error(
        f"API异常: {exc.error_type} - {exc.detail}",
        extra={
            "error_type": exc.error_type,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            message=exc.detail,
            code=exc.status_code,
            error_type=exc.error_type
        ).model_dump()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器
    
    处理FastAPI的标准HTTP异常
    返回统一格式的错误响应
    """
    logger.error(
        f"HTTP异常: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            message=exc.detail,
            code=exc.status_code,
            error_type="HTTPException"
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器
    
    处理所有未被捕获的异常
    避免向用户暴露敏感的错误信息
    """
    logger.error(
        f"未处理异常: {type(exc).__name__} - {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "path": request.url.path
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            message="服务器内部错误",
            code=500,
            error_type="InternalServerError"
        ).model_dump()
    )


@app.get("/", response_model=SuccessResponse[dict])
async def root():
    """根路径接口
    
    返回应用基本信息
    用于验证服务是否正常运行
    """
    return SuccessResponse(
        data={
            "app_name": settings.app_name,
            "version": settings.app_version,
            "message": "欢迎使用Taible FastAPI测试应用！",
            "docs_url": "/docs",
            "redoc_url": "/redoc"
        },
        message="应用运行正常"
    )


@app.get("/health", response_model=SuccessResponse[HealthCheck])
async def health_check():
    """健康检查接口
    
    用于监控系统健康状态
    Railway等部署平台会使用此接口检查服务状态
    """
    uptime = datetime.now() - app_start_time
    uptime_str = f"{uptime.days}天 {uptime.seconds // 3600}小时 {(uptime.seconds % 3600) // 60}分钟"
    
    health_data = HealthCheck(
        status="healthy",
        version=settings.app_version,
        uptime=uptime_str
    )
    
    return SuccessResponse(
        data=health_data,
        message="系统健康状态良好"
    )


# 注册路由
app.include_router(
    users_router,
    prefix=f"{settings.api_v1_prefix}/users",
    tags=["用户管理"]
)


@app.on_event("startup")
async def startup_event():
    """应用启动事件
    
    在应用启动时执行初始化操作
    记录启动信息和配置
    """
    logger.info(f"🚀 {settings.app_name} v{settings.app_version} 启动成功")
    logger.info(f"📝 API文档地址: http://{settings.host}:{settings.port}/docs")
    logger.info(f"🔍 ReDoc文档地址: http://{settings.host}:{settings.port}/redoc")
    logger.info(f"💚 健康检查地址: http://{settings.host}:{settings.port}/health")
    logger.info(f"🌍 CORS允许的源: {settings.cors_origins}")
    logger.info(f"📊 日志级别: {settings.log_level}")
    logger.info(f"📁 日志文件: {settings.log_file}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件
    
    在应用关闭时执行清理操作
    记录关闭信息
    """
    uptime = datetime.now() - app_start_time
    logger.info(f"👋 {settings.app_name} 正在关闭，运行时长: {uptime}")


if __name__ == "__main__":
    """直接运行脚本时启动开发服务器
    
    用于本地开发和测试
    生产环境应该使用uvicorn命令启动
    """
    import uvicorn
    
    logger.info("🔧 开发模式启动")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )