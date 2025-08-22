#!/usr/bin/env python3
"""应用启动脚本

用于本地开发和生产环境启动FastAPI应用
支持不同的启动模式和配置
"""

import os
import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings


def start_dev():
    """启动开发服务器
    
    使用uvicorn启动开发服务器，启用热重载
    适用于本地开发环境
    """
    import uvicorn
    
    print(f"🔧 启动开发服务器...")
    print(f"📝 API文档: http://{settings.host}:{settings.port}/docs")
    print(f"💚 健康检查: http://{settings.host}:{settings.port}/health")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower(),
        access_log=True
    )


def start_prod():
    """启动生产服务器
    
    使用uvicorn启动生产服务器，优化性能配置
    适用于生产环境部署
    """
    import uvicorn
    
    print(f"🚀 启动生产服务器...")
    print(f"🌍 服务地址: http://{settings.host}:{settings.port}")
    
    # 生产环境配置
    workers = int(os.getenv("WORKERS", "1"))
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        workers=workers,
        log_level=settings.log_level.lower(),
        access_log=True,
        loop="uvloop" if sys.platform != "win32" else "asyncio"
    )


def main():
    """主函数
    
    解析命令行参数并启动相应的服务器
    """
    parser = argparse.ArgumentParser(description="Taible FastAPI应用启动脚本")
    parser.add_argument(
        "--mode",
        choices=["dev", "prod"],
        default="dev",
        help="启动模式: dev(开发) 或 prod(生产)"
    )
    parser.add_argument(
        "--host",
        default=settings.host,
        help=f"服务器主机地址 (默认: {settings.host})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.port,
        help=f"服务器端口 (默认: {settings.port})"
    )
    
    args = parser.parse_args()
    
    # 更新配置
    settings.host = args.host
    settings.port = args.port
    
    # 确保日志目录存在
    log_dir = Path(settings.log_file).parent
    log_dir.mkdir(exist_ok=True)
    
    # 启动服务器
    if args.mode == "dev":
        start_dev()
    else:
        start_prod()


if __name__ == "__main__":
    main()