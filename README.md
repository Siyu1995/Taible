# Taible FastAPI Test

一个用于Railway部署测试的简单FastAPI项目。

## 功能特性

- 基础的FastAPI应用
- 健康检查接口
- 用户管理API
- 结构化日志记录
- Railway部署支持

## 本地开发

```bash
# 安装依赖
uv sync

# 启动开发服务器
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 部署

本项目支持Railway一键部署。