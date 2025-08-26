#!/usr/bin/env python3
"""Railway部署启动脚本

用于在Railway平台上启动FastAPI应用
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """启动FastAPI应用
    
    从环境变量获取端口号，默认使用8000
    """
    import uvicorn
    
    # 获取端口号，Railway会设置PORT环境变量
    port = int(os.getenv("PORT", 8000))
    
    # 启动应用
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        # 生产环境不使用reload
        reload=False,
        # 设置工作进程数（Railway推荐单进程）
        workers=1,
        # 设置日志级别
        log_level="info",
        # 启用访问日志
        access_log=True
    )

if __name__ == "__main__":
    main()