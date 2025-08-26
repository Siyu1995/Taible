# Taible Storage API

基于 FastAPI 的文件存储服务，支持 Cloudflare R2 对象存储，部署在 Railway 平台。

## 技术栈

- **Web框架**: FastAPI + Uvicorn
- **数据库**: PostgreSQL (异步)
- **缓存**: Redis (异步)
- **对象存储**: Cloudflare R2
- **部署平台**: Railway
- **包管理**: uv

## 项目结构

```
project_root/
├── pyproject.toml          # 项目配置和依赖
├── .env.example            # 环境变量模板
├── README.md               # 项目说明
├── app/
│   ├── main.py            # FastAPI应用入口
│   ├── core/              # 核心模块
│   │   ├── config.py      # 配置管理
│   │   ├── database.py    # 数据库连接
│   │   └── redis.py       # Redis连接
│   ├── shared/            # 共享模块
│   │   └── schemas/       # 通用数据模式
│   ├── features/          # 功能模块
│   │   └── storage/       # 存储功能
│   │       ├── models.py  # 数据模型
│   │       ├── service.py # 业务逻辑
│   │       └── router.py  # 路由定义
│   └── middleware/        # 中间件
├── tests/                 # 测试文件
├── logs/                  # 日志文件
└── scripts/               # 工具脚本
    └── test_upload.py     # 上传测试脚本
```

## 快速开始

### 1. 环境准备

```bash
# 安装 uv (如果还没有安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境
uv venv

# 激活虚拟环境 (Windows)
.venv\Scripts\activate

# 激活虚拟环境 (Linux/macOS)
source .venv/bin/activate

# 安装依赖
uv sync
```

### 2. 数据库迁移

项目使用 Alembic 进行数据库版本管理：

```bash
# 初始化迁移环境（首次运行）
python scripts/manage_migrations.py init

# 创建新迁移（当修改模型后）
python scripts/manage_migrations.py create "描述你的更改"

# 升级数据库到最新版本
python scripts/manage_migrations.py upgrade

# 查看当前数据库版本
python scripts/manage_migrations.py current

# 查看迁移历史
python scripts/manage_migrations.py history
```

### 3. 环境配置

复制环境变量模板并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下变量：

```env
# Cloudflare R2配置 (必需)
R2_ACCESS_KEY_ID=your_r2_access_key_id
R2_SECRET_ACCESS_KEY=your_r2_secret_access_key
R2_BUCKET_NAME=your_bucket_name
R2_ENDPOINT_URL=https://your_account_id.r2.cloudflarestorage.com
R2_PUBLIC_URL=https://your_custom_domain.com

# 本地开发数据库 (可选，Railway会自动注入)
DATABASE_URL=postgresql://user:password@localhost:5432/taible
REDIS_URL=redis://localhost:6379/0
```

### 4. 本地运行

```bash
# 启动开发服务器
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 或者直接运行
uv run python -m app.main
```

访问 API 文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

### 5. 测试文件上传

```bash
# 使用测试脚本上传文件
uv run python scripts/test_upload.py

# 或上传指定文件
uv run python scripts/test_upload.py /path/to/your/file.txt
```

## 数据库迁移管理

### 常用迁移命令

```bash
# 创建新迁移（修改模型后）
python scripts/manage_migrations.py create "添加新字段"

# 升级到最新版本
python scripts/manage_migrations.py upgrade

# 降级到上一个版本
python scripts/manage_migrations.py downgrade -1

# 降级到指定版本
python scripts/manage_migrations.py downgrade <revision_id>

# 标记数据库版本（用于现有数据库）
python scripts/manage_migrations.py stamp head
```

### 迁移最佳实践

1. **修改模型后立即创建迁移**：确保数据库结构与代码同步
2. **审查生成的迁移文件**：检查自动生成的迁移是否正确
3. **测试迁移**：在开发环境中测试升级和降级操作
4. **备份生产数据**：在生产环境执行迁移前备份数据
5. **渐进式部署**：大型更改分解为多个小迁移

## API 端点

### 存储相关

- `POST /api/storage/presigned-upload-url` - 获取预签名上传URL
- `GET /api/storage/files/{file_id}` - 获取文件记录
- `PATCH /api/storage/files/{file_id}` - 更新文件记录
- `GET /api/storage/files/{file_id}/download-url` - 获取下载URL
- `POST /api/storage/files/{file_id}/complete` - 标记上传完成

### 系统相关

- `GET /` - API信息
- `GET /health` - 健康检查

## Railway 部署

### 1. 准备部署

1. 在 Railway 创建新项目
2. 添加 PostgreSQL 和 Redis 服务
3. 连接 GitHub 仓库

### 2. 环境变量配置

在 Railway 项目设置中配置以下环境变量：

```env
# Railway会自动注入这些变量
# DATABASE_URL=postgresql://...
# REDIS_URL=redis://...

# 需要手动配置的变量
APP_NAME=Taible Storage API
APP_VERSION=1.0.0
DEBUG=false

# Cloudflare R2配置
R2_ACCESS_KEY_ID=your_r2_access_key_id
R2_SECRET_ACCESS_KEY=your_r2_secret_access_key
R2_BUCKET_NAME=your_bucket_name
R2_ENDPOINT_URL=https://your_account_id.r2.cloudflarestorage.com
R2_PUBLIC_URL=https://your_custom_domain.com

# 缓存配置
CACHE_TTL_USER=3600
CACHE_TTL_PRODUCT=1800
CACHE_TTL_CONFIG=7200
CACHE_TTL_STATS=900
CACHE_TTL_SEARCH=300

# 文件上传限制
MAX_FILE_SIZE=104857600
ALLOWED_FILE_TYPES=jpg,jpeg,png,gif,pdf,doc,docx,txt,zip
```

### 3. 部署配置

Railway 会自动检测 `pyproject.toml` 并使用 uv 进行部署。确保项目根目录包含：

- `pyproject.toml` - 依赖配置
- `app/main.py` - 应用入口

## Cloudflare R2 配置

### 1. 创建 R2 存储桶

1. 登录 Cloudflare 控制台
2. 进入 R2 Object Storage
3. 创建新的存储桶
4. 配置 CORS 策略（如需要）

### 2. 获取 API 凭证

1. 进入 "Manage R2 API tokens"
2. 创建新的 API token
3. 记录 Access Key ID 和 Secret Access Key

### 3. 自定义域名（可选）

1. 在存储桶设置中配置自定义域名
2. 更新 `R2_PUBLIC_URL` 环境变量

## 文件上传流程

1. **获取预签名URL**: 客户端调用 `/api/storage/presigned-upload-url`
2. **直接上传**: 使用返回的预签名URL直接上传到R2
3. **标记完成**: 上传完成后调用 `/api/storage/files/{file_id}/complete`
4. **获取文件**: 可通过 `/api/storage/files/{file_id}/download-url` 获取下载链接

## 开发指南

### 代码规范

- 使用 `black` 进行代码格式化
- 使用 `ruff` 进行代码检查
- 使用 `mypy` 进行类型检查

```bash
# 代码格式化
uv run black app/ tests/ scripts/

# 代码检查
uv run ruff check app/ tests/ scripts/

# 类型检查
uv run mypy app/
```

### 测试

```bash
# 运行测试
uv run pytest

# 运行测试并生成覆盖率报告
uv run pytest --cov=app
```

### 日志

应用使用 `loguru` 进行日志记录，日志文件保存在 `logs/` 目录：

- 按天轮转
- 保留30天
- JSON格式便于分析

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查 `DATABASE_URL` 是否正确
   - 确认数据库服务是否运行

2. **Redis连接失败**
   - 检查 `REDIS_URL` 是否正确
   - 确认Redis服务是否运行

3. **R2上传失败**
   - 检查R2凭证是否正确
   - 确认存储桶权限设置
   - 检查CORS配置

4. **Railway部署失败**
   - 检查环境变量配置
   - 查看部署日志
   - 确认依赖安装正确

### 调试模式

设置 `DEBUG=true` 启用调试模式，会显示详细的错误信息。

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！