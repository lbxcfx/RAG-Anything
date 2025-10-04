# 后端启动状态说明

## 当前情况

后端服务已配置完成，但在启动时遇到 SQLAlchemy 2.0 模型定义兼容性问题。

### 已完成的工作

✅ Python虚拟环境创建
✅ 所有核心依赖安装完成
✅ 开发环境配置文件 (.env.dev)
✅ SQLite数据库支持配置
✅ 异步数据库引擎配置

### 需要修复的问题

SQLAlchemy 2.0 要求模型字段使用 `Mapped[]` 类型注解，但当前代码使用的是旧式语法。

**错误示例**（当前代码）：
```python
class User(Base):
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True)
    username: str = Column(String, unique=True)
```

**正确写法**（SQLAlchemy 2.0）：
```python
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
```

### 快速解决方案

**方案1**: 允许未映射字段（临时解决）
在每个模型类中添加：
```python
class User(Base):
    __allow_unmapped__ = True
    # ... 其他代码
```

**方案2**: 使用SQLAlchemy 1.4（降级）
```bash
cd backend
venv/Scripts/python.exe -m pip install "sqlalchemy<2.0"
```

**方案3**: 更新所有模型为2.0语法（推荐，但工作量大）
需要更新以下文件：
- app/models/user.py
- app/models/model_config.py
- app/models/knowledge_base.py
- app/models/document.py
- app/models/chat.py

## 前端状态

✅ 前端服务运行正常
🌐 访问地址: http://localhost:3003

## 后续步骤

1. 选择上述解决方案之一修复模型问题
2. 运行数据库迁移初始化数据库
3. 启动后端服务
4. 测试前后端联调

## 手动启动命令

### 前端（已运行）
```bash
cd frontend
npm run dev
# 运行在 http://localhost:3003
```

### 后端（待修复后启动）
```bash
cd backend
venv/Scripts/python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 开发工具

- **前端热重载**: 已启用，修改代码自动刷新
- **后端热重载**: 配置了 `--reload` 参数
- **API文档**: http://localhost:8000/docs（启动后可访问）
- **数据库**: SQLite (./rag_anything_dev.db)

## 注意事项

1. 当前使用SQLite，无需配置PostgreSQL/Redis等外部服务
2. 某些功能可能需要完整的依赖（Neo4j, Qdrant等）才能正常运行
3. 开发环境已配置CORS允许前端跨域请求
