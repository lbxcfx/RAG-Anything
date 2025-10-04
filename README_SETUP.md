# RAG-Anything 系统部署指南

## 系统架构概览

本项目是一个完整的多模态RAG知识管理平台，包含以下组件：

### 后端服务 (FastAPI)
- **端口**: 8000 (主API服务)
- **功能**:
  - 用户认证与授权
  - 模型配置管理 (LLM/VLM/Embedding/Rerank)
  - 知识库管理
  - 文档处理与向量化
  - 智能问答
  - 知识图谱构建

### 前端应用 (Vue 3 + TypeScript)
- **端口**: 5173 (开发环境) / 80 (生产环境)
- **技术栈**: Vue 3, TypeScript, Element Plus, Vite
- **功能**:
  - 用户登录/注册
  - 模型配置管理界面
  - 知识库创建与管理
  - 文档上传与处理流程可视化
  - 多模态智能问答
  - 知识图谱可视化

### 数据服务
- **PostgreSQL**: 主数据库 (端口 5432)
- **Redis**: 缓存与消息队列 (端口 6379)
- **Neo4j**: 知识图谱数据库 (端口 7474/7687)
- **Qdrant**: 向量数据库 (端口 6333)

### 异步任务处理
- **Celery Worker**: 文档处理任务
- **Celery Beat**: 定时任务调度
- **Flower**: Celery监控面板 (端口 5555)

## 环境要求

- Docker & Docker Compose
- Python 3.10+
- Node.js 18+
- 8GB+ RAM 推荐

## 快速启动

### 1. 配置环境变量

复制环境变量模板：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置必要的参数：

```env
# 数据库配置
POSTGRES_SERVER=postgres
POSTGRES_PORT=5432
POSTGRES_DB=rag_anything
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password

# Redis配置
REDIS_HOST=redis
REDIS_PORT=6379

# Neo4j配置
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

# Qdrant配置
QDRANT_URL=http://qdrant:6333

# JWT密钥
SECRET_KEY=your_very_long_and_secure_secret_key_here

# 默认管理员密码
ADMIN_PASSWORD=admin123456
```

### 2. 使用Docker Compose启动所有服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 3. 访问系统

- **前端界面**: http://localhost
- **后端API文档**: http://localhost:8000/docs
- **Celery监控**: http://localhost:5555
- **Neo4j浏览器**: http://localhost:7474

默认管理员账号：
- 用户名: `admin`
- 密码: 在 `.env` 中配置的 `ADMIN_PASSWORD`

## 开发环境启动

### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:5173

### Celery Worker开发

```bash
cd backend

# 启动Worker
celery -A app.core.celery_app worker --loglevel=info

# 启动Beat (定时任务)
celery -A app.core.celery_app beat --loglevel=info

# 启动Flower (监控)
celery -A app.core.celery_app flower
```

## 功能模块说明

### 1. 模型配置管理
- 支持配置多种模型类型 (LLM/VLM/Embedding/Rerank)
- 支持 OpenAI、Anthropic、Gemini 等主流API
- 支持本地模型配置
- 可设置默认模型

### 2. 知识库管理
- 创建多个独立知识库
- 配置不同的文档解析器 (LlamaParse/UnstructuredIO/Marker)
- 支持 OCR、表格识别、公式识别等功能

### 3. 文档处理流程
完整的4阶段处理流程：
1. **解析阶段 (Parsing)**: 提取文本和结构
2. **分析阶段 (Analyzing)**: 内容理解和分类
3. **构建图谱 (Building Graph)**: 提取实体和关系
4. **向量化 (Embedding)**: 生成嵌入向量

实时进度展示和中间结果查看

### 4. 多模态智能问答
- 支持文本问答
- 支持图片输入
- 支持表格和公式识别
- 多种查询模式：
  - 本地模式 (Local)
  - 全局模式 (Global)
  - 混合模式 (Hybrid)
  - 混合+图谱模式 (Hybrid Graph)

### 5. 知识图谱可视化
- 基于 vis-network 的交互式图谱展示
- 实体和关系筛选
- 节点详情查看
- 图谱统计信息

## API接口说明

### 认证接口
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录

### 模型配置
- `GET /api/v1/models` - 获取模型列表
- `POST /api/v1/models` - 创建模型配置
- `PUT /api/v1/models/{id}` - 更新模型配置
- `DELETE /api/v1/models/{id}` - 删除模型配置
- `POST /api/v1/models/{id}/default` - 设为默认模型

### 知识库管理
- `GET /api/v1/knowledge-bases` - 获取知识库列表
- `POST /api/v1/knowledge-bases` - 创建知识库
- `GET /api/v1/knowledge-bases/{id}` - 获取知识库详情
- `PUT /api/v1/knowledge-bases/{id}` - 更新知识库
- `DELETE /api/v1/knowledge-bases/{id}` - 删除知识库

### 文档管理
- `GET /api/v1/documents?kb_id={id}` - 获取文档列表
- `POST /api/v1/documents/upload` - 上传文档
- `WS /api/v1/documents/ws/{kb_id}` - WebSocket实时进度
- `DELETE /api/v1/documents/{id}` - 删除文档

### 问答接口
- `POST /api/v1/query/{kb_id}` - 知识库问答
- `POST /api/v1/query` - 无知识库问答
- `POST /api/v1/query/{kb_id}/sessions` - 创建会话
- `GET /api/v1/query/sessions` - 获取会话列表

### 知识图谱
- `GET /api/v1/graph/{kb_id}` - 获取图谱数据
- `GET /api/v1/graph/{kb_id}/stats` - 获取图谱统计

## 故障排查

### 前端无法连接后端
检查后端服务是否正常运行：
```bash
docker-compose logs backend
curl http://localhost:8000/api/v1/health
```

### 文档处理失败
查看 Celery Worker 日志：
```bash
docker-compose logs celery-worker
```

### 数据库连接失败
检查 PostgreSQL 服务：
```bash
docker-compose logs postgres
docker-compose exec postgres psql -U postgres -d rag_anything
```

### WebSocket 连接失败
确保前端正确配置了 WebSocket URL，检查 Nginx 配置是否支持 WebSocket

## 性能优化建议

1. **向量检索优化**
   - 调整 Qdrant 的索引参数
   - 使用合适的向量维度

2. **文档处理优化**
   - 增加 Celery Worker 数量
   - 使用 GPU 加速 OCR 和模型推理

3. **数据库优化**
   - 为常用查询字段添加索引
   - 定期清理过期数据

4. **缓存策略**
   - 使用 Redis 缓存频繁访问的数据
   - 配置合适的缓存过期时间

## 许可证

本项目基于原 RAG-Anything 项目进行扩展开发。

## 技术支持

如有问题，请查看：
- API文档: http://localhost:8000/docs
- 项目Issues: [GitHub Issues链接]
