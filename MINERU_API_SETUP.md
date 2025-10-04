# MinerU API 配置说明

本文档说明如何将 MinerU 从本地命令行调用方式切换为 API 调用方式。

## 背景

MinerU 原本通过命令行方式调用，需要在本地安装多个模型。为了减少本地资源占用并提高性能，现已支持通过 API 方式调用 MinerU 服务。

## MinerU API 调用方式

MinerU 提供两种 API 调用方式：

### 1. 本地 API 服务（推荐）

**优势：**
- 完全控制，无配额限制
- 数据隐私性好
- 可根据需求配置 GPU/CPU

**启动本地 MinerU API 服务：**

```bash
# CPU 模式
mineru-api --host 0.0.0.0 --port 8000 --source modelscope

# GPU 模式（推荐）
mineru-api --host 0.0.0.0 --port 8000 --device cuda --source modelscope
```

服务启动后会在 `http://localhost:8000` 提供 API 接口，可访问 `http://localhost:8000/docs` 查看 API 文档。

### 2. 云端 API 服务

**使用 MinerU 官方云端 API：**

1. 访问 https://mineru.net 注册账号
2. 申请 API 密钥
3. 使用限制：
   - 单个文件大小 < 200MB
   - 单个文件页数 < 600 页
   - 每日免费解析额度有限

## 配置方法

### 后端配置（Backend）

在 `backend/.env` 文件中添加以下配置：

```bash
# MinerU API 配置
MINERU_USE_API=true                           # 启用 API 模式
MINERU_API_URL=http://localhost:8000          # API 服务地址
MINERU_API_KEY=                               # API 密钥（本地服务可留空）

# 如果使用云端 API：
# MINERU_API_URL=https://mineru.net/api/v4
# MINERU_API_KEY=your-api-key-here
```

### RAGAnything 配置

如果直接使用 RAGAnything 库，可以通过环境变量或配置对象设置：

**方式 1：环境变量**

```bash
export MINERU_USE_API=true
export MINERU_API_URL=http://localhost:8000
export MINERU_API_KEY=your-key-here  # 可选
```

**方式 2：代码配置**

```python
from raganything import RAGAnything, RAGAnythingConfig

config = RAGAnythingConfig(
    working_dir="./rag_storage",
    parser="mineru",
    mineru_use_api=True,
    mineru_api_url="http://localhost:8000",
    mineru_api_key=None,  # 本地服务不需要
)

rag = RAGAnything(
    config=config,
    llm_model_func=your_llm_func,
    embedding_func=your_embedding_func,
)
```

## API 接口说明

### 请求格式

MinerU API 接受以下参数：

- `file`: 文件内容（multipart/form-data）
- `method`: 解析方法 (auto/txt/ocr)
- `lang`: 文档语言（可选，如 zh/en/ja）
- 其他参数：backend, device, formula, table 等

### 响应格式

API 返回 JSON 格式的解析结果：

```json
{
  "md_url": "http://api/files/xxx.md",
  "json_url": "http://api/files/xxx_content_list.json",
  "images": [
    {
      "url": "http://api/files/image_1.png",
      "name": "image_1.png"
    }
  ]
}
```

## 本地命令行 vs API 对比

| 特性 | 命令行模式 | API 模式 |
|------|----------|---------|
| 模型加载 | 每次调用都加载 | 服务启动时一次性加载 |
| 资源占用 | 每次占用新进程 | 共享服务进程 |
| 并发处理 | 需多进程 | 原生支持 |
| 远程调用 | 不支持 | 支持 |
| GPU 利用 | 低效 | 高效 |
| 配置灵活性 | 高 | 中等 |

## 故障排查

### 1. API 连接失败

**错误：** `Failed to connect to MinerU API`

**解决方案：**
- 检查 API 服务是否启动：`curl http://localhost:8000/docs`
- 检查防火墙设置
- 验证 `MINERU_API_URL` 配置是否正确

### 2. 认证失败

**错误：** `API request failed with status 401`

**解决方案：**
- 检查 API 密钥是否正确
- 本地服务不需要密钥，确保 `MINERU_API_KEY` 为空或不设置

### 3. 文件解析失败

**错误：** `API request failed with status 400`

**解决方案：**
- 检查文件大小是否超过限制（200MB）
- 检查文件格式是否支持
- 查看 API 服务日志获取详细错误信息

## 性能优化建议

1. **使用本地 API + GPU**：最佳性能
   ```bash
   mineru-api --host 0.0.0.0 --port 8000 --device cuda
   ```

2. **批量处理**：API 模式下可以并发处理多个文件

3. **缓存结果**：RAGAnything 会自动缓存解析结果，避免重复解析

## 切换回命令行模式

如需切换回命令行模式，只需设置：

```bash
MINERU_USE_API=false
```

或在配置中：

```python
config = RAGAnythingConfig(
    mineru_use_api=False,
)
```

## 参考资源

- MinerU GitHub: https://github.com/opendatalab/MinerU
- MinerU 官网: https://mineru.net
- API 文档: 启动服务后访问 http://localhost:8000/docs
