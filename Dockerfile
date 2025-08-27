# 多阶段构建Dockerfile for FastAPI应用
# 使用Python 3.12官方镜像作为基础镜像

# 第一阶段：构建阶段
FROM python:3.12-slim as builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖（构建时需要的包）
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装uv（更快的Python包管理器）
RUN pip install --no-cache-dir uv

# 复制依赖文件
COPY pyproject.toml ./
# 注意：如果有uv.lock文件，也需要复制
# COPY uv.lock ./

# 使用uv sync安装依赖（推荐方式，更快且确保版本一致性）
# 如果没有uv.lock文件，使用pip install作为fallback
RUN if [ -f "uv.lock" ]; then \
        uv sync --frozen --no-dev; \
    else \
        uv pip install --system --no-cache -e .; \
    fi

# 第二阶段：运行阶段
FROM python:3.12-slim as runtime

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:$PATH" \
    PORT=8000

# 创建非root用户（安全最佳实践）
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 安装运行时系统依赖
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 设置工作目录
WORKDIR /app

# 从构建阶段复制Python包（uv安装到系统路径）
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY start.py ./

# 更改文件所有权
RUN chown -R appuser:appuser /app

# 切换到非root用户
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:$PORT/health', timeout=10)"

# 暴露端口
EXPOSE $PORT

# 启动命令
# Railway会自动设置PORT环境变量，我们使用uvicorn直接启动
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --log-level info"]